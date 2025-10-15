import json
import logging
import random
import re
from datetime import datetime, timedelta
from typing import Optional

import text_unidecode
from cryptography.fernet import Fernet
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from fyle_accounting_library.common_resources.enums import DimensionDetailSourceTypeEnum
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, MappingSetting
from sageintacctsdk import SageIntacctSDK
from sageintacctsdk.exceptions import WrongParamsError

from apps.fyle.models import DependentFieldSetting
from apps.mappings.models import GeneralMapping, LocationEntityMapping
from apps.sage_intacct.models import (
    APPayment,
    APPaymentLineitem,
    Bill,
    BillLineitem,
    ChargeCardTransaction,
    ChargeCardTransactionLineitem,
    CostCode,
    CostType,
    DimensionDetail,
    ExpenseReport,
    ExpenseReportLineitem,
    JournalEntry,
    JournalEntryLineitem,
    SageIntacctReimbursement,
    SageIntacctReimbursementLineitem,
)
from apps.workspaces.helpers import get_app_name
from apps.workspaces.models import Configuration, FyleCredential, SageIntacctCredential, Workspace
from workers.helpers import RoutingKeyEnum, WorkerActionEnum, publish_to_rabbitmq

logger = logging.getLogger(__name__)
logger.level = logging.INFO


SYNC_UPPER_LIMIT = {
    'items': 5000,
    'classes': 1000,
    'accounts': 2000,
    'vendors': 20000,
    'locations': 1000,
    'projects': 25000,
    'tax_details': 200,
    'customers': 10000,
    'cost_codes': 10000,
    'departments': 1000,
    'cost_types': 500000,
    'expense_types': 1000,
    'user_defined_dimensions': 5000
}

ATTRIBUTE_DISABLE_CALLBACK_PATH = {
    'PROJECT': 'fyle_integrations_imports.modules.projects.disable_projects',
    'VENDOR': 'fyle_integrations_imports.modules.merchants.disable_merchants',
    'ACCOUNT': 'fyle_integrations_imports.modules.categories.disable_categories',
    'EXPENSE_TYPE': 'fyle_integrations_imports.modules.categories.disable_categories',
    'COST_CENTER': 'fyle_integrations_imports.modules.cost_centers.disable_cost_centers'
}


class SageIntacctConnector:
    """
    Sage Intacct utility functions
    """
    def __init__(self, credentials_object: SageIntacctCredential, workspace_id: int):
        sender_id = settings.SI_SENDER_ID
        sender_password = settings.SI_SENDER_PASSWORD
        encryption_key = settings.ENCRYPTION_KEY
        cipher_suite = Fernet(encryption_key)
        decrypted_password = cipher_suite.decrypt(credentials_object.si_user_password.encode('utf-8')).decode('utf-8')

        # TODO: Cache general_mappings
        location_entity_mapping = LocationEntityMapping.objects.filter(~Q(destination_id='top_level'), workspace_id=workspace_id).first()

        self.connection = SageIntacctSDK(
            sender_id=sender_id,
            sender_password=sender_password,
            user_id=credentials_object.si_user_id,
            company_id=credentials_object.si_company_id,
            user_password=decrypted_password,
            entity_id=location_entity_mapping.destination_id if location_entity_mapping else None
        )

        self.workspace_id = workspace_id

    def is_duplicate_deletion_skipped(self, attribute_type: str) -> bool:
        """
        Check if duplicate deletion is skipped for the attribute type
        :param attribute_type: Type of the attribute
        :return: Whether deletion is skipped
        """
        if attribute_type in [
            'ACCOUNT', 'VENDOR', 'ITEM', 'CUSTOMER',
            'DEPARTMENT', 'CLASS', 'EXPENSE_TYPE',
            'PROJECT', 'LOCATION'
        ]:
            return False

        return True

    def is_import_enabled(self, attribute_type: str) -> bool:
        """
        Check if import is enabled for the attribute type
        :param attribute_type: Type of the attribute
        :return: Whether import is enabled
        """
        is_import_to_fyle_enabled = False

        configuration = Configuration.objects.filter(workspace_id=self.workspace_id).first()
        if not configuration:
            return is_import_to_fyle_enabled

        if attribute_type in ['ACCOUNT', 'EXPENSE_TYPE'] and configuration.import_categories:
            is_import_to_fyle_enabled = True

        elif attribute_type == 'VENDOR' and configuration.import_vendors_as_merchants:
            is_import_to_fyle_enabled = True

        elif attribute_type in ['CUSTOMER', 'DEPARTMENT', 'CLASS', 'LOCATION', 'PROJECT', 'ITEM']:
            mapping_setting = MappingSetting.objects.filter(workspace_id=self.workspace_id, destination_field=attribute_type).first()
            if mapping_setting and mapping_setting.import_to_fyle:
                is_import_to_fyle_enabled = True

        return is_import_to_fyle_enabled

    def get_attribute_disable_callback_path(self, attribute_type: str) -> Optional[str]:
        """
        Get the attribute disable callback path
        :param attribute_type: Type of the attribute
        :return: attribute disable callback path or none
        """
        if attribute_type in ['ACCOUNT', 'VENDOR', 'EXPENSE_TYPE']:
            return ATTRIBUTE_DISABLE_CALLBACK_PATH.get(attribute_type)

        mapping_setting = MappingSetting.objects.filter(
            workspace_id=self.workspace_id,
            destination_field=attribute_type
        ).first()

        if mapping_setting and not mapping_setting.is_custom:
            return ATTRIBUTE_DISABLE_CALLBACK_PATH.get(mapping_setting.source_field)

    def get_tax_solution_id_or_none(self, lineitems: list[ExpenseReportLineitem | BillLineitem | JournalEntryLineitem | ChargeCardTransactionLineitem]) -> str:
        """
        Get Tax Solution Id or None
        :param lineitems: List of lineitems
        :return: Tax Solution Id or None
        """
        general_mappings = GeneralMapping.objects.get(workspace_id=self.workspace_id)

        if general_mappings.location_entity_id:
            return None
        else:
            tax_code = lineitems[0].tax_code

            if tax_code:
                destination_attribute = DestinationAttribute.objects.get(value=tax_code, workspace_id=self.workspace_id)
                tax_solution_id = destination_attribute.detail['tax_solution_id']
            else:
                destination_attribute = DestinationAttribute.objects.get(value=general_mappings.default_tax_code_name, workspace_id=self.workspace_id)
                tax_solution_id = destination_attribute.detail['tax_solution_id']

            return tax_solution_id

    def get_tax_exclusive_amount(self, amount: float | int, default_tax_code_id: str) -> tuple:
        """
        Get Tax Exclusive Amount
        :param amount: Amount
        :param default_tax_code_id: Default Tax Code Id
        :return: Tax Exclusive Amount and Tax Amount
        """
        tax_attribute = DestinationAttribute.objects.filter(destination_id=default_tax_code_id, attribute_type='TAX_DETAIL',workspace_id=self.workspace_id).first()
        tax_exclusive_amount = amount
        tax_amount = None
        if tax_attribute:
            tax_rate = int(tax_attribute.detail['tax_rate'])
            tax_exclusive_amount = round((amount - (amount / (tax_rate + 1))), 2)
            tax_amount = round((amount - tax_exclusive_amount), 2)

        return tax_exclusive_amount, tax_amount

    def is_sync_allowed(self, attribute_type: str, attribute_count: int) -> bool:
        """
        Checks if the sync is allowed
        :param attribute_type: Attribute Type
        :param attribute_count: Attribute Count
        :return: True if sync is allowed else False
        """
        if attribute_count > SYNC_UPPER_LIMIT[attribute_type]:
            workspace_created_at = Workspace.objects.get(id=self.workspace_id).created_at
            if workspace_created_at > timezone.make_aware(datetime(2024, 10, 1), timezone.get_current_timezone()):
                return False
            else:
                return True

        return True

    def get_latest_sync(self, workspace_id: int, attribute_type: str) -> str:
        """
        Get the latest sync date
        :param workspace_id: Workspace Id
        :param attribute_type: Attribute Type
        :return: Latest Sync Date
        """
        latest_sync = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type=attribute_type).order_by('-updated_at').first()
        if latest_sync:
            latest_synced_timestamp = latest_sync.updated_at - timedelta(days=1)
            return latest_synced_timestamp.strftime('%m/%d/%Y')

        return None

    def construct_get_all_generator_params(self, fields: list, latest_updated_at: str = None) -> dict:
        """
        Construct Get All Generator Params
        :param fields: Fields
        :param latest_updated_at: Latest Updated At
        :return: Params
        """
        params = {'fields': fields}

        if latest_updated_at:
            params['updated_at'] = latest_updated_at
        else:
            params['field'] = 'STATUS'
            params['value'] = 'active'

        return params

    def sync_accounts(self) -> list:
        """
        Get accounts
        """
        attribute_count = self.connection.accounts.count()

        if not self.is_sync_allowed(attribute_type = 'accounts', attribute_count=attribute_count):
            logger.info('Skipping sync of accounts for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['TITLE', 'ACCOUNTNO', 'ACCOUNTTYPE', 'STATUS']
        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='ACCOUNT')
        is_account_import_enabled = self.is_import_enabled('ACCOUNT')

        params = self.construct_get_all_generator_params(fields=fields, latest_updated_at=latest_updated_at)
        account_generator = self.connection.accounts.get_all_generator(**params)

        account_attributes = {
            'account': [],
            'ccc_account': []
        }

        for accounts in account_generator:
            for account in accounts:
                account_attributes['account'].append({
                    'attribute_type': 'ACCOUNT',
                    'display_name': 'Account',
                    'value': text_unidecode.unidecode(u'{0}'.format(account['TITLE'].replace('/', '-'))),
                    'destination_id': account['ACCOUNTNO'],
                    'active': account['STATUS'] == 'active',
                    'detail': {
                        'account_type': account['ACCOUNTTYPE']
                    },
                    'code': account['ACCOUNTNO']
                })

        for attribute_type, account_attribute in account_attributes.items():
            if account_attribute:
                DestinationAttribute.bulk_create_or_update_destination_attributes(
                    account_attribute,
                    attribute_type.upper(),
                    self.workspace_id,
                    True,
                    app_name=get_app_name(),
                    attribute_disable_callback_path=self.get_attribute_disable_callback_path('ACCOUNT'),
                    is_import_to_fyle_enabled=is_account_import_enabled,
                    skip_deletion=self.is_duplicate_deletion_skipped('ACCOUNT')
                )
        return []

    def sync_departments(self) -> list:
        """
        Get departments
        """
        attribute_count = self.connection.departments.count()
        if not self.is_sync_allowed(attribute_type = 'departments', attribute_count = attribute_count):
            logger.info('Skipping sync of department for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['TITLE', 'DEPARTMENTID', 'STATUS']
        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='DEPARTMENT')
        is_import_enabled = self.is_import_enabled('DEPARTMENT')

        params = self.construct_get_all_generator_params(fields=fields, latest_updated_at=latest_updated_at)

        department_generator = self.connection.departments.get_all_generator(**params)

        department_attributes = []

        for departments in department_generator:
            for department in departments:
                department_attributes.append({
                    'attribute_type': 'DEPARTMENT',
                    'display_name': 'department',
                    'value': department['TITLE'],
                    'destination_id': department['DEPARTMENTID'],
                    'active': department['STATUS'] == 'active',
                    'code': department['DEPARTMENTID']
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            department_attributes,
            'DEPARTMENT',
            self.workspace_id,
            True,
            app_name=get_app_name(),
            attribute_disable_callback_path=self.get_attribute_disable_callback_path('DEPARTMENT'),
            is_import_to_fyle_enabled=is_import_enabled,
            skip_deletion=self.is_duplicate_deletion_skipped('DEPARTMENT')
        )

        return []

    def sync_expense_types(self) -> list:
        """
        Get expense types
        """
        attribute_count = self.connection.expense_types.count()
        if not self.is_sync_allowed(attribute_type = 'expense_types', attribute_count = attribute_count):
            logger.info('Skipping sync of expense_type for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['DESCRIPTION', 'ACCOUNTLABEL', 'GLACCOUNTNO', 'GLACCOUNTTITLE', 'STATUS']
        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='EXPENSE_TYPE')
        is_expense_type_import_enabled = self.is_import_enabled('EXPENSE_TYPE')

        params = self.construct_get_all_generator_params(fields=fields, latest_updated_at=latest_updated_at)
        expense_type_generator = self.connection.expense_types.get_all_generator(**params)

        expense_types_attributes = []

        for expense_types in expense_type_generator:
            for expense_type in expense_types:
                expense_types_attributes.append({
                    'attribute_type': 'EXPENSE_TYPE',
                    'display_name': 'Expense Types',
                    'value': text_unidecode.unidecode(u'{0}'.format(expense_type['DESCRIPTION'].replace('/', '-'))),
                    'destination_id': expense_type['ACCOUNTLABEL'],
                    'active': expense_type['STATUS'] == 'active',
                    'detail': {
                        'gl_account_no': expense_type['GLACCOUNTNO'],
                        'gl_account_title': expense_type['GLACCOUNTTITLE']
                    },
                    'code': expense_type['ACCOUNTLABEL']
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            expense_types_attributes,
            'EXPENSE_TYPE',
            self.workspace_id,
            True,
            app_name=get_app_name(),
            attribute_disable_callback_path=self.get_attribute_disable_callback_path('EXPENSE_TYPE'),
            is_import_to_fyle_enabled=is_expense_type_import_enabled,
            skip_deletion=self.is_duplicate_deletion_skipped('EXPENSE_TYPE')
        )

        if not is_expense_type_import_enabled:
            payload = {
                'workspace_id': self.workspace_id,
                'action': WorkerActionEnum.CHECK_AND_CREATE_CCC_MAPPINGS.value,
                'data': {
                    'workspace_id': self.workspace_id
                }
            }
            publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)

        return []

    def sync_charge_card_accounts(self) -> list:
        """
        Get charge card accounts
        """
        charge_card_accounts = self.connection.charge_card_accounts.get_by_query(and_filter=[('equalto', 'LIABILITYTYPE', 'Credit'), ('equalto', 'STATUS', 'active')])

        charge_card_accounts_attributes = []

        for charge_card_account in charge_card_accounts:
            charge_card_accounts_attributes.append({
                'attribute_type': 'CHARGE_CARD_NUMBER',
                'display_name': 'Charge Card Account',
                'value': charge_card_account['CARDID'],
                'destination_id': charge_card_account['CARDID'],
                'active': True
            })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            charge_card_accounts_attributes, 'CHARGE_CARD_NUMBER', self.workspace_id, True)

        return []

    def sync_payment_accounts(self) -> list:
        """
        Get Payment accounts
        """
        fields = ['BANKNAME', 'BANKACCOUNTID']
        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='PAYMENT_ACCOUNT')
        payment_account_generator = self.connection.checking_accounts.get_all_generator(field='STATUS', value='active', fields=fields, updated_at=latest_updated_at if latest_updated_at else None)

        payment_accounts_attributes = []

        for payment_accounts in payment_account_generator:
            for payment_account in payment_accounts:
                payment_accounts_attributes.append({
                    'attribute_type': 'PAYMENT_ACCOUNT',
                    'display_name': 'Payment Account',
                    'value': '{} - {}'.format(payment_account['BANKNAME'], payment_account['BANKACCOUNTID']),
                    'destination_id': payment_account['BANKACCOUNTID'],
                    'active': True
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            payment_accounts_attributes, 'PAYMENT_ACCOUNT', self.workspace_id, True)

        return []

    def sync_cost_types(self) -> list:
        """
        Sync of Sage Intacct Cost Types
        """
        attribute_count = self.connection.cost_types.count()
        if not self.is_sync_allowed(attribute_type = 'cost_types', attribute_count = attribute_count):
            logger.info('Skipping sync of cost_types for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        args = {
            'field': 'STATUS',
            'value': 'active'
        }

        dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=self.workspace_id).first()

        if dependent_field_setting and dependent_field_setting.last_synced_at:
            # subtracting 1 day from the last_synced_at since time is not involved
            latest_synced_timestamp = dependent_field_setting.last_synced_at - timedelta(days=1)
            args['updated_at'] = latest_synced_timestamp.strftime('%m/%d/%Y')

        cost_types_generator = self.connection.cost_types.get_all_generator(**args)

        for cost_types in cost_types_generator:
            CostType.bulk_create_or_update(cost_types, self.workspace_id)

        dependent_field_setting.last_synced_at = datetime.now()
        dependent_field_setting.save()

    def sync_cost_codes(self) -> None:
        """
        Sync Cost Codes
        """
        attribute_count = self.connection.tasks.count(field=None, value=None)
        logger.info("Cost Code count for workspace %s: %s", self.workspace_id, attribute_count)

        if not self.is_sync_allowed(attribute_type = 'cost_codes', attribute_count = attribute_count):
            logger.info('Skipping sync of tasks for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['RECORDNO', 'TASKID', 'NAME', 'PROJECTID', 'PROJECTNAME']
        args = {}

        dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=self.workspace_id).first()

        if dependent_field_setting and dependent_field_setting.last_synced_at:
            latest_synced_timestamp = dependent_field_setting.last_synced_at - timedelta(days=1)
            args['updated_at'] = latest_synced_timestamp.strftime('%m/%d/%Y')

        tasks_generator = self.connection.tasks.get_all_generator(field=None, value=None, fields=fields, updated_at=args.get('updated_at', None))

        for tasks in tasks_generator:
            CostCode.bulk_create_or_update(tasks, self.workspace_id)

        dependent_field_setting.last_synced_at = datetime.now()
        dependent_field_setting.save()

    def sync_projects(self) -> list:
        """
        Get projects
        """
        attribute_count = self.connection.projects.count()
        if not self.is_sync_allowed(attribute_type = 'projects', attribute_count = attribute_count):
            logger.info('Skipping sync of projects for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['CUSTOMERID', 'CUSTOMERNAME', 'NAME', 'PROJECTID', 'STATUS']

        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='PROJECT')
        is_project_import_enabled = self.is_import_enabled('PROJECT')

        params = self.construct_get_all_generator_params(fields=fields, latest_updated_at=latest_updated_at)
        project_generator = self.connection.projects.get_all_generator(**params)

        project_attributes = []

        for projects in project_generator:
            for project in projects:
                detail = {
                    'customer_id': project['CUSTOMERID'],
                    'customer_name': project['CUSTOMERNAME']
                }

                project_attributes.append({
                    'attribute_type': 'PROJECT',
                    'display_name': 'project',
                    'value': project['NAME'],
                    'destination_id': project['PROJECTID'],
                    'active': project['STATUS'] == 'active',
                    'detail': detail,
                    'code': project['PROJECTID']
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                project_attributes,
                'PROJECT',
                self.workspace_id,
                True,
                app_name=get_app_name(),
                attribute_disable_callback_path=self.get_attribute_disable_callback_path('PROJECT'),
                is_import_to_fyle_enabled=is_project_import_enabled,
                skip_deletion=self.is_duplicate_deletion_skipped('PROJECT')
            )

        return []

    def sync_items(self) -> list:
        """
        Get items
        """
        attribute_count = self.connection.items.count()
        if not self.is_sync_allowed(attribute_type = 'items', attribute_count = attribute_count):
            logger.info('Skipping sync of items for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['NAME', 'ITEMID', 'ITEMTYPE', 'STATUS']

        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='ITEM')

        params = self.construct_get_all_generator_params(fields=fields, latest_updated_at=latest_updated_at)

        item_generator = self.connection.items.get_all_generator(**params)

        item_attributes = []

        for items in item_generator:
            for item in items:
                # remove this check when we are mapping Fyle Categories with Sage Intacct Items
                if item['ITEMTYPE'] == 'Non-Inventory':
                    item_attributes.append({
                        'attribute_type': 'ITEM',
                        'display_name': 'item',
                        'value': item['NAME'],
                        'destination_id': item['ITEMID'],
                        'active': item['STATUS'] == 'active'
                    })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                item_attributes,
                'ITEM',
                self.workspace_id,
                True,
                app_name=get_app_name(),
                attribute_disable_callback_path=self.get_attribute_disable_callback_path('ITEM'),
                skip_deletion=self.is_duplicate_deletion_skipped('ITEM'),
                is_import_to_fyle_enabled=self.is_import_enabled('ITEM')
            )

        return []

    def sync_locations(self) -> list:
        """
        Get locations
        """
        attribute_count = self.connection.locations.count()
        if not self.is_sync_allowed(attribute_type = 'locations', attribute_count = attribute_count):
            logger.info('Skipping sync of locations for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return
        fields = ['NAME', 'LOCATIONID', 'STATUS']
        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='LOCATION')
        params = self.construct_get_all_generator_params(fields=fields, latest_updated_at=latest_updated_at)
        location_generator = self.connection.locations.get_all_generator(**params)

        location_attributes = []

        for locations in location_generator:
            for location in locations:
                location_attributes.append({
                    'attribute_type': 'LOCATION',
                    'display_name': 'location',
                    'value': location['NAME'],
                    'destination_id': location['LOCATIONID'],
                    'active': location['STATUS'] == 'active'
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            location_attributes, 'LOCATION', self.workspace_id, True,
            app_name=get_app_name(),
            attribute_disable_callback_path=self.get_attribute_disable_callback_path('LOCATION'),
            skip_deletion=self.is_duplicate_deletion_skipped('LOCATION'),
            is_import_to_fyle_enabled=self.is_import_enabled('LOCATION')
        )

        return []

    def __get_entity_slide_preference(self) -> bool:
        """
        Get Entity Slide Preference
        :return: True if Entity Slide is disabled else False
        """
        entity_slide_disabled = False

        # Check if entity slide is disabled or enabled
        try:
            company_prefs = self.connection.api_base.format_and_send_request({
                'get_companyprefs': {
                    '@application': 'ME'
                }
            })['data']['companypref']

            entity_slide_info = list(filter(
                lambda item: item['preference'] == 'DISABLEENTITYSLIDEIN', company_prefs
            ))[0]

            entity_slide_disabled = entity_slide_info['prefvalue'] == 'true'
        except Exception as e:
            logger.error(e.__dict__)

        return entity_slide_disabled

    def sync_location_entities(self) -> list:
        """
        Get location entities
        """
        if not self.__get_entity_slide_preference():
            fields = ['NAME', 'LOCATIONID', 'OPCOUNTRY']
            latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='LOCATION_ENTITY')
            location_entity_generator = self.connection.location_entities.get_all_generator(field='STATUS', value='active', fields=fields, updated_at=latest_updated_at if latest_updated_at else None)

            location_entities_attributes = []

            for location_entities in location_entity_generator:
                for location_entity in location_entities:
                    location_entities_attributes.append({
                        'attribute_type': 'LOCATION_ENTITY',
                        'display_name': 'location entity',
                        'value': location_entity['NAME'],
                        'destination_id': location_entity['LOCATIONID'],
                        'detail': {
                            'country': location_entity['OPCOUNTRY']
                        },
                        'active': True
                    })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                location_entities_attributes, 'LOCATION_ENTITY', self.workspace_id, True)

        return []

    def sync_expense_payment_types(self) -> list:
        """
        Get Expense Payment Types
        """
        fields = ['NAME', 'RECORDNO', 'NONREIMBURSABLE']
        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='EXPENSE_PAYMENT_TYPE')
        expense_payment_type_generator = self.connection.expense_payment_types.get_all_generator(field='STATUS', value='active', fields=fields, updated_at=latest_updated_at if latest_updated_at else None)

        expense_payment_type_attributes = []

        for expense_payment_types in expense_payment_type_generator:
            for expense_payment_type in expense_payment_types:
                expense_payment_type_attributes.append({
                    'attribute_type': 'EXPENSE_PAYMENT_TYPE',
                    'display_name': 'expense payment type',
                    'value': expense_payment_type['NAME'],
                    'destination_id': expense_payment_type['RECORDNO'],
                    'detail': {
                        'is_reimbursable': expense_payment_type['NONREIMBURSABLE'] == 'false'
                    },
                    'active': True
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            expense_payment_type_attributes, 'EXPENSE_PAYMENT_TYPE', self.workspace_id, True)

        return []

    def sync_employees(self) -> list:
        """
        Get employees
        """
        fields = ['CONTACT.EMAIL1', 'CONTACT.PRINTAS', 'DEPARTMENTID', 'CONTACT.CONTACTNAME', 'EMPLOYEEID', 'LOCATIONID']
        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='EMPLOYEE')
        employee_generator = self.connection.employees.get_all_generator(field='STATUS', value='active', fields=fields, updated_at=latest_updated_at if latest_updated_at else None)

        employee_attributes = []

        for employees in employee_generator:
            for employee in employees:
                detail = {
                    'email': employee['CONTACT.EMAIL1'] if employee['CONTACT.EMAIL1'] else None,
                    'full_name': employee['CONTACT.PRINTAS'] if employee['CONTACT.PRINTAS'] else None,
                    'location_id': employee['LOCATIONID'] if employee['LOCATIONID'] else None,
                    'department_id': employee['DEPARTMENTID'] if employee['DEPARTMENTID'] else None
                }

                employee_attributes.append({
                    'attribute_type': 'EMPLOYEE',
                    'display_name': 'employee',
                    'value': employee['CONTACT.CONTACTNAME'],
                    'destination_id': employee['EMPLOYEEID'],
                    'detail': detail,
                    'active': True
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            employee_attributes, 'EMPLOYEE', self.workspace_id, True)

        return []

    def sync_allocations(self) -> list:
        """
        Sync allocation entries from intacct
        """
        allocation_attributes = []
        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='ALLOCATION')
        params = {}
        if latest_updated_at:
            params['updated_at'] = latest_updated_at
        else:
            params['field'] = 'STATUS'
            params['value'] = 'active'
        allocations_generator = self.connection.allocations.get_all_generator(**params)

        for allocations in allocations_generator:
            for allocation in allocations:
                allocation_entry_generator = self.connection.allocation_entry.get_all_generator(field='allocation.ALLOCATIONID', value=allocation['ALLOCATIONID'])
                for allocation_entries in allocation_entry_generator:
                    if not allocation_entries:
                        continue

                    detail = {}
                    for allocation_entry in allocation_entries:
                        value = allocation_entry['ALLOCATIONID']
                        status = allocation['STATUS']
                        destination_id = allocation_entry['ALLOCATIONKEY']
                        for field_name in allocation_entry.keys():
                            if allocation_entry[field_name] is not None and field_name not in detail:
                                detail[field_name] = True

                    detail.pop('ALLOCATIONID')
                    detail.pop('ALLOCATIONKEY')

                    allocation_attributes.append({
                        'attribute_type': 'ALLOCATION',
                        'display_name': 'allocation',
                        'value': value,
                        'destination_id': destination_id,
                        'active': status == 'active',
                        'detail': detail
                    })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                allocation_attributes, 'ALLOCATION', self.workspace_id, update=True
            )

    def sync_user_defined_dimensions(self) -> list:
        """
        Get User Defined Dimensions
        """
        dimensions = self.connection.dimensions.get_all()
        dimension_details = []

        for dimension in dimensions:
            dimension_details.append({
                'attribute_type': dimension['objectName'],
                'display_name': dimension['termLabel'],
                'source_type': DimensionDetailSourceTypeEnum.ACCOUNTING.value,
                'workspace_id': self.workspace_id
            })

            if dimension['userDefinedDimension'] == 'true':
                try:
                    dimension_attributes = []
                    dimension_name = dimension['objectName'].upper().replace(" ", "_")
                    dimension_count = self.connection.dimension_values.count(dimension_name=dimension['objectName'])

                    is_sync_allowed = self.is_sync_allowed(attribute_type = 'user_defined_dimensions', attribute_count = dimension_count)

                    if not is_sync_allowed:
                        logger.info('Skipping sync of UDD %s for workspace %s as it has %s counts which is over the limit', dimension_name, self.workspace_id, dimension_count)
                        continue

                    dimension_values = self.connection.dimension_values.get_all(dimension['objectName'])

                    for value in dimension_values:
                        dimension_attributes.append({
                            'attribute_type': dimension_name,
                            'display_name': dimension['termLabel'],
                            'value': value['name'],
                            'destination_id': value['id'],
                            'active': True
                        })

                    DestinationAttribute.bulk_create_or_update_destination_attributes(
                        dimension_attributes, dimension_name, self.workspace_id
                    )
                except Exception as e:
                    logger.error("Error while syncing user defined dimension %s for workspace %s: %s", dimension_name, self.workspace_id, e)

        DimensionDetail.bulk_create_or_update_dimension_details(
            dimensions=dimension_details,
            workspace_id=self.workspace_id,
            source_type=DimensionDetailSourceTypeEnum.ACCOUNTING.value
        )

        return []

    def sync_classes(self) -> list:
        """
        Get classes
        """
        attribute_count = self.connection.classes.count()
        if not self.is_sync_allowed(attribute_type = 'classes', attribute_count = attribute_count):
            logger.info('Skipping sync of classes for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['NAME', 'CLASSID', 'STATUS']

        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='CLASS')
        params = self.construct_get_all_generator_params(fields=fields, latest_updated_at=latest_updated_at)
        class_generator = self.connection.classes.get_all_generator(**params)
        class_attributes = []

        for _classes in class_generator:
            for _class in _classes:
                class_attributes.append({
                    'attribute_type': 'CLASS',
                    'display_name': 'class',
                    'value': _class['NAME'],
                    'destination_id': _class['CLASSID'],
                    'active': _class['STATUS'] == 'active'
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                class_attributes, 'CLASS', self.workspace_id, True,
                app_name=get_app_name(),
                attribute_disable_callback_path=self.get_attribute_disable_callback_path('CLASS'),
                skip_deletion=self.is_duplicate_deletion_skipped('CLASS'),
                is_import_to_fyle_enabled=self.is_import_enabled('CLASS')
            )

        return []

    def sync_customers(self) -> list:
        """
        Get Customers
        """
        attribute_count = self.connection.customers.count()
        if not self.is_sync_allowed(attribute_type = 'customers', attribute_count = attribute_count):
            logger.info('Skipping sync of customers for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['NAME', 'CUSTOMERID', 'STATUS']

        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='CUSTOMER')
        params = self.construct_get_all_generator_params(fields=fields, latest_updated_at=latest_updated_at)
        customer_generator = self.connection.customers.get_all_generator(**params)

        customer_attributes = []

        for customers in customer_generator:
            for customer in customers:
                customer_attributes.append({
                    'attribute_type': 'CUSTOMER',
                    'display_name': 'customer',
                    'value': customer['NAME'],
                    'destination_id': customer['CUSTOMERID'],
                    'active': customer['STATUS'] == 'active'
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                customer_attributes, 'CUSTOMER', self.workspace_id, True,
                app_name=get_app_name(),
                attribute_disable_callback_path=self.get_attribute_disable_callback_path('CUSTOMER'),
                skip_deletion=self.is_duplicate_deletion_skipped('CUSTOMER'),
                is_import_to_fyle_enabled=self.is_import_enabled('CUSTOMER')
            )

        return []

    def sync_tax_details(self) -> list:
        """
        Get and Sync Tax Details
        """
        attribute_count = self.connection.tax_details.count()
        if not self.is_sync_allowed(attribute_type = 'tax_details', attribute_count = attribute_count):
            logger.info('Skipping sync of tax_details for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        attributes = []
        fields = ['DETAILID', 'VALUE', 'TAXSOLUTIONID', 'TAXTYPE']
        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='TAX_DETAIL')
        tax_details_generator = self.connection.tax_details.get_all_generator(field='STATUS', value='active', fields=fields, updated_at=latest_updated_at if latest_updated_at else None)
        for tax_details in tax_details_generator:
            for tax_detail in tax_details:
                if float(tax_detail['VALUE']) >= 0 and tax_detail['TAXTYPE'] == 'Purchase':
                    attributes.append({
                        'attribute_type': 'TAX_DETAIL',
                        'display_name': 'Tax Detail',
                        'value': tax_detail['DETAILID'],
                        'destination_id': tax_detail['DETAILID'],
                        'active': True,
                        'detail': {
                            'tax_rate': float(tax_detail['VALUE']),
                            'tax_solution_id': tax_detail['TAXSOLUTIONID']
                        }
                    })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            attributes,
            'TAX_DETAIL',
            self.workspace_id,
            True
        )

        return []

    def create_destination_attribute(self, attribute: str, name: str, destination_id: str, email: str = None) -> DestinationAttribute:
        """
        Create Destination Attribute
        :param attribute: Attribute
        :param name: Name
        :param destination_id: Destination Id
        :param email: Email
        :return: Destination Attribute
        """
        created_attribute = DestinationAttribute.create_or_update_destination_attribute({
            'attribute_type': attribute.upper(),
            'display_name': attribute,
            'value': name,
            'destination_id': destination_id,
            'active': True,
            'detail': {
                'email': email
            }
        }, self.workspace_id)

        return created_attribute

    def get_or_create_employee(self, source_employee: ExpenseAttribute) -> DestinationAttribute:
        """
        Call Sage Intacct api to get or create employee
        :param source_employee: employee attribute to be created
        :return: Employee
        """
        employee_name = source_employee.detail['full_name']
        employee = self.connection.employees.get(field='CONTACT_NAME', value=employee_name)

        if 'employee' in employee:
            employee = employee['employee'][0] if int(employee['@totalcount']) > 1 else employee['employee']
        else:
            employee = None

        if not employee:
            created_employee = self.post_employees(source_employee)
            return self.create_destination_attribute(
                'employee', created_employee['EMPLOYEEID'], created_employee['EMPLOYEEID'], source_employee.value
            )
        else:
            return self.create_destination_attribute(
                'employee', employee['CONTACT_NAME'], employee['EMPLOYEEID'], source_employee.value
            )

    def get_or_create_vendor(self, vendor_name: str, email: str = None, create: bool = False) -> DestinationAttribute:
        """
        Call Sage Intacct api to get or create vendor
        :param vendor_name: Name of the vendor
        :param email: Email of the vendor
        :param create: False to just Get and True to Get or Create if not exists
        :return: Vendor
        """
        vendor_from_db = DestinationAttribute.objects.filter(
            workspace_id=self.workspace_id,
            attribute_type='VENDOR',
            active=True
        ).filter(
            Q(value__iexact=vendor_name.lower()) | Q(destination_id__iexact=vendor_name.lower())
        ).first()
        if vendor_from_db:
            return vendor_from_db

        try:
            if create:
                vendor_id = self.sanitize_vendor_name(vendor_name)
                if len(vendor_id) > 20:
                    vendor_id = vendor_id[:17] + str(random.randint(100, 999))
                created_vendor = self.post_vendor(vendor_id, vendor_name, email)
                return self.create_destination_attribute(
                    'vendor', vendor_name, created_vendor['VENDORID'], email)
        except WrongParamsError as e:
            logger.info("Error while creating vendor %s in Workspace %s: %s", vendor_name, self.workspace_id, e.response)

            if 'error' in e.response:
                sage_intacct_errors = e.response['error']

                if "Another record with the value" in sage_intacct_errors[0]['description2']:
                    logger.info('Searching for vendor: %s in Sage Intacct in Workspace %s', vendor_name, self.workspace_id)
                    vendor = self.connection.vendors.get(field='NAME', value=vendor_name.replace("'", "\\'"))
                    vendor_name = vendor_name.replace(',', '').replace("'", ' ').replace('-', ' ')[:20]

                    if 'VENDOR' in vendor:
                        if int(vendor['@totalcount']) > 1:
                            sorted_vendor_data = sorted(vendor['VENDOR'], key=lambda x: datetime.strptime(x["WHENMODIFIED"], "%m/%d/%Y %H:%M:%S"), reverse=True)
                            vendor = sorted_vendor_data[0]
                        else:
                            vendor = vendor['VENDOR'][0]

                        vendor = vendor if vendor['STATUS'] == 'active' else None
                    else:
                        try:
                            vendor_id = vendor_id[:18] + '-1'
                            vendor = self.post_vendor(vendor_id, vendor_name, email)
                        except Exception as e:
                            logger.error("Error while creating vendor %s in Workspace %s: %s", vendor_name, self.workspace_id, e.response)
                            return None

                    if vendor:
                        return self.create_destination_attribute(
                            attribute='vendor',
                            name=vendor_name,
                            destination_id=vendor['VENDORID'],
                            email=email
                        )

    def get_expense_link(self, lineitem: ChargeCardTransactionLineitem | ExpenseReportLineitem | JournalEntryLineitem | BillLineitem) -> str:
        """
        Create Link For Fyle Expenses
        :param expense: Expense Lineitem
        :return: Expense link
        """
        workspace = Workspace.objects.get(id=self.workspace_id)
        org_id = workspace.fyle_org_id
        cluster_domain = workspace.cluster_domain

        if not cluster_domain:
            fyle_credentials = FyleCredential.objects.get(workspace_id=self.workspace_id)
            cluster_domain = fyle_credentials.cluster_domain
            workspace.cluster_domain = cluster_domain
            workspace.save()

        expense_link = '{0}/app/admin/#/company_expenses?txnId={1}&org_id={2}'.format(
            settings.FYLE_EXPENSE_URL, lineitem.expense.expense_id, org_id
        )

        return expense_link

    def post_employees(self, employee: ExpenseAttribute) -> dict:
        """
        Create a Vendor on Sage Intacct
        :param employee: employee attribute to be created
        :return Employee Destination Attribute
        """
        department = DestinationAttribute.objects.filter(
            workspace_id=self.workspace_id, attribute_type='DEPARTMENT',
            value__iexact=employee.detail['department']).first()

        location = DestinationAttribute.objects.filter(
            workspace_id=self.workspace_id, attribute_type='LOCATION',
            value__iexact=employee.detail['location']).first()

        general_mappings = GeneralMapping.objects.filter(workspace_id=employee.workspace_id).first()

        sage_intacct_display_name = employee.detail['full_name']

        name = employee.detail['full_name'].split(' ')

        try:
            contact = {
                'CONTACTNAME': sage_intacct_display_name,
                'PRINTAS': sage_intacct_display_name,
                'EMAIL1': employee.value,
                'FIRSTNAME': name[0],
                'LASTNAME': name[-1] if len(name) == 2 else None
            }

            self.connection.contacts.post(contact)

        except Exception as e:
            logger.info(e.response)

        location_id = location.destination_id if location else None
        department_id = department.destination_id if department else None

        if not location_id and general_mappings:
            location_id = general_mappings.default_location_id

        if not department_id and general_mappings:
            department_id = general_mappings.default_department_id

        employee_payload = {
            'PERSONALINFO': {
                'CONTACTNAME': sage_intacct_display_name
            },
            'EMPLOYEEID': sage_intacct_display_name,
            'LOCATIONID': location_id,
            'DEPARTMENTID': department_id
        }

        created_employee = self.connection.employees.post(employee_payload)['data']['employee']

        return created_employee

    def sync_vendors(self) -> list:
        """
        Get vendors
        """
        fields = ['DISPLAYCONTACT.EMAIL1', 'NAME', 'VENDORID', 'STATUS']
        latest_updated_at = self.get_latest_sync(workspace_id=self.workspace_id, attribute_type='ACCOUNT')
        params = self.construct_get_all_generator_params(fields=fields, latest_updated_at=latest_updated_at)
        vendor_generator = self.connection.vendors.get_all_generator(**params)
        vendor_attributes = []

        for vendors in vendor_generator:
            for vendor in vendors:
                detail = {
                    'email': vendor['DISPLAYCONTACT.EMAIL1'] if vendor['DISPLAYCONTACT.EMAIL1'] else None
                }
                vendor_attributes.append({
                    'attribute_type': 'VENDOR',
                    'display_name': 'vendor',
                    'value': vendor['NAME'],
                    'destination_id': vendor['VENDORID'],
                    'detail': detail,
                    'active': vendor['STATUS'] == 'active'
                })

        if vendor_attributes:
            DestinationAttribute.bulk_create_or_update_destination_attributes(
                vendor_attributes, 'VENDOR', self.workspace_id, True,
                app_name=get_app_name(),
                attribute_disable_callback_path=self.get_attribute_disable_callback_path('VENDOR'),
                skip_deletion=self.is_duplicate_deletion_skipped('VENDOR'),
                is_import_to_fyle_enabled=self.is_import_enabled('VENDOR')
            )

        return []

    def post_vendor(self, vendor_id: str, vendor_name: str, email: str = None) -> dict:
        """
        Create a Vendor on Sage Intacct
        :param vendor: vendor attribute to be created
        :return Vendor Destination Attribute
        """
        sage_intacct_display_name = vendor_name

        name = vendor_name.split(' ')

        vendor_payload = {
            'NAME': sage_intacct_display_name,
            'VENDORID': vendor_id,
            'DISPLAYCONTACT': {
                'PRINTAS': sage_intacct_display_name,
                'EMAIL1': email,
                'FIRSTNAME': name[0],
                'LASTNAME': name[-1] if len(name) == 2 else None
            }
        }
        logger.info("| Payload for the vendor creation | Content : {{WORKSPACE_ID = {}, VENDOR_PAYLOAD = {}}}".format(self.workspace_id, vendor_payload))

        created_vendor = self.connection.vendors.post(vendor_payload)['data']['vendor']

        return created_vendor

    def __construct_expense_report(
        self,
        expense_report: ExpenseReport,
        expense_report_lineitems: list[ExpenseReportLineitem]
    ) -> dict:
        """
        Create a expense report
        :param expense_report: ExpenseReport object extracted from database
        :param expense_report_lineitems: ExpenseReportLineitem objects extracted from database
        :return: constructed expense_report
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        general_mappings = GeneralMapping.objects.get(workspace_id=self.workspace_id)

        expense_payload = []
        for lineitem in expense_report_lineitems:
            transaction_date = lineitem.transaction_date
            expense_link = self.get_expense_link(lineitem)

            tax_exclusive_amount, _ = self.get_tax_exclusive_amount(lineitem.amount, general_mappings.default_tax_code_id)
            amount = lineitem.amount - lineitem.tax_amount if (lineitem.tax_code and lineitem.tax_amount) else tax_exclusive_amount
            amount = round(amount, 2)

            expense = {
                'expensetype' if lineitem.expense_type_id else 'glaccountno': lineitem.expense_type_id \
                if lineitem.expense_type_id else lineitem.gl_account_number,
                'amount': amount,
                'expensedate': {
                    'year': transaction_date.year,
                    'month': transaction_date.month,
                    'day': transaction_date.day
                },
                'memo': lineitem.memo,
                'locationid': lineitem.location_id,
                'departmentid': lineitem.department_id,
                'customfields': {
                    'customfield': [{
                        'customfieldname': 'FYLE_EXPENSE_URL',
                        'customfieldvalue': expense_link
                    }]
                },
                'projectid': lineitem.project_id,
                'taskid': lineitem.task_id,
                'costtypeid': lineitem.cost_type_id,
                'customerid': lineitem.customer_id,
                'itemid': lineitem.item_id,
                'classid': lineitem.class_id,
                'billable': lineitem.billable,
                'exppmttype': lineitem.expense_payment_type,
                'totaltrxamount': lineitem.amount,
                'taxentries': {
                    'taxentry': {
                        'detailid': lineitem.tax_code if (lineitem.tax_code and lineitem.tax_amount) else general_mappings.default_tax_code_id,
                    }
                }
            }

            for dimension in lineitem.user_defined_dimensions:
                customfield = {
                    'customfieldname': list(dimension.keys())[0],
                    'customfieldvalue': list(dimension.values())[0]
                }
                expense['customfields']['customfield'].append(customfield)

            expense_payload.append(expense)

        transaction_date = datetime.strptime(expense_report.transaction_date, '%Y-%m-%dT%H:%M:%S')
        expense_report_payload = {
            'employeeid': expense_report.employee_id,
            'datecreated': {
                'year': transaction_date.year,
                'month': transaction_date.month,
                'day': transaction_date.day
            },
            'state': 'Submitted',
            'supdocid': expense_report.supdoc_id,
            'description': expense_report.memo,
            'basecurr': expense_report.currency,
            'currency': expense_report.currency,
            'expenses': {
                'expense': expense_payload
            }
        }

        if configuration.import_tax_codes:
            expense_report_payload.update({
                'inclusivetax': True,
                'taxsolutionid': self.get_tax_solution_id_or_none(expense_report_lineitems),
            })

        logger.info("| Payload for the expense report creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, EXPENSE_REPORT_PAYLOAD = {}}}".format(self.workspace_id, expense_report.expense_group.id, expense_report_payload))
        return expense_report_payload

    def __construct_bill(self, bill: Bill, bill_lineitems: list[BillLineitem]) -> dict:
        """
        Create a bill
        :param bill: Bill object extracted from database
        :param bill_lineitems: BillLineItem objects extracted from database
        :return: constructed bill
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        general_mappings = GeneralMapping.objects.get(workspace_id=self.workspace_id)

        bill_lineitems_payload = []
        for lineitem in bill_lineitems:
            expense_link = self.get_expense_link(lineitem)
            tax_exclusive_amount, _ = self.get_tax_exclusive_amount(abs(lineitem.amount), general_mappings.default_tax_code_id)

            expense = {
                'ACCOUNTNO': lineitem.gl_account_number,
                'TRX_AMOUNT': lineitem.amount - lineitem.tax_amount if (lineitem.tax_code and lineitem.tax_amount) else tax_exclusive_amount,
                'TOTALTRXAMOUNT': lineitem.amount,
                'ENTRYDESCRIPTION': lineitem.memo,
                'LOCATIONID': lineitem.location_id,
                'DEPARTMENTID': lineitem.department_id,
                'PROJECTID': lineitem.project_id,
                'CUSTOMERID': lineitem.customer_id,
                'ITEMID': lineitem.item_id,
                'TASKID': lineitem.task_id,
                'COSTTYPEID': lineitem.cost_type_id,
                'CLASSID': lineitem.class_id,
                'BILLABLE': lineitem.billable,
                'ALLOCATION': lineitem.allocation_id,
                'TAXENTRIES': {
                    'TAXENTRY': {
                        'DETAILID': lineitem.tax_code if (lineitem.tax_code and lineitem.tax_amount) else general_mappings.default_tax_code_id
                    }
                },
                'customfields': {
                    'customfield': [{
                        'customfieldname': 'FYLE_EXPENSE_URL',
                        'customfieldvalue': expense_link
                    }]
                }
            }

            # case of a refund
            if lineitem.amount < 0:
                expense['TRX_AMOUNT'] = round(-(abs(lineitem.amount) - abs(lineitem.tax_amount) if (lineitem.tax_code and lineitem.tax_amount) else tax_exclusive_amount), 2)

            for dimension in lineitem.user_defined_dimensions:
                for name, value in dimension.items():
                    expense[name] = value

            bill_lineitems_payload.append(expense)

        transaction_date = datetime.strptime(bill.transaction_date, '%Y-%m-%dT%H:%M:%S')
        transaction_date = '{0}/{1}/{2}'.format(transaction_date.month, transaction_date.day, transaction_date.year)
        current_date = '{0}/{1}/{2}'.format(datetime.today().month, datetime.today().day, datetime.today().year)

        bill_payload = {
            'WHENCREATED': transaction_date,
            'VENDORID': bill.vendor_id,
            'RECORDID': bill.memo,
            'WHENDUE': current_date,
            'BASECURR': bill.currency,
            'SUPDOCID': bill.supdoc_id,
            'CURRENCY': bill.currency,
            'EXCH_RATE_TYPE_ID': None,
            'APBILLITEMS': {
                'APBILLITEM': bill_lineitems_payload
            }
        }

        if configuration.import_tax_codes:
            expense.update({
                'INCLUSIVETAX': True,
                'TAXSOLUTIONID': self.get_tax_solution_id_or_none(bill_lineitems)
            })

        logger.info("| Payload for the bill creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, BILL_PAYLOAD = {}}}".format(self.workspace_id, bill.expense_group.id, bill_payload))
        return bill_payload

    def __construct_charge_card_transaction(
        self,
        charge_card_transaction: ChargeCardTransaction,
        charge_card_transaction_lineitems: list[ChargeCardTransactionLineitem]
    ) -> dict:
        """
        Create a charge card transaction
        :param charge_card_transaction: ChargeCardTransaction object extracted from database
        :param charge_card_transaction_lineitems: ChargeCardTransactionLineitem objects extracted from database
        :return: constructed charge_card_transaction
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        general_mappings = GeneralMapping.objects.get(workspace_id=self.workspace_id)

        charge_card_transaction_lineitem_payload = []
        for lineitem in charge_card_transaction_lineitems:
            expense_link = self.get_expense_link(lineitem)

            tax_exclusive_amount, _ = self.get_tax_exclusive_amount(lineitem.amount, general_mappings.default_tax_code_id)
            expense = {
                'glaccountno': lineitem.gl_account_number,
                'description': lineitem.memo,
                'paymentamount': lineitem.amount - lineitem.tax_amount if (lineitem.tax_code and lineitem.tax_amount) else tax_exclusive_amount,
                'departmentid': lineitem.department_id,
                'locationid': lineitem.location_id,
                'customerid': lineitem.customer_id,
                'vendorid': charge_card_transaction.vendor_id,
                'projectid': lineitem.project_id,
                'taskid': lineitem.task_id,
                'costtypeid': lineitem.cost_type_id,
                'itemid': lineitem.item_id,
                'classid': lineitem.class_id,
                'customfields': {
                    'customfield': [{
                        'customfieldname': 'FYLE_EXPENSE_URL',
                        'customfieldvalue': expense_link
                    }]
                },
                'totaltrxamount': lineitem.amount,
                'taxentries': {
                    'taxentry': {
                        'detailid': lineitem.tax_code if (lineitem.tax_code and lineitem.tax_amount) else general_mappings.default_tax_code_id,
                    }
                },
                'billable': lineitem.billable
            }

            for dimension in lineitem.user_defined_dimensions:
                customfield = {
                    'customfieldname': list(dimension.keys())[0],
                    'customfieldvalue': list(dimension.values())[0]
                }
                expense['customfields']['customfield'].append(customfield)

            charge_card_transaction_lineitem_payload.append(expense)

        transaction_date = datetime.strptime(charge_card_transaction.transaction_date, '%Y-%m-%dT%H:%M:%S')
        charge_card_transaction_payload = {
            'chargecardid': charge_card_transaction.charge_card_id,
            'paymentdate': {
                'year': transaction_date.year,
                'month': transaction_date.month,
                'day': transaction_date.day
            },
            'referenceno': charge_card_transaction.reference_no,
            'payee': charge_card_transaction.payee,
            'description': charge_card_transaction.memo,
            'supdocid': charge_card_transaction.supdoc_id,
            'currency': charge_card_transaction.currency,
            'exchratetype': None,
            'inclusivetax': True if configuration.import_tax_codes else False,
            'ccpayitems': {
                'ccpayitem': charge_card_transaction_lineitem_payload
            }
        }

        logger.info("| Payload for the charge card transaction creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, CHARGE_CARD_TRANSACTION_PAYLOAD = {}}}".format(self.workspace_id, charge_card_transaction.expense_group.id, charge_card_transaction_payload))
        return charge_card_transaction_payload

    def __get_dimensions_values(self, lineitem: JournalEntryLineitem, workspace_id: int) -> dict:
        """
        Get dimension values for a line item, handling allocation if present
        :param lineitem: JournalEntryLineitem object
        :param workspace_id: Workspace ID
        :return: Dictionary of dimension values
        """
        dimensions_values = {
            'project_id': lineitem.project_id,
            'location_id': lineitem.location_id,
            'department_id': lineitem.department_id,
            'class_id': lineitem.class_id,
            'customer_id': lineitem.customer_id,
            'item_id': lineitem.item_id,
            'task_id': lineitem.task_id,
            'cost_type_id': lineitem.cost_type_id
        }

        if lineitem.allocation_id:
            allocation_mapping = {
                'LOCATIONID': 'location_id',
                'DEPARTMENTID': 'department_id',
                'CLASSID': 'class_id',
                'CUSTOMERID': 'customer_id',
                'ITEMID': 'item_id',
                'TASKID': 'task_id',
                'COSTTYPEID': 'cost_type_id',
                'PROJECTID': 'project_id'
            }

            allocation_detail = DestinationAttribute.objects.filter(
                workspace_id=workspace_id,
                attribute_type='ALLOCATION',
                value=lineitem.allocation_id
            ).first().detail

            for allocation_dimension, dimension_variable_name in allocation_mapping.items():
                if allocation_dimension in allocation_detail.keys():
                    dimensions_values[dimension_variable_name] = None

            allocation_dimensions = set(allocation_detail.keys())
            lineitem.user_defined_dimensions = [
                user_defined_dimension for user_defined_dimension in lineitem.user_defined_dimensions
                if list(user_defined_dimension.keys())[0] not in allocation_dimensions
            ]

        return dimensions_values

    def __get_location_id_for_journal_entry(self, workspace_id: int) -> Optional[str]:
        """
        Get location ID based on configuration.

        :param workspace_id: Workspace ID
        :return: Location ID or None if not found
        """
        general_mapping = (
            GeneralMapping.objects
            .filter(workspace_id=workspace_id, default_location_id__isnull=False)
            .values('default_location_id')
            .first()
        )
        if general_mapping:
            return general_mapping['default_location_id']

        location_mapping = (
            LocationEntityMapping.objects
            .filter(workspace_id=workspace_id)
            .exclude(location_entity_name='Top Level')
            .values('location_entity_name', 'destination_id')
            .first()
        )
        if location_mapping:
            return location_mapping['destination_id']

        return None

    def __construct_single_itemized_credit_line(self, journal_entry_lineitems: list[JournalEntryLineitem], general_mappings: GeneralMapping, journal_entry: JournalEntry, configuration: Configuration) -> list[dict]:
        """
        Create credit lines grouped by vendor with summed amounts
        :param journal_entry_lineitems: List of JournalEntryLineItem objects
        :param general_mappings: GeneralMapping object
        :param journal_entry: JournalEntry object
        :param configuration: Configuration object
        :return: List of credit line dictionaries grouped by vendor
        """
        # Group lineitems by vendor
        vendor_groups = {}
        for lineitem in journal_entry_lineitems:
            vendor_id = lineitem.vendor_id
            if vendor_id not in vendor_groups:
                vendor_groups[vendor_id] = []
            vendor_groups[vendor_id].append(lineitem)

        credit_lines = []
        for vendor_id, lineitems in vendor_groups.items():
            total_amount = sum(lineitem.amount for lineitem in lineitems)
            # Skip if total amount is zero
            if total_amount == 0:
                continue

            # Handle refund case
            tr_type = 1 if total_amount < 0 else -1
            amount = abs(total_amount)

            credit_line = {
                'accountno': general_mappings.default_credit_card_id if journal_entry.expense_group.fund_source == 'CCC' else general_mappings.default_gl_account_id,
                'currency': journal_entry.currency,
                'vendorid': vendor_id,
                'location': self.__get_location_id_for_journal_entry(self.workspace_id),
                'employeeid': lineitems[0].employee_id,
                'amount': round(amount, 2),
                'tr_type': tr_type,
                'description': 'Total Credit Line'
            }
            credit_lines.append(credit_line)

        return credit_lines

    def __construct_base_line_item(self, lineitem: JournalEntryLineitem, dimensions_values: dict, journal_entry: JournalEntry, expense_link: str) -> dict:
        """
        Create base line item with common fields
        :param lineitem: JournalEntryLineitem object
        :param dimensions_values: Dictionary of dimension values
        :param journal_entry: JournalEntry object
        :param expense_link: Expense link URL
        :return: Base line item dictionary
        """
        return {
            'currency': journal_entry.currency,
            'description': lineitem.memo,
            'department': dimensions_values['department_id'],
            'location': dimensions_values['location_id'],
            'projectid': dimensions_values['project_id'],
            'customerid': dimensions_values['customer_id'],
            'vendorid': lineitem.vendor_id,
            'employeeid': lineitem.employee_id,
            'classid': dimensions_values['class_id'],
            'itemid': dimensions_values['item_id'],
            'taskid': dimensions_values['task_id'],
            'costtypeid': dimensions_values['cost_type_id'],
            'allocation': lineitem.allocation_id,
            'customfields': {
                'customfield': [{
                    'customfieldname': 'FYLE_EXPENSE_URL',
                    'customfieldvalue': expense_link
                }]
            }
        }

    def __construct_journal_entry(self, journal_entry: JournalEntry, journal_entry_lineitems: list[JournalEntryLineitem], supdocid: str = None, recordno: str = None) -> dict:
        """
        Create a journal_entry
        :param journal_entry: JournalEntry object extracted from database
        :param journal_entry_lineitems: JournalEntryLineItem objects extracted from database
        :param supdocid: SupDocId
        :param recordno: RecordNo
        :return: constructed journal_entry
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        general_mappings = GeneralMapping.objects.get(workspace_id=self.workspace_id)

        journal_entry_payload = []

        # Process debit lines for all line items (consistent behavior)
        for lineitem in journal_entry_lineitems:
            dimensions_values = self.__get_dimensions_values(lineitem, self.workspace_id)
            expense_link = self.get_expense_link(lineitem)
            tax_inclusive_amount, tax_amount = self.get_tax_exclusive_amount(abs(lineitem.amount), general_mappings.default_tax_code_id)

            # Create base line item
            base_line_item = self.__construct_base_line_item(lineitem, dimensions_values, journal_entry, expense_link)

            # Create debit line
            debit_line = base_line_item.copy()
            debit_line.update({
                'accountno': lineitem.gl_account_number,
                'amount': round((lineitem.amount - lineitem.tax_amount), 2) if (lineitem.tax_code and lineitem.tax_amount) else tax_inclusive_amount,
                'tr_type': 1,
                'billable': lineitem.billable,
                'taxentries': {
                    'taxentry': {
                        'trx_tax': lineitem.tax_amount if (lineitem.tax_code and lineitem.tax_amount) else tax_amount,
                        'detailid': lineitem.tax_code if (lineitem.tax_code and lineitem.tax_amount) else general_mappings.default_tax_code_id,
                    }
                }
            })

            # Handle refund case
            if lineitem.amount < 0:
                amount = abs(lineitem.amount)
                debit_line['amount'] = amount
                debit_line['tr_type'] = -1

            # Add user defined dimensions
            for dimension in lineitem.user_defined_dimensions:
                for name, value in dimension.items():
                    debit_line[name] = value

            journal_entry_payload.append(debit_line)

        # Handle credit lines based on configuration
        if configuration.je_single_credit_line:
            # Create credit lines grouped by vendor
            credit_lines = self.__construct_single_itemized_credit_line(journal_entry_lineitems, general_mappings, journal_entry, configuration)
            # Insert all credit lines at the beginning to maintain order
            for credit_line in reversed(credit_lines):
                journal_entry_payload.insert(0, credit_line)
        else:
            # Process credit lines for each line item
            for i, lineitem in enumerate(journal_entry_lineitems):
                dimensions_values = self.__get_dimensions_values(lineitem, self.workspace_id)
                expense_link = self.get_expense_link(lineitem)
                tax_inclusive_amount, tax_amount = self.get_tax_exclusive_amount(abs(lineitem.amount), general_mappings.default_tax_code_id)

                # Create base line item
                base_line_item = self.__construct_base_line_item(lineitem, dimensions_values, journal_entry, expense_link)

                # Create credit line
                credit_line = base_line_item.copy()
                credit_line.update({
                    'accountno': general_mappings.default_credit_card_id if journal_entry.expense_group.fund_source == 'CCC' else general_mappings.default_gl_account_id,
                    'amount': round(lineitem.amount, 2),
                    'tr_type': -1,
                    'billable': lineitem.billable if configuration.is_journal_credit_billable else None
                })

                # Handle refund case
                if lineitem.amount < 0:
                    amount = abs(lineitem.amount)
                    credit_line['amount'] = round(amount - abs(lineitem.tax_amount) if (lineitem.tax_code and lineitem.tax_amount) else tax_inclusive_amount, 2)
                    credit_line['tr_type'] = 1
                    # Copy tax entries to credit line in refund case
                    debit_line_index = i * 2  # Calculate actual index of debit line after credit line insertion
                    credit_line['taxentries'] = journal_entry_payload[debit_line_index]['taxentries'].copy()
                    journal_entry_payload[debit_line_index].pop('taxentries')

                # Add user defined dimensions
                for dimension in lineitem.user_defined_dimensions:
                    for name, value in dimension.items():
                        credit_line[name] = value

                journal_entry_payload.insert(i * 2, credit_line)  # Insert before corresponding debit line

        # Format transaction date
        transaction_date = datetime.strptime(journal_entry.transaction_date, '%Y-%m-%dT%H:%M:%S')
        transaction_date = '{0}/{1}/{2}'.format(transaction_date.month, transaction_date.day, transaction_date.year)

        supdocid = journal_entry.supdoc_id or supdocid

        # Construct final payload
        journal_entry_payload = {
            'recordno': recordno if recordno else None,
            'journal': 'FYLE_JE' if settings.BRAND_ID == 'fyle' else 'EM_JOURNAL',
            'batch_date': transaction_date,
            'batch_title': journal_entry.memo,
            'supdocid': supdocid,
            'entries': [{
                'glentry': journal_entry_payload
            }]
        }

        # Add tax implications if configured
        if configuration.import_tax_codes:
            journal_entry_payload.update({
                'taximplications': 'Inbound',
                'taxsolutionid': self.get_tax_solution_id_or_none(journal_entry_lineitems),
            })

        logger.info("| Payload for the journal entry report creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, JOURNAL_ENTRY_PAYLOAD = {}}}".format(
            self.workspace_id, journal_entry.expense_group.id, journal_entry_payload
        ))
        return journal_entry_payload

    def post_expense_report(self, expense_report: ExpenseReport, expense_report_lineitems: list[ExpenseReportLineitem]) -> dict:
        """
        Post expense report to Sage Intacct
        :param expense_report: ExpenseReport object extracted from database
        :param expense_report_lineitems: ExpenseReportLineitem objects extracted from database
        :return: created expense report
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        try:
            expense_report_payload = self.__construct_expense_report(expense_report, expense_report_lineitems)
            created_expense_report = self.connection.expense_reports.post(expense_report_payload)
            return created_expense_report
        except WrongParamsError as exception:
            logger.info(exception.response)
            if 'error' in exception.response:
                sage_intacct_errors = exception.response['error']
                error_words_list = ['period', 'closed', 'Date must be on or after']
                if any(word in sage_intacct_errors[0]['description2'] for word in error_words_list):
                    if configuration.change_accounting_period:
                        first_day_of_month = datetime.today().date().replace(day=1)
                        expense_report_payload = self.__construct_expense_report(expense_report, expense_report_lineitems)
                        expense_report_payload['datecreated'] = {
                            'year': first_day_of_month.year,
                            'month': first_day_of_month.month,
                            'day': first_day_of_month.day
                        },
                        created_expense_report = self.connection.expense_reports.post(expense_report_payload)
                        return created_expense_report
                    else:
                        raise
                else:
                    raise
            else:
                raise

    def post_bill(self, bill: Bill, bill_lineitems: list[BillLineitem]) -> dict:
        """
        Post expense report to Sage Intacct
        :param bill: Bill object
        :param bill_lineitems: BillLineitem objects
        :return: created bill
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        try:
            bill_payload = self.__construct_bill(bill, bill_lineitems)
            created_bill = self.connection.bills.post(bill_payload)
            return created_bill

        except WrongParamsError as exception:
            logger.info(exception.response)
            if 'error' in exception.response:
                sage_intacct_errors = exception.response['error']
                error_words_list = ['period', 'closed', 'Date must be on or after']
                if any(word in sage_intacct_errors[0]['description2'] for word in error_words_list):
                    if configuration.change_accounting_period:
                        first_day_of_month = datetime.today().date().replace(day=1)
                        bill_payload = self.__construct_bill(bill, bill_lineitems)
                        bill_payload['WHENCREATED'] = first_day_of_month
                        created_bill = self.connection.bills.post(bill_payload)
                        return created_bill
                    else:
                        raise
                else:
                    raise
            else:
                raise

    def post_journal_entry(self, journal_entry: JournalEntry, journal_entry_lineitems: list[JournalEntryLineitem]) -> dict:
        """
        Post journal_entry  to Sage Intacct
        :param journal_entry: JournalEntry object
        :param journal_entry_lineitems: JournalEntryLineitem objects
        :return: created journal_entry
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        try:
            journal_entry_payload = self.__construct_journal_entry(journal_entry, journal_entry_lineitems)
            created_journal_entry = self.connection.journal_entries.post(journal_entry_payload)
            return created_journal_entry

        except WrongParamsError as exception:
            logger.info(exception.response)
            if 'error' in exception.response:
                sage_intacct_errors = exception.response['error']
                error_words_list = ['period', 'closed', 'Date must be on or after']
                if any(word in sage_intacct_errors[0]['description2'] for word in error_words_list):
                    if configuration.change_accounting_period:
                        first_day_of_month = datetime.today().date().replace(day=1)
                        journal_entry_payload = self.__construct_journal_entry(journal_entry, journal_entry_lineitems)
                        journal_entry_payload['batch_date'] = first_day_of_month
                        created_journal_entry = self.connection.journal_entries.post(journal_entry_payload)
                        return created_journal_entry
                    else:
                        raise
                else:
                    raise
            else:
                raise

    def get_bill(self, bill_id: str, fields: list = None) -> dict:
        """
        GET bill from SAGE Intacct
        :param bill_id: Bill Id
        :param fields: Fields to be fetched
        :return: Bill
        """
        bill = self.connection.bills.get(field='RECORDNO', value=bill_id, fields=fields)
        return bill

    def get_bills(self, bill_ids: list[str], fields: list = None) -> list[dict]:
        """
        GET bills from SAGE Intacct
        :param bill_ids: Bill Ids
        :param fields: Fields to be fetched
        :return: Bills
        """
        and_filter = [('in', 'RECORDNO', bill_ids)]
        if not fields:
            fields = ['RECORDNO', 'STATE']
        bills = self.connection.bills.get_by_query(and_filter=and_filter, fields=fields)
        return bills

    def get_expense_report(self, expense_report_id: str, fields: list = None) -> dict:
        """
        GET expense reports from SAGE
        :param expense_report_id: Expense Report Id
        :param fields: Fields to be fetched
        :return: Expense Report
        """
        expense_report = self.connection.expense_reports.get(field='RECORDNO', value=expense_report_id, fields=fields)
        return expense_report

    def get_expense_reports(self, expense_report_ids: list[str], fields: list = None) -> list[dict]:
        """
        GET expense reports from SAGE
        :param expense_report_ids: Expense Report Ids
        :param fields: Fields to be fetched
        :return: Expense Reports
        """
        and_filter = [('in', 'RECORDNO', expense_report_ids)]
        if not fields:
            fields = ['RECORDNO', 'STATE']
        expense_reports = self.connection.expense_reports.get_by_query(and_filter=and_filter, fields=fields)
        return expense_reports

    def get_journal_entry(self, journal_entry_id: str, fields: list = None) -> dict:
        """
        GET journal_entry from SAGE Intacct
        :param journal_entry_id: Journal Entry Id
        :param fields: Fields to be fetched
        :return: Journal Entry
        """
        journal_entry = self.connection.journal_entries.get(field='RECORDNO', value=journal_entry_id, fields=fields)
        return journal_entry

    def post_charge_card_transaction(
        self,
        charge_card_transaction: ChargeCardTransaction,
        charge_card_transaction_lineitems: list[ChargeCardTransactionLineitem]
    ) -> dict:
        """
        Post charge card transaction to Sage Intacct
        :param charge_card_transaction: ChargeCardTransaction object
        :param charge_card_transaction_lineitems: ChargeCardTransactionLineitem objects
        :return: created charge card transaction
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        try:
            created_charge_card_transaction_payload = self.__construct_charge_card_transaction(
                charge_card_transaction,
                charge_card_transaction_lineitems
            )
            created_charge_card_transaction = self.connection.charge_card_transactions.post(created_charge_card_transaction_payload)
            return created_charge_card_transaction

        except WrongParamsError as exception:
            logger.info(exception.response)
            if 'error' in exception.response:
                sage_intacct_errors = exception.response['error']
                error_words_list = ['period', 'closed', 'Date must be on or after']
                if any(word in sage_intacct_errors[0]['description2'] for word in error_words_list):
                    if configuration.change_accounting_period:
                        first_day_of_month = datetime.today().date().replace(day=1)
                        charge_card_transaction_payload = self.__construct_charge_card_transaction(
                            charge_card_transaction, charge_card_transaction_lineitems
                        )
                        charge_card_transaction_payload['paymentdate'] = {
                            'year': first_day_of_month.year,
                            'month': first_day_of_month.month,
                            'day': first_day_of_month.day
                        },
                        created_charge_card_transaction = self.connection.charge_card_transactions.post(
                            charge_card_transaction_payload
                        )
                        return created_charge_card_transaction
                    else:
                        raise
                else:
                    raise
            else:
                raise

    def get_charge_card_transaction(self, charge_card_transaction_id: str, fields: list = None) -> dict:
        """
        GET charge card transaction from SAGE Intacct
        :param charge_card_transaction_id: Charge Card Transaction Id
        :param fields: Fields to be fetched
        :return: Charge Card Transaction
        """
        charge_card_transaction = self.connection.charge_card_transactions.get(
            field='RECORDNO', value=charge_card_transaction_id, fields=fields)
        return charge_card_transaction

    def update_expense_report(self, object_key: str, supdocid: str) -> dict:
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: expense report key
        :param supdocid: attachments id
        :return: response from sage intacct
        """
        return self.connection.expense_reports.update_attachment(key=object_key, supdocid=supdocid)

    def update_bill(self, object_key: str, supdocid: str) -> dict:
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: expense report key
        :param supdocid: attachments id
        :return: response from sage intacct
        """
        return self.connection.bills.update_attachment(recordno=object_key, supdocid=supdocid)

    def update_charge_card_transaction(self, object_key: str, supdocid: str) -> dict:
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: charge card transaction key
        :param supdocid: attachments id
        :return: response from sage intacct
        """
        return self.connection.charge_card_transactions.update_attachment(key=object_key, supdocid=supdocid)

    def update_journal_entry(self, journal_entry: JournalEntry, journal_entry_lineitems: list[JournalEntryLineitem], supdocid: str, recordno: str) -> dict:
        """
        Map posted attachment with Sage Intacct Object
        :param supdocid: attachments id
        :param recordno: record no
        :return: response from sage intacct
        """
        journal_entry_payload = self.__construct_journal_entry(journal_entry, journal_entry_lineitems, supdocid, recordno)
        return self.connection.journal_entries.update(journal_entry_payload)

    def post_attachments(self, attachments: list[dict], supdoc_id: str, attachment_number: int) -> str | bool:
        """
        Post attachments to Sage Intacct
        :param attachments: List of attachment dictionaries
        :param supdoc_id: Supporting document ID to be used in Sage Intacct
        :param attachment_number: Number used to uniquely name attachments
        :return: supdoc_id if first attachment is successfully posted, else False
        """
        if not attachments:
            return False

        for attachment in attachments:
            attachment_type = attachment['name'].split('.')[-1]
            attachment_data = {
                'attachmentname': f"{attachment['id']} - {attachment_number}",
                'attachmenttype': attachment_type,
                'attachmentdata': attachment['download_url'],
            }

            payload = {
                'supdocid': supdoc_id,
                'supdocfoldername': 'FyleAttachments',
                'attachments': {
                    'attachment': [attachment_data]
                }
            }

            if attachment_number == 1:
                created_attachment = self.connection.attachments.post(payload)
            else:
                try:
                    self.connection.attachments.update(payload)
                except Exception:
                    logger.info(f"Error updating attachment {attachment_number} for supdoc {supdoc_id}")
                    continue

        if attachment_number == 1 and created_attachment.get('status') == 'success' and created_attachment.get('key'):
            return supdoc_id

        return False

    @staticmethod
    def __construct_ap_payment(ap_payment: APPayment, ap_payment_lineitems: list[APPaymentLineitem]) -> dict:
        """
        Create an AP Payment
        :param ap_payment: APPayment object extracted from database
        :param ap_payment_lineitems: APPaymentLineItem objects extracted from database
        :return: constructed AP Payment
        """
        ap_payment_lineitems_payload = []

        for lineitem in ap_payment_lineitems:
            payment_detail = {
                'RECORDKEY': lineitem.record_key,
                'TRX_PAYMENTAMOUNT': lineitem.amount
            }

            ap_payment_lineitems_payload.append(payment_detail)

        current_date = '{0}/{1}/{2}'.format(datetime.today().month, datetime.today().day, datetime.today().year)

        ap_payment_payload = {
            'FINANCIALENTITY': ap_payment.payment_account_id,
            'PAYMENTMETHOD': 'Cash',
            'VENDORID': ap_payment.vendor_id,
            'DESCRIPTION': ap_payment.description,
            'PAYMENTDATE': current_date,
            'CURRENCY': ap_payment.currency,
            'BASECURR': ap_payment.currency,
            'APPYMTDETAILS': {
                'APPYMTDETAIL': ap_payment_lineitems_payload
            }
        }

        logger.info("| Payload for the AP Payment creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, AP_PAYMENT_PAYLOAD = {}}}".format(ap_payment.expense_group.workspace.id, ap_payment.expense_group.id, ap_payment_payload))
        return ap_payment_payload

    def post_ap_payment(self, ap_payment: APPayment, ap_payment_lineitems: list[APPaymentLineitem]) -> dict:
        """
        Post AP Payment to Sage Intacct
        :param ap_payment: APPayment object
        :param ap_payment_lineitems: APPaymentLineItem objects
        :return: created AP Payment
        """
        ap_payment_payload = self.__construct_ap_payment(ap_payment, ap_payment_lineitems)
        created_ap_payment = self.connection.ap_payments.post(ap_payment_payload)
        return created_ap_payment

    @staticmethod
    def __construct_sage_intacct_reimbursement(
        reimbursement: SageIntacctReimbursement,
        reimbursement_lineitems: list[SageIntacctReimbursementLineitem]
    ) -> dict:
        """
        Create a Reimbursement
        :param reimbursement: Reimbursement object extracted from database
        :param reimbursement_lineitems: ReimbursementLineItem objects extracted from database
        :return: constructed Reimbursement
        """
        reimbursement_lineitems_payload = []

        for lineitem in reimbursement_lineitems:
            reimbursement_detail = {
                'key': lineitem.record_key,
                'paymentamount': lineitem.amount
            }

            reimbursement_lineitems_payload.append(reimbursement_detail)

        reimbursement_payload = {
            'bankaccountid': reimbursement.account_id,
            'employeeid': reimbursement.employee_id,
            'memo': reimbursement.memo,
            'paymentmethod': 'Cash',
            'paymentdate': {
                'year': datetime.now().strftime('%Y'),
                'month': datetime.now().strftime('%m'),
                'day': datetime.now().strftime('%d')
            },
            'eppaymentrequestitems': {
                'eppaymentrequestitem': reimbursement_lineitems_payload
            },
            'paymentdescription': reimbursement.payment_description
        }

        logger.info("| Payload for the reimbursement creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, REIMBURSEMENT_PAYLOAD = {}}}".format(reimbursement.expense_group.workspace.id, reimbursement.expense_group.id, reimbursement_payload))
        return reimbursement_payload

    def post_sage_intacct_reimbursement(
        self,
        reimbursement: SageIntacctReimbursement,
        reimbursement_lineitems: list[SageIntacctReimbursementLineitem]
    ) -> dict:
        """
        Post Reimbursement to Sage Intacct
        :param reimbursement: SageIntacctReimbursement object
        :param reimbursement_lineitems: SageIntacctReimbursementLineItem objects
        :return: created Reimbursement
        """
        reimbursement_payload = self.__construct_sage_intacct_reimbursement(reimbursement, reimbursement_lineitems)
        created_reimbursement = self.connection.reimbursements.post(reimbursement_payload)
        return created_reimbursement

    def sanitize_vendor_name(self, vendor_name: str = None) -> str:
        """
        Remove special characters from Vendor Name
        :param vendor_name: Vendor Name
        :return: Sanitized Vendor Name
        """
        sanitized_name = None
        if vendor_name:
            pattern = r'[!@#$%^&*()\-_=\+\[\]{}|\\:;"\'<>,.?/~`]'
            sanitized_name = re.sub(pattern, '', vendor_name)
            sanitized_name = re.sub(r'\s+', ' ', sanitized_name).strip()

        if sanitized_name:
            return sanitized_name[:19]  # 20 is the max length of the vendor name in Sage Intacct

        return None

    def get_exported_entry(self, resource_type: str, export_id: str) -> dict:
        """
        Retrieve a specific resource by internal ID.
        :param resource_type: The type of resource to fetch.
        :param export_id: The internal ID of the resource to fetch.
        :return: Parsed JSON representation of the resource data.
        """
        response = getattr(self, 'get_{}'.format(resource_type))(export_id)
        return json.loads(json.dumps(response, default=str))

    def get_accounting_fields(self, resource_type: str) -> dict:
        """
        Retrieve accounting fields for a specific resource type and internal ID.
        :param resource_type: The type of resource to fetch accounting fields for.
        :return: Parsed JSON representation of the accounting fields.
        """
        module = getattr(self.connection, resource_type)
        method = 'get_all' if resource_type == 'dimensions' else 'get_all_generator'

        generator = getattr(module, method)()

        response = [row for responses in generator for row in responses] if resource_type != 'dimensions' else generator

        return json.loads(json.dumps(response, default=str))

    def search_and_create_vendors(self, workspace_id: int, missing_vendors: list) -> None:
        """
        Seach vendors in Intacct and Upsert Vendors in DB
        :param workspace_id: Workspace ID
        :param missing_vendors: Missing Vendors List
        """
        missing_vendors_batches = [missing_vendors[i:i + 50] for i in range(0, len(missing_vendors), 50)]

        for missing_vendors_batch in missing_vendors_batches:
            vendors_list = [vendor.replace("'", "\\'") for vendor in missing_vendors_batch]

            and_filter = [('in', 'NAME', vendors_list), ('equalto', 'STATUS', 'active')]

            fields = ['NAME', 'VENDORID', 'DISPLAYCONTACT.EMAIL1', 'WHENMODIFIED']

            vendors = self.connection.vendors.get_by_query(and_filter=and_filter, fields=fields)

            # To Keep only most recently modified vendor for each name
            unique_vendors = {}

            for vendor in vendors:
                name_key = vendor.get('NAME', '')
                when_modified_str = vendor.get('WHENMODIFIED')
                when_modified = datetime.strptime(when_modified_str, "%m/%d/%Y %H:%M:%S")

                if name_key not in unique_vendors:
                    unique_vendors[name_key] = (vendor, when_modified)
                else:
                    _, existing_date = unique_vendors[name_key]
                    if when_modified > existing_date:
                        unique_vendors[name_key] = (vendor, when_modified)

            for vendor, _ in unique_vendors.values():
                logger.info("Upserting Vendor %s in Workspace %s", vendor['NAME'], workspace_id)
                self.create_destination_attribute(
                    'vendor',
                    vendor['NAME'],
                    vendor['VENDORID'],
                    vendor.get('DISPLAYCONTACT.EMAIL1')
                )
