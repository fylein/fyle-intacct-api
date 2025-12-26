import re
import json
import random
import text_unidecode

import logging
from typing import Optional
from datetime import datetime, timedelta, timezone

from django.db.models import Q
from django.conf import settings

from intacctsdk import IntacctRESTSDK
from sageintacctsdk import SageIntacctSDK
from intacctsdk.exceptions import BadRequestError

from fyle_accounting_library.common_resources.models import DimensionDetail
from fyle_accounting_library.common_resources.enums import DimensionDetailSourceTypeEnum
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, MappingSetting

from apps.workspaces.helpers import get_app_name
from apps.fyle.models import DependentFieldSetting
from apps.sage_intacct.enums import DestinationAttributeTypeEnum
from apps.sage_intacct.exports.bills import construct_bill_payload
from apps.mappings.models import GeneralMapping, LocationEntityMapping
from apps.sage_intacct.exports.ap_payments import construct_ap_payment_payload
from workers.helpers import RoutingKeyEnum, WorkerActionEnum, publish_to_rabbitmq
from apps.sage_intacct.exports.reimbursements import construct_reimbursement_payload
from apps.sage_intacct.exports.journal_entries import construct_journal_entry_payload
from apps.sage_intacct.exports.expense_reports import construct_expense_report_payload
from apps.sage_intacct.exports.charge_card_transactions import construct_charge_card_transaction_payload
from apps.sage_intacct.models import (
    Bill,
    CostCode,
    CostType,
    APPayment,
    JournalEntry,
    BillLineitem,
    ExpenseReport,
    APPaymentLineitem,
    JournalEntryLineitem,
    ChargeCardTransaction,
    ExpenseReportLineitem,
    SageIntacctReimbursement,
    SageIntacctAttributesCount,
    ChargeCardTransactionLineitem,
    SageIntacctReimbursementLineitem,
)
from apps.workspaces.models import (
    Workspace,
    Configuration,
    SageIntacctCredential,
    IntacctSyncedTimestamp
)

logger = logging.getLogger(__name__)
logger.level = logging.INFO


SYNC_UPPER_LIMIT = 30000
COST_TYPES_LIMIT = 500000

ATTRIBUTE_DISABLE_CALLBACK_PATH = {
    'PROJECT': 'fyle_integrations_imports.modules.projects.disable_projects',
    'VENDOR': 'fyle_integrations_imports.modules.merchants.disable_merchants',
    'ACCOUNT': 'fyle_integrations_imports.modules.categories.disable_categories',
    'EXPENSE_TYPE': 'fyle_integrations_imports.modules.categories.disable_categories',
    'COST_CENTER': 'fyle_integrations_imports.modules.cost_centers.disable_cost_centers'
}


class SageIntacctRestConnector:
    """
    Sage Intacct REST connector
    """
    def __init__(self, workspace_id: int):
        """
        Initialize the Sage Intacct REST connector
        :param workspace_id: Workspace ID
        """
        self.soap_sdk_connection = None
        self.workspace_id = workspace_id
        self.credential_object = self.__get_credential_object()
        self.username = self.__get_username()

        self.access_token = self.__get_access_token()
        self.location_entity_id = self.__get_location_entity_id()

        self.connection = IntacctRESTSDK(
            username=self.username,
            access_token=self.access_token,
            entity_id=self.location_entity_id,
            client_id=settings.INTACCT_CLIENT_ID,
            client_secret=settings.INTACCT_CLIENT_SECRET
        )

        if not self.access_token:
            self.__update_tokens(
                access_token=self.connection.access_token,
                access_token_expires_in=self.connection.access_token_expires_in if hasattr(self.connection, 'access_token_expires_in') and self.connection.access_token_expires_in else 21600
            )

    def __get_credential_object(self) -> Optional[SageIntacctCredential]:
        """
        Get credential object
        :return: Optional[SageIntacctCredential]
        """
        return SageIntacctCredential.objects.filter(workspace_id=self.workspace_id).first()

    def __get_access_token(self) -> Optional[str]:
        """
        Get access token
        :return: Optional[str]
        """
        if (
            self.credential_object
            and self.credential_object.access_token
            and self.credential_object.access_token_expires_at > datetime.now(timezone.utc)
        ):
            return self.credential_object.access_token

        return None

    def __get_username(self) -> Optional[str]:
        """
        Get username
        :return: Optional[str]
        """
        if self.credential_object and self.credential_object.si_company_id and self.credential_object.si_user_id:
            return f'{self.credential_object.si_user_id}@{self.credential_object.si_company_id}'

        return None

    def __get_location_entity_id(self) -> Optional[str]:
        """
        Get location entity id
        :return: Optional[str]
        """
        location_entity_mapping = LocationEntityMapping.objects.filter(
            ~Q(destination_id='top_level'), workspace_id=self.workspace_id
        ).first()
        return location_entity_mapping.destination_id if location_entity_mapping else None

    def __update_tokens(
        self,
        access_token: str,
        access_token_expires_in: int
    ) -> None:
        """
        Update tokens
        :param access_token: Access token
        :param access_token_expires_in: Access token expires in
        :return: None
        """
        self.credential_object.refresh_from_db()
        self.credential_object.access_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=self.__get_access_token_expiry_time(access_token_expires_in))
        self.credential_object.access_token = access_token
        self.credential_object.is_expired = False
        self.credential_object.save(update_fields=[
            'access_token_expires_at',
            'access_token',
            'is_expired',
            'updated_at'
        ])

    def __get_access_token_expiry_time(self, access_token_expires_in: int) -> int:
        """
        Get access token expiry time
        :param access_token_expires_in: Access token expires in
        :return: int
        """
        hours_remaining = access_token_expires_in / 3600

        # If more than 5 hours remain, set to 5 hours
        if hours_remaining >= 5:
            hours_remaining = 5

        return int(hours_remaining)

    def get_session_id(self) -> str:
        """
        Get Session Id
        """
        return self.connection.sessions.get_session_id()['sessionId']

    def get_soap_connection(self) -> 'SageIntacctSDK':
        """
        Get Soap Connection
        """
        self.soap_sdk_connection = SageIntacctSDK(
            sender_id=settings.SI_SENDER_ID,
            sender_password=settings.SI_SENDER_PASSWORD,
            user_id='dummy',
            company_id=self.credential_object.si_company_id,
            user_password='dummy',
            entity_id=self.location_entity_id,
            session_id=self.get_session_id()
        )

        return self.soap_sdk_connection


class SageIntacctDimensionSyncManager(SageIntacctRestConnector):
    """
    Sage Intacct Dimension Sync Manager
    """
    def __init__(self, workspace_id: int):
        """
        Initialize the Sage Intacct Rest Dimension Sync Manager
        :param: workspace_id: Workspace ID
        """
        super().__init__(workspace_id)
        self.intacct_synced_timestamp_object = self.__get_intacct_synced_timestamp_object()
        self.count_filter = [{
            '$eq': {
                'status': 'active'
            }
        }]

    def __get_intacct_synced_timestamp_object(self) -> 'IntacctSyncedTimestamp':
        """
        Get Intacct synced timestamp object
        :return: IntacctSyncedTimestamp
        """
        return IntacctSyncedTimestamp.get_latest_synced_timestamp(workspace_id=self.workspace_id)

    def __update_intacct_synced_timestamp_object(self, key: str) -> None:
        """
        Update Intacct synced timestamp object
        :param: key: field to update
        :return: None
        """
        IntacctSyncedTimestamp.update_latest_synced_timestamp(workspace_id=self.workspace_id, key=key)

    def __is_sync_allowed(self, attribute_type: str, attribute_count: int) -> bool:
        """
        Checks if the sync is allowed
        :param attribute_count: Number of attributes to sync
        :param attribute_type: Type of attribute (e.g., 'cost_types'). Optional, used for exceptions.
        :return: True if sync allowed, False otherwise
        """
        limit = COST_TYPES_LIMIT if attribute_type == DestinationAttributeTypeEnum.COST_TYPE.value else SYNC_UPPER_LIMIT

        if attribute_count > limit:
            workspace = Workspace.objects.get(id=self.workspace_id)
            if workspace.created_at > timezone.make_aware(datetime(2024, 10, 1), timezone.get_current_timezone()):
                return False
            else:
                return True

        return True

    def __get_all_generator_params(
        self,
        fields: list,
        latest_synced_timestamp: datetime = None,
        extra_filter_params: list[dict] = [],
        active_status_only: bool = True,
    ) -> dict:
        """
        Get all generator params
        :param fields: Fields
        :param latest_synced_timestamp: Latest synced timestamp
        :param active_status_only: Active status only
        :return: Params
        """
        params = {'fields': fields}
        filters = []

        if latest_synced_timestamp:
            filters.append({
                '$gte': {
                    'audit.modifiedDateTime': latest_synced_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
                }
            })

        if not latest_synced_timestamp and active_status_only:
            filters.append({
                '$eq': {
                    'status': 'active'
                }
            })

        filters.extend(extra_filter_params)
        params['filters'] = filters

        return params

    def __is_duplicate_deletion_skipped(self, attribute_type: str) -> bool:
        """
        Check if duplicate deletion is skipped for the attribute type
        :param attribute_type: Type of the attribute
        :return: Whether deletion is skipped
        """
        if attribute_type in [
            DestinationAttributeTypeEnum.ITEM.value,
            DestinationAttributeTypeEnum.CLASS.value,
            DestinationAttributeTypeEnum.VENDOR.value,
            DestinationAttributeTypeEnum.PROJECT.value,
            DestinationAttributeTypeEnum.ACCOUNT.value,
            DestinationAttributeTypeEnum.LOCATION.value,
            DestinationAttributeTypeEnum.CUSTOMER.value,
            DestinationAttributeTypeEnum.DEPARTMENT.value,
            DestinationAttributeTypeEnum.EXPENSE_TYPE.value,
        ]:
            return False

        return True

    def __is_import_enabled(self, attribute_type: str) -> bool:
        """
        Check if import is enabled for the attribute type
        :param attribute_type: Type of the attribute
        :return: Whether import is enabled
        """
        is_import_to_fyle_enabled = False

        configuration = Configuration.objects.filter(workspace_id=self.workspace_id).first()
        if not configuration:
            return is_import_to_fyle_enabled

        if attribute_type in [
            DestinationAttributeTypeEnum.ACCOUNT.value,
            DestinationAttributeTypeEnum.EXPENSE_TYPE.value
        ] and configuration.import_categories:
            is_import_to_fyle_enabled = True

        elif attribute_type == DestinationAttributeTypeEnum.VENDOR.value and configuration.import_vendors_as_merchants:
            is_import_to_fyle_enabled = True

        elif attribute_type in [
            DestinationAttributeTypeEnum.ITEM.value,
            DestinationAttributeTypeEnum.CLASS.value,
            DestinationAttributeTypeEnum.PROJECT.value,
            DestinationAttributeTypeEnum.CUSTOMER.value,
            DestinationAttributeTypeEnum.LOCATION.value,
            DestinationAttributeTypeEnum.DEPARTMENT.value,
        ]:
            mapping_setting = MappingSetting.objects.filter(workspace_id=self.workspace_id, destination_field=attribute_type).first()

            if mapping_setting and mapping_setting.import_to_fyle:
                is_import_to_fyle_enabled = True

        return is_import_to_fyle_enabled

    def __get_attribute_disable_callback_path(self, attribute_type: str) -> Optional[str]:
        """
        Get the attribute disable callback path
        :param attribute_type: Type of the attribute
        :return: attribute disable callback path or none
        """
        if attribute_type in [
            DestinationAttributeTypeEnum.ACCOUNT.value,
            DestinationAttributeTypeEnum.VENDOR.value,
            DestinationAttributeTypeEnum.EXPENSE_TYPE.value
        ]:
            return ATTRIBUTE_DISABLE_CALLBACK_PATH.get(attribute_type)

        mapping_setting = MappingSetting.objects.filter(
            workspace_id=self.workspace_id,
            destination_field=attribute_type
        ).first()

        if mapping_setting and not mapping_setting.is_custom:
            return ATTRIBUTE_DISABLE_CALLBACK_PATH.get(mapping_setting.source_field)

    def __update_attribute_count(self, attribute_type: str, count: int) -> None:
        """
        Update attribute count
        :param attribute_type: Type of attribute (e.g., 'accounts', 'vendors')
        :param count: Count value from Sage Intacct
        :return: None
        """
        ATTRIBUTE_TYPE_MAP = {
            DestinationAttributeTypeEnum.ITEM.value: 'items',
            DestinationAttributeTypeEnum.CLASS.value: 'classes',
            DestinationAttributeTypeEnum.VENDOR.value: 'vendors',
            DestinationAttributeTypeEnum.PROJECT.value: 'projects',
            DestinationAttributeTypeEnum.ACCOUNT.value: 'accounts',
            DestinationAttributeTypeEnum.LOCATION.value: 'locations',
            DestinationAttributeTypeEnum.EMPLOYEE.value: 'employees',
            DestinationAttributeTypeEnum.CUSTOMER.value: 'customers',
            DestinationAttributeTypeEnum.COST_TYPE.value: 'cost_types',
            DestinationAttributeTypeEnum.COST_CODE.value: 'cost_codes',
            DestinationAttributeTypeEnum.TAX_DETAIL.value: 'tax_details',
            DestinationAttributeTypeEnum.ALLOCATION.value: 'allocations',
            DestinationAttributeTypeEnum.DEPARTMENT.value: 'departments',
            DestinationAttributeTypeEnum.EXPENSE_TYPE.value: 'expense_types',
            DestinationAttributeTypeEnum.PAYMENT_ACCOUNT.value: 'payment_accounts',
            DestinationAttributeTypeEnum.CHARGE_CARD_NUMBER.value: 'charge_card_accounts',
            DestinationAttributeTypeEnum.EXPENSE_PAYMENT_TYPE.value: 'expense_payment_types'
        }

        attribute_type_map = ATTRIBUTE_TYPE_MAP.get(attribute_type)
        if attribute_type_map:
            SageIntacctAttributesCount.update_attribute_count(
                workspace_id=self.workspace_id,
                attribute_type=attribute_type_map,
                count=count
            )
        else:
            logger.warning('Attribute type %s not found in the attribute type map', attribute_type)

    def __update_user_defined_dimensions_count(self, user_defined_dimensions_count: dict) -> None:
        """
        Update user defined dimensions count
        :param user_defined_dimensions_count: User defined dimensions count
        :return: None
        """
        SageIntacctAttributesCount.objects.filter(
            workspace_id=self.workspace_id
        ).update(
            user_defined_dimensions_details=user_defined_dimensions_count,
            updated_at=datetime.now(timezone.utc)
        )

    def sync_accounts(self) -> None:
        """
        Sync accounts
        """
        attribute_count = self.connection.accounts.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.ACCOUNT.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.ACCOUNT.value, attribute_count=attribute_count):
            logger.info('Skipping sync of accounts for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'name', 'accountType', 'status']
        latest_synced_timestamp = self.intacct_synced_timestamp_object.account_synced_at
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        account_generator = self.connection.accounts.get_all_generator(**params)

        account_attributes = {
            'account': [],
            'ccc_account': []
        }

        for accounts in account_generator:
            for account in accounts:
                account_attributes['account'].append({
                    'attribute_type': DestinationAttributeTypeEnum.ACCOUNT.value,
                    'display_name': 'Account',
                    'value': text_unidecode.unidecode(u'{0}'.format(account['name'].replace('/', '-'))),
                    'destination_id': account['id'],
                    'active': account['status'] == 'active',
                    'detail': {
                        'account_type': account['accountType'].lower() if account['accountType'] else None
                    },
                    'code': account['id']
                })

        for attribute_type, account_attribute in account_attributes.items():
            if account_attribute:
                DestinationAttribute.bulk_create_or_update_destination_attributes(
                    account_attribute,
                    attribute_type.upper(),
                    self.workspace_id,
                    True,
                    app_name=get_app_name(),
                    attribute_disable_callback_path=self.__get_attribute_disable_callback_path(DestinationAttributeTypeEnum.ACCOUNT.value),
                    is_import_to_fyle_enabled=self.__is_import_enabled(DestinationAttributeTypeEnum.ACCOUNT.value),
                    skip_deletion=self.__is_duplicate_deletion_skipped(DestinationAttributeTypeEnum.ACCOUNT.value)
                )

        self.__update_intacct_synced_timestamp_object(key='account_synced_at')

    def sync_departments(self) -> None:
        """
        Sync departments
        """
        attribute_count = self.connection.departments.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.DEPARTMENT.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.DEPARTMENT.value, attribute_count=attribute_count):
            logger.info('Skipping sync of department for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'name', 'status']
        latest_synced_timestamp = self.intacct_synced_timestamp_object.department_synced_at
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        department_generator = self.connection.departments.get_all_generator(**params)

        department_attributes = []

        for departments in department_generator:
            for department in departments:
                department_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.DEPARTMENT.value,
                    'display_name': 'department',
                    'value': department['name'],
                    'destination_id': department['id'],
                    'active': department['status'] == 'active',
                    'code': department['id']
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            department_attributes,
            DestinationAttributeTypeEnum.DEPARTMENT.value,
            self.workspace_id,
            True,
            app_name=get_app_name(),
            attribute_disable_callback_path=self.__get_attribute_disable_callback_path(DestinationAttributeTypeEnum.DEPARTMENT.value),
            is_import_to_fyle_enabled=self.__is_import_enabled(DestinationAttributeTypeEnum.DEPARTMENT.value),
            skip_deletion=self.__is_duplicate_deletion_skipped(DestinationAttributeTypeEnum.DEPARTMENT.value)
        )

        self.__update_intacct_synced_timestamp_object(key='department_synced_at')

    def sync_expense_types(self) -> None:
        """
        Sync expense types
        """
        attribute_count = self.connection.expense_types.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.EXPENSE_TYPE.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.EXPENSE_TYPE.value, attribute_count=attribute_count):
            logger.info('Skipping sync of expense_type for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'description', 'glAccount.id', 'glAccount.name', 'status']
        latest_synced_timestamp = self.intacct_synced_timestamp_object.expense_type_synced_at
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        is_expense_type_import_enabled = self.__is_import_enabled(DestinationAttributeTypeEnum.EXPENSE_TYPE.value)
        expense_type_generator = self.connection.expense_types.get_all_generator(**params)

        expense_types_attributes = []

        for expense_types in expense_type_generator:
            for expense_type in expense_types:
                expense_types_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.EXPENSE_TYPE.value,
                    'display_name': 'Expense Types',
                    'value': text_unidecode.unidecode(u'{0}'.format(expense_type['description'].replace('/', '-'))),
                    'destination_id': expense_type['id'],
                    'active': expense_type['status'] == 'active',
                    'detail': {
                        'gl_account_no': expense_type['glAccount.id'],
                        'gl_account_title': expense_type['glAccount.name']
                    },
                    'code': expense_type['id']
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            expense_types_attributes,
            DestinationAttributeTypeEnum.EXPENSE_TYPE.value,
            self.workspace_id,
            True,
            app_name=get_app_name(),
            attribute_disable_callback_path=self.__get_attribute_disable_callback_path(DestinationAttributeTypeEnum.EXPENSE_TYPE.value),
            is_import_to_fyle_enabled=is_expense_type_import_enabled,
            skip_deletion=self.__is_duplicate_deletion_skipped(DestinationAttributeTypeEnum.EXPENSE_TYPE.value)
        )

        self.__update_intacct_synced_timestamp_object(key='expense_type_synced_at')

        if not is_expense_type_import_enabled:
            payload = {
                'workspace_id': self.workspace_id,
                'action': WorkerActionEnum.CHECK_AND_CREATE_CCC_MAPPINGS.value,
                'data': {
                    'workspace_id': self.workspace_id
                }
            }
            publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)

    def sync_charge_card_accounts(self) -> None:
        """
        Sync charge card accounts
        """
        attribute_count = self.connection.charge_card_accounts.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.CHARGE_CARD_NUMBER.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.CHARGE_CARD_NUMBER.value, attribute_count=attribute_count):
            logger.info('Skipping sync of charge card number for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'status']
        extra_filter_params = [{
            '$eq': {
                'accountDetails.accountType': 'credit'
            }
        }]

        params = self.__get_all_generator_params(fields=fields, extra_filter_params=extra_filter_params)
        charge_card_number_generator = self.connection.charge_card_accounts.get_all_generator(**params)
        charge_card_number_attributes = []

        for charge_card_numbers in charge_card_number_generator:
            for charge_card_number in charge_card_numbers:
                charge_card_number_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.CHARGE_CARD_NUMBER.value,
                    'display_name': 'Charge Card Account',
                    'value': charge_card_number['id'],
                    'destination_id': charge_card_number['id'],
                    'active': True
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            charge_card_number_attributes,
            DestinationAttributeTypeEnum.CHARGE_CARD_NUMBER.value,
            self.workspace_id,
            True
        )

    def sync_payment_accounts(self) -> None:
        """
        Sync payment accounts
        """
        attribute_count = self.connection.checking_accounts.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.PAYMENT_ACCOUNT.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.PAYMENT_ACCOUNT.value, attribute_count=attribute_count):
            logger.info('Skipping sync of payment accounts for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'bankAccountDetails.bankName', 'status']
        latest_synced_timestamp = self.intacct_synced_timestamp_object.payment_account_synced_at
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        payment_account_generator = self.connection.checking_accounts.get_all_generator(**params)

        payment_accounts_attributes = []

        for payment_accounts in payment_account_generator:
            for payment_account in payment_accounts:
                payment_accounts_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.PAYMENT_ACCOUNT.value,
                    'display_name': 'Payment Account',
                    'value': '{} - {}'.format(payment_account['bankAccountDetails.bankName'], payment_account['id']),
                    'destination_id': payment_account['id'],
                    'active': payment_account['status'] == 'active'
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            payment_accounts_attributes,
            DestinationAttributeTypeEnum.PAYMENT_ACCOUNT.value,
            self.workspace_id,
            True
        )

        self.__update_intacct_synced_timestamp_object(key='payment_account_synced_at')

    def sync_cost_types(self) -> None:
        """
        Sync Cost Types
        """
        attribute_count = self.connection.cost_types.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.COST_TYPE.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.COST_TYPE.value, attribute_count=attribute_count):
            logger.info('Skipping sync of cost_types for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = [
            'id',
            'key',
            'name',
            'status',
            'project.id',
            'project.name',
            'project.key',
            'task.id',
            'task.name',
            'task.key',
            'audit.createdDateTime',
            'audit.modifiedDateTime'
        ]
        latest_synced_timestamp = None
        dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=self.workspace_id).first()

        if dependent_field_setting and dependent_field_setting.last_synced_at:
            latest_synced_timestamp = dependent_field_setting.last_synced_at - timedelta(days=1)

        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        cost_types_generator = self.connection.cost_types.get_all_generator(**params)

        for cost_types in cost_types_generator:
            CostType.bulk_create_or_update_rest(cost_types, self.workspace_id)

        dependent_field_setting.last_synced_at = datetime.now()
        dependent_field_setting.save()

    def sync_cost_codes(self) -> None:
        """
        Sync Cost Codes
        """
        attribute_count = self.connection.tasks.count()

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.COST_CODE.value, count=attribute_count)

        logger.info("Cost Code count for workspace %s: %s", self.workspace_id, attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.COST_CODE.value, attribute_count=attribute_count):
            logger.info('Skipping sync of tasks for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['key', 'name', 'project.key', 'project.name']
        latest_synced_timestamp = None

        dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=self.workspace_id).first()

        if dependent_field_setting and dependent_field_setting.last_synced_at:
            latest_synced_timestamp = dependent_field_setting.last_synced_at - timedelta(days=1)

        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp, active_status_only=False)
        tasks_generator = self.connection.tasks.get_all_generator(**params)

        for tasks in tasks_generator:
            CostCode.bulk_create_or_update_rest(tasks, self.workspace_id)

        dependent_field_setting.last_synced_at = datetime.now()
        dependent_field_setting.save()

    def sync_projects(self) -> None:
        """
        Sync projects
        """
        attribute_count = self.connection.projects.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.PROJECT.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.PROJECT.value, attribute_count=attribute_count):
            logger.info('Skipping sync of projects for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'name', 'status', 'customer.id', 'customer.name', 'isBillableEmployeeExpense', 'isBillablePurchasingAPExpense']
        latest_synced_timestamp = self.intacct_synced_timestamp_object.customer_synced_at
        is_project_import_enabled = self.__is_import_enabled(DestinationAttributeTypeEnum.PROJECT.value)
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        project_generator = self.connection.projects.get_all_generator(**params)

        project_attributes = []

        for projects in project_generator:
            for project in projects:
                detail = {
                    'customer_id': project['customer.id'],
                    'customer_name': project['customer.name'],
                    'default_expense_report_billable': project['isBillableEmployeeExpense'],
                    'default_bill_billable': project['isBillablePurchasingAPExpense']
                }

                project_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.PROJECT.value,
                    'display_name': 'project',
                    'value': project['name'],
                    'destination_id': project['id'],
                    'active': project['status'] == 'active',
                    'detail': detail,
                    'code': project['id']
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                project_attributes,
                DestinationAttributeTypeEnum.PROJECT.value,
                self.workspace_id,
                True,
                app_name=get_app_name(),
                attribute_disable_callback_path=self.__get_attribute_disable_callback_path(DestinationAttributeTypeEnum.PROJECT.value),
                is_import_to_fyle_enabled=is_project_import_enabled,
                skip_deletion=self.__is_duplicate_deletion_skipped(DestinationAttributeTypeEnum.PROJECT.value)
            )

        self.__update_intacct_synced_timestamp_object(key='project_synced_at')

    def sync_items(self) -> None:
        """
        Sync items
        """
        attribute_count = self.connection.items.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.ITEM.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.ITEM.value, attribute_count=attribute_count):
            logger.info('Skipping sync of items for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'name', 'status', 'itemType']
        latest_synced_timestamp = self.intacct_synced_timestamp_object.item_synced_at
        extra_filter_params = [{
            '$eq': {
                'itemType': 'nonInventory'
            }
        }]
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp, extra_filter_params=extra_filter_params)
        item_generator = self.connection.items.get_all_generator(**params)

        item_attributes = []

        for items in item_generator:
            for item in items:
                item_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.ITEM.value,
                    'display_name': 'item',
                    'value': item['name'],
                    'destination_id': item['id'],
                    'active': item['status'] == 'active'
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                item_attributes,
                DestinationAttributeTypeEnum.ITEM.value,
                self.workspace_id,
                True,
                app_name=get_app_name(),
                attribute_disable_callback_path=self.__get_attribute_disable_callback_path(DestinationAttributeTypeEnum.ITEM.value),
                skip_deletion=self.__is_duplicate_deletion_skipped(DestinationAttributeTypeEnum.ITEM.value),
                is_import_to_fyle_enabled=self.__is_import_enabled(DestinationAttributeTypeEnum.ITEM.value)
            )

        self.__update_intacct_synced_timestamp_object(key='item_synced_at')

    def sync_locations(self) -> None:
        """
        Sync locations
        """
        attribute_count = self.connection.locations.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.LOCATION.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.LOCATION.value, attribute_count=attribute_count):
            logger.info('Skipping sync of locations for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'name', 'status']
        latest_synced_timestamp = self.intacct_synced_timestamp_object.location_synced_at
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        location_generator = self.connection.locations.get_all_generator(**params)

        location_attributes = []

        for locations in location_generator:
            for location in locations:
                location_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.LOCATION.value,
                    'display_name': 'location',
                    'value': location['name'],
                    'destination_id': location['id'],
                    'active': location['status'] == 'active'
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            location_attributes,
            DestinationAttributeTypeEnum.LOCATION.value,
            self.workspace_id,
            True,
            app_name=get_app_name(),
            attribute_disable_callback_path=self.__get_attribute_disable_callback_path(DestinationAttributeTypeEnum.LOCATION.value),
            skip_deletion=self.__is_duplicate_deletion_skipped(DestinationAttributeTypeEnum.LOCATION.value),
            is_import_to_fyle_enabled=self.__is_import_enabled(DestinationAttributeTypeEnum.LOCATION.value)
        )

        self.__update_intacct_synced_timestamp_object(key='location_synced_at')

    def sync_expense_payment_types(self) -> None:
        """
        Sync Expense Payment Types
        """
        attribute_count = self.connection.expense_payment_types.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.EXPENSE_PAYMENT_TYPE.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.EXPENSE_PAYMENT_TYPE.value, attribute_count=attribute_count):
            logger.info('Skipping sync of expense payment types for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['key', 'id', 'isNonReimbursable']
        latest_synced_timestamp = self.intacct_synced_timestamp_object.expense_payment_type_synced_at
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        expense_payment_type_generator = self.connection.expense_payment_types.get_all_generator(**params)

        expense_payment_type_attributes = []

        for expense_payment_types in expense_payment_type_generator:
            for expense_payment_type in expense_payment_types:
                expense_payment_type_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.EXPENSE_PAYMENT_TYPE.value,
                    'display_name': 'expense payment type',
                    'value': expense_payment_type['id'],
                    'destination_id': expense_payment_type['key'],
                    'detail': {
                        'is_reimbursable': not bool(expense_payment_type['isNonReimbursable'])
                    },
                    'active': True
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            expense_payment_type_attributes,
            DestinationAttributeTypeEnum.EXPENSE_PAYMENT_TYPE.value,
            self.workspace_id,
            True
        )

        self.__update_intacct_synced_timestamp_object(key='expense_payment_type_synced_at')

    def sync_employees(self) -> None:
        """
        Sync employees
        """
        attribute_count = self.connection.employees.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.EMPLOYEE.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.EMPLOYEE.value, attribute_count=attribute_count):
            logger.info('Skipping sync of employees for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'name', 'status', 'primaryContact.email1', 'primaryContact.printAs',  'department.id', 'location.id']
        latest_synced_timestamp = self.intacct_synced_timestamp_object.employee_synced_at
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        employee_generator = self.connection.employees.get_all_generator(**params)

        employee_attributes = []

        for employees in employee_generator:
            for employee in employees:
                detail = {
                    'email': employee['primaryContact.email1'] if employee['primaryContact.email1'] else None,
                    'full_name': employee['primaryContact.printAs'] if employee['primaryContact.printAs'] else None,
                    'location_id': employee['location.id'] if employee['location.id'] else None,
                    'department_id': employee['department.id'] if employee['department.id'] else None
                }

                employee_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.EMPLOYEE.value,
                    'display_name': 'employee',
                    'value': employee['name'],
                    'destination_id': employee['id'],
                    'detail': detail,
                    'active': True
                })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            employee_attributes,
            DestinationAttributeTypeEnum.EMPLOYEE.value,
            self.workspace_id,
            True
        )

        self.__update_intacct_synced_timestamp_object(key='employee_synced_at')

    def sync_classes(self) -> None:
        """
        Sync classes
        """
        attribute_count = self.connection.classes.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.CLASS.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.CLASS.value, attribute_count=attribute_count):
            logger.info('Skipping sync of classes for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'name', 'status']

        latest_synced_timestamp = self.intacct_synced_timestamp_object.class_synced_at
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        class_generator = self.connection.classes.get_all_generator(**params)
        class_attributes = []

        for _classes in class_generator:
            for _class in _classes:
                class_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.CLASS.value,
                    'display_name': 'class',
                    'value': _class['name'],
                    'destination_id': _class['id'],
                    'active': _class['status'] == 'active'
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                class_attributes,
                DestinationAttributeTypeEnum.CLASS.value,
                self.workspace_id,
                True,
                app_name=get_app_name(),
                attribute_disable_callback_path=self.__get_attribute_disable_callback_path(DestinationAttributeTypeEnum.CLASS.value),
                skip_deletion=self.__is_duplicate_deletion_skipped(DestinationAttributeTypeEnum.CLASS.value),
                is_import_to_fyle_enabled=self.__is_import_enabled(DestinationAttributeTypeEnum.CLASS.value)
            )

        self.__update_intacct_synced_timestamp_object(key='class_synced_at')

    def sync_customers(self) -> None:
        """
        Sync Customers
        """
        attribute_count = self.connection.customers.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.CUSTOMER.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.CUSTOMER.value, attribute_count=attribute_count):
            logger.info('Skipping sync of customers for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'name', 'status']

        latest_synced_timestamp = self.intacct_synced_timestamp_object.customer_synced_at
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        customer_generator = self.connection.customers.get_all_generator(**params)

        customer_attributes = []

        for customers in customer_generator:
            for customer in customers:
                customer_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.CUSTOMER.value,
                    'display_name': 'customer',
                    'value': customer['name'],
                    'destination_id': customer['id'],
                    'active': customer['status'] == 'active'
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                customer_attributes,
                DestinationAttributeTypeEnum.CUSTOMER.value,
                self.workspace_id,
                True,
                app_name=get_app_name(),
                attribute_disable_callback_path=self.__get_attribute_disable_callback_path(DestinationAttributeTypeEnum.CUSTOMER.value),
                skip_deletion=self.__is_duplicate_deletion_skipped(DestinationAttributeTypeEnum.CUSTOMER.value),
                is_import_to_fyle_enabled=self.__is_import_enabled(DestinationAttributeTypeEnum.CUSTOMER.value)
            )

        self.__update_intacct_synced_timestamp_object(key='customer_synced_at')

    def sync_tax_details(self) -> None:
        """
        Sync Tax Details
        """
        attribute_count = self.connection.tax_details.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.TAX_DETAIL.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.TAX_DETAIL.value, attribute_count=attribute_count):
            logger.info('Skipping sync of tax_details for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        attributes = []
        fields = ['taxPercent', 'id', 'taxSolution.id', 'status', 'taxType']
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=None)
        tax_details_generator = self.connection.tax_details.get_all_generator(**params)

        for tax_details in tax_details_generator:
            for tax_detail in tax_details:
                if float(tax_detail['taxPercent']) >= 0 and tax_detail['taxType'] == 'purchase':
                    attributes.append({
                        'attribute_type': DestinationAttributeTypeEnum.TAX_DETAIL.value,
                        'display_name': 'Tax Detail',
                        'value': tax_detail['id'],
                        'destination_id': tax_detail['id'],
                        'active': True,
                        'detail': {
                            'tax_rate': float(tax_detail['taxPercent']),
                            'tax_solution_id': tax_detail['taxSolution.id']
                        }
                    })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            attributes,
            DestinationAttributeTypeEnum.TAX_DETAIL.value,
            self.workspace_id,
            True
        )

        self.__update_intacct_synced_timestamp_object(key='tax_detail_synced_at')

    def sync_vendors(self) -> None:
        """
        Sync vendors
        """
        attribute_count = self.connection.vendors.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.VENDOR.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.VENDOR.value, attribute_count=attribute_count):
            logger.info('Skipping sync of vendors for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        fields = ['id', 'name', 'status', 'contacts.default.email1']
        latest_synced_timestamp = self.intacct_synced_timestamp_object.vendor_synced_at
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        vendor_generator = self.connection.vendors.get_all_generator(**params)
        vendor_attributes = []

        for vendors in vendor_generator:
            for vendor in vendors:
                detail = {
                    'email': vendor['contacts.default.email1'] if vendor['contacts.default.email1'] else None
                }
                vendor_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.VENDOR.value,
                    'display_name': 'vendor',
                    'value': vendor['name'],
                    'destination_id': vendor['id'],
                    'detail': detail,
                    'active': vendor['status'] == 'active'
                })

        if vendor_attributes:
            DestinationAttribute.bulk_create_or_update_destination_attributes(
                vendor_attributes,
                DestinationAttributeTypeEnum.VENDOR.value,
                self.workspace_id,
                True,
                app_name=get_app_name(),
                attribute_disable_callback_path=self.__get_attribute_disable_callback_path(DestinationAttributeTypeEnum.VENDOR.value),
                skip_deletion=self.__is_duplicate_deletion_skipped(DestinationAttributeTypeEnum.VENDOR.value),
                is_import_to_fyle_enabled=self.__is_import_enabled(DestinationAttributeTypeEnum.VENDOR.value)
            )

        self.__update_intacct_synced_timestamp_object(key='vendor_synced_at')

    def sync_user_defined_dimensions(self) -> None:
        """
        Sync User Defined Dimensions
        """
        dimensions = self.connection.dimensions.list()
        dimension_details = []
        user_defined_dimensions_count = {}

        for dimension in dimensions:
            dimension_details.append({
                'attribute_type': dimension['dimensionName'],
                'display_name': dimension['termName'],
                'source_type': DimensionDetailSourceTypeEnum.ACCOUNTING.value,
                'workspace_id': self.workspace_id
            })

            if dimension['isUserDefinedDimension']:
                try:
                    dimension_attributes = []
                    dimension_name = dimension['dimensionName'].upper().replace(' ', '_')
                    dimension_field_name = dimension['dimensionEndpoint'].split('::')[1]
                    dimension_count = self.connection.dimensions.count(dimension_name=dimension_field_name)

                    user_defined_dimensions_count[dimension_name] = dimension_count

                    is_sync_allowed = self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.USER_DEFINED_DIMENSION.value, attribute_count=dimension_count)

                    if not is_sync_allowed:
                        logger.info('Skipping sync of UDD %s for workspace %s as it has %s counts which is over the limit', dimension_name, self.workspace_id, dimension_count)
                        continue

                    fields = ['id', 'name']
                    dimension_value_generator = self.connection.dimensions.get_all_generator(fields=fields, dimension_name=dimension_field_name)

                    for dimension_values in dimension_value_generator:
                        for value in dimension_values:
                            dimension_attributes.append({
                                'attribute_type': dimension_name,
                                'display_name': dimension['termName'],
                                'value': value['name'],
                                'destination_id': value['id'],
                                'active': True,
                                'detail': {'dimension_name': dimension_field_name}
                            })

                        DestinationAttribute.bulk_create_or_update_destination_attributes(
                            dimension_attributes,
                            dimension_name,
                            self.workspace_id
                        )
                except Exception as e:
                    logger.error("Error while syncing user defined dimension %s for workspace %s: %s", dimension_name, self.workspace_id, e)

        self.__update_user_defined_dimensions_count(user_defined_dimensions_count=user_defined_dimensions_count)
        DimensionDetail.bulk_create_or_update_dimension_details(
            dimensions=dimension_details,
            workspace_id=self.workspace_id,
            source_type=DimensionDetailSourceTypeEnum.ACCOUNTING.value
        )

    def sync_allocations(self) -> None:
        """
        Sync allocation entries
        """
        attribute_count = self.connection.allocations.count(filters=self.count_filter)

        self.__update_attribute_count(attribute_type=DestinationAttributeTypeEnum.ALLOCATION.value, count=attribute_count)

        if not self.__is_sync_allowed(attribute_type=DestinationAttributeTypeEnum.ALLOCATION.value, attribute_count=attribute_count):
            logger.info('Skipping sync of allocations for workspace %s as it has %s counts which is over the limit', self.workspace_id, attribute_count)
            return

        allocation_attributes = []
        is_allocation_present = False
        latest_synced_timestamp = self.intacct_synced_timestamp_object.allocation_synced_at

        fields = ['id', 'status', 'key']
        params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
        allocations_generator = self.connection.allocations.get_all_generator(**params)

        for allocations in allocations_generator:
            for allocation in allocations:
                allocation_entry = self.connection.allocations.get_by_key(key=allocation['key'])['ia::result']
                if not allocation_entry:
                    continue

                detail = {}
                value = allocation_entry['id']
                status = allocation['status']
                destination_id = allocation_entry['key']
                for lines in allocation_entry['lines']:
                    for dimension in lines['dimensions'].keys():
                        if lines['dimensions'][dimension]['key'] is not None and dimension not in detail:
                            detail[dimension] = True

                allocation_attributes.append({
                    'attribute_type': DestinationAttributeTypeEnum.ALLOCATION.value,
                    'display_name': 'allocation',
                    'value': value,
                    'destination_id': destination_id,
                    'active': status == 'active',
                    'detail': detail
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                allocation_attributes,
                DestinationAttributeTypeEnum.ALLOCATION.value,
                self.workspace_id,
                update=True
            )

            is_allocation_present = True

        self.__update_intacct_synced_timestamp_object(key='allocation_synced_at')

        if is_allocation_present:
            dimension_details = [{
                'attribute_type': DestinationAttributeTypeEnum.ALLOCATION.value,
                'display_name': DestinationAttributeTypeEnum.ALLOCATION.value.title(),
                'source_type': DimensionDetailSourceTypeEnum.ACCOUNTING.value,
                'workspace_id': self.workspace_id
            }]

            DimensionDetail.bulk_create_or_update_dimension_details(
                dimensions=dimension_details,
                workspace_id=self.workspace_id,
                source_type=DimensionDetailSourceTypeEnum.ACCOUNTING.value
            )

    def __get_entity_slide_preference(self) -> bool:
        """
        Get Entity Slide preference
        """
        entity_slide_disabled = False

        sdk_soap_connection = self.get_soap_connection()

        try:
            company_prefs = sdk_soap_connection.api_base.format_and_send_request({
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

    def sync_location_entities(self) -> None:
        """
        Sync location entities
        """
        if not self.__get_entity_slide_preference():
            fields = ['id', 'name', 'operatingCountry']

            latest_synced_timestamp = self.intacct_synced_timestamp_object.location_entity_synced_at
            params = self.__get_all_generator_params(fields=fields, latest_synced_timestamp=latest_synced_timestamp)
            location_entity_generator = self.connection.location_entities.get_all_generator(**params)

            location_entities_attributes = []

            for location_entities in location_entity_generator:
                for location_entity in location_entities:
                    location_entities_attributes.append({
                        'attribute_type': DestinationAttributeTypeEnum.LOCATION_ENTITY.value,
                        'display_name': 'location entity',
                        'value': location_entity['name'],
                        'destination_id': location_entity['id'],
                        'detail': {
                            'country': location_entity['operatingCountry']
                        },
                        'active': True
                    })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                location_entities_attributes,
                DestinationAttributeTypeEnum.LOCATION_ENTITY.value,
                self.workspace_id,
                True
            )

            self.__update_intacct_synced_timestamp_object(key='location_entity_synced_at')

    def get_bills(self, bill_ids: list[str], fields: list = None) -> list[dict]:
        """
        GET bills from Sage Intacct
        :param bill_ids: Bill Ids
        :param fields: Fields to be fetched
        :return: Bills
        """
        fields = ['key', 'state']
        filters = [
            {
                '$in': {
                    'key': bill_ids
                }
            },
            {
                '$eq': {
                    'state': 'paid'
                }
            }
        ]
        bill_generator = self.connection.bills.get_all_generator(fields=fields, filters=filters)
        return bill_generator

    def get_expense_reports(self, expense_report_ids: list[str], fields: list = None) -> dict:
        """
        GET expense reports from Sage Intacct
        :param expense_report_ids: Expense Report Ids
        :param fields: Fields to be fetched
        :return: Expense Report
        """
        fields = ['key', 'state']
        filters = [
            {
                '$in': {
                    'key': expense_report_ids
                }
            },
            {
                '$eq': {
                    'state': 'paid'
                }
            }
        ]
        expense_report = self.connection.expense_reports.get_all_generator(fields=fields, filters=filters)

        return expense_report


class SageIntacctObjectCreationManager(SageIntacctRestConnector):
    """
    Sage Intacct Object Creation Manager
    """
    def __init__(self, workspace_id: int):
        """
        Initialize the Sage Intacct Rest Object Creation Manager
        :param: workspace_id: Workspace ID
        """
        super().__init__(workspace_id)

    def __create_destination_attribute(
        self,
        attribute_type: str,
        value: str,
        destination_id: str,
        email: str = None,
    ) -> DestinationAttribute:
        """
        Create Destination Attribute
        :param attribute_type: Attribute Type
        :param value: Value
        :param destination_id: Destination Id
        :param email: Email
        :return: Destination Attribute
        """
        created_attribute = DestinationAttribute.create_or_update_destination_attribute(
            workspace_id=self.workspace_id,
            attribute={
                'attribute_type': attribute_type.upper(),
                'display_name': attribute_type.lower(),
                'value': value,
                'destination_id': destination_id,
                'active': True,
                'detail': {
                    'email': email
                }
            },
        )

        return created_attribute

    def __sanitize_vendor_name(self, vendor_name: str = None) -> str:
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

    def __get_object_key_from_response(self, response: dict) -> Optional[str]:
        """
        Get object key from response
        :param response: Response
        :return: Object Key or None
        """
        return response['ia::result']['key'] if 'key' in response['ia::result'] else None

    def __get_employee(self, employee_name: str) -> Optional[dict]:
        """
        Get employee
        :param employee_name: Employee Name
        :return: Employee or None
        """
        fields = [
            'id',
            'name',
            'status',
            'location.id',
            'department.id',
            'primaryContact.email1',
            'primaryContact.printAs'
        ]
        params = {
            'fields': fields,
            'filters': [
                {
                    '$eq': {
                        'name': employee_name
                    }
                }
            ]
        }

        employee_generator = self.connection.employees.get_all_generator(**params)

        for employees in employee_generator:
            for employee in employees:
                return employee

        return None

    def __get_vendor(self, vendor_name: str) -> Optional[dict]:
        """
        Get vendor
        :param vendor_name: Vendor Name
        :return: Vendor or None
        """
        fields = ['id', 'name', 'status', 'contacts.default.email1']
        params = {
            'fields': fields,
            'filters': [
                {
                    '$eq': {
                        'name': vendor_name
                    }
                },
                {
                    '$eq': {
                        'status': 'active'
                    }
                }
            ],
            'order_by': [
                {
                    'audit.modifiedDateTime': 'desc'
                }
            ]
        }

        vendor_generator = self.connection.vendors.get_all_generator(**params)
        for vendors in vendor_generator:
            for vendor in vendors:
                return vendor

        return None

    def __get_vendor_from_key(self, key: str) -> Optional[dict]:
        """
        Get vendor from key
        :param key: Key
        :return: Vendor or None
        """
        response = self.connection.vendors.get_by_key(key=key)
        return response['ia::result']

    def __get_contact_from_key(self, key: str) -> Optional[dict]:
        """
        Get contact from key
        :param key: Key
        :return: Contact or None
        """
        response = self.connection.contacts.get_by_key(key=key)
        return response['ia::result']

    def __get_employee_from_key(self, key: str) -> Optional[dict]:
        """
        Get employee from key
        :param key: Key
        :return: Employee or None
        """
        response = self.connection.employees.get_by_key(key=key)
        return response['ia::result']

    def create_vendor(
        self,
        vendor_id: str,
        vendor_name: str,
        email: str = None
    ) -> Optional[dict]:
        """
        Create a Vendor in Sage Intacct
        :param vendor_id: Vendor ID
        :param vendor_name: Vendor Name
        :param email: Email
        :return: Vendor or None
        """
        sage_intacct_display_name = vendor_name

        name = vendor_name.split(' ')

        vendor_payload = {
            'id': vendor_id,
            'name': sage_intacct_display_name,
            'contacts': {
                'default': {
                    'printAs': sage_intacct_display_name,
                    'email1': email,
                    'firstName': name[0],
                    'lastName': name[-1] if len(name) == 2 else None
                }
            }
        }

        logger.info("| Payload for the vendor creation | Content : {{WORKSPACE_ID = {}, VENDOR_PAYLOAD = {}}}".format(self.workspace_id, vendor_payload))

        response = self.connection.vendors.post(vendor_payload)
        object_key = self.__get_object_key_from_response(response)

        if not object_key:
            return None

        return self.__get_vendor_from_key(key=object_key)

    def create_contact(
        self,
        contact_id: str,
        contact_name: str,
        email: str = None,
        first_name: str = None,
        last_name: str = None
    ) -> Optional[dict]:
        """
        Create a Contact in Sage Intacct
        :param contact_id: Contact ID
        :param contact_name: Contact Name
        :param email: Email
        :return: Contact or None
        """
        contact_payload = {
            'id': contact_id,
            'printAs': contact_name,
            'email1': email,
            'firstName': first_name,
            'lastName': last_name
        }
        try:
            response = self.connection.contacts.post(contact_payload)
            object_key = self.__get_object_key_from_response(response)
        except Exception as e:
            logger.info("Error while creating contact %s in workspace %s: %s", contact_name, self.workspace_id, e.response)
            return None

        if not object_key:
            return None

        return self.__get_contact_from_key(key=object_key)

    def create_employee(self, employee: ExpenseAttribute) -> Optional[dict]:
        """
        Create an Employee in Sage Intacct
        :param employee: employee attribute to be created
        :return Employee or None
        """
        department = DestinationAttribute.objects.filter(
            workspace_id=self.workspace_id, attribute_type=DestinationAttributeTypeEnum.DEPARTMENT.value,
            value__iexact=employee.detail['department']
        ).first()

        location = DestinationAttribute.objects.filter(
            workspace_id=self.workspace_id, attribute_type=DestinationAttributeTypeEnum.LOCATION.value,
            value__iexact=employee.detail['location']
        ).first()

        general_mappings = GeneralMapping.objects.filter(workspace_id=self.workspace_id).first()

        location_id = location.destination_id if location else None
        department_id = department.destination_id if department else None

        if not location_id and general_mappings:
            location_id = general_mappings.default_location_id

        if not department_id and general_mappings:
            department_id = general_mappings.default_department_id

        sage_intacct_display_name = employee.detail['full_name']
        name = employee.detail['full_name'].split(' ')

        if location_id is None:
            logger.info("Location Id not found for employee %s in workspace %s", employee.detail['full_name'], self.workspace_id)
            return

        contact = self.create_contact(
            contact_id=sage_intacct_display_name,
            contact_name=sage_intacct_display_name,
            email=employee.value,
            first_name=name[0],
            last_name=name[-1] if len(name) == 2 else None
        )

        if not contact:
            logger.info("Error while creating contact for employee %s in workspace %s", employee.detail['full_name'], self.workspace_id)
            return None

        employee_payload = {
            'id': sage_intacct_display_name,
            'primaryContact': {
                'id': contact['id']
            },
            'location': {
                'id': location_id
            },
            'department': {
                'id': department_id
            }
        }

        try:
            response = self.connection.employees.post(employee_payload)
            object_key = self.__get_object_key_from_response(response)
        except Exception as e:
            logger.info("Error while creating employee %s in workspace %s: %s", employee.detail['full_name'], self.workspace_id, e.response)
            return None

        if not object_key:
            return None

        return self.__get_employee_from_key(key=object_key)

    def get_or_create_employee(self, source_employee: ExpenseAttribute) -> DestinationAttribute:
        """
        Get or create employee
        :param source_employee: employee attribute to be created
        :return: Destination Attribute
        """
        employee_name = source_employee.detail['full_name']
        employee = self.__get_employee(employee_name=employee_name)

        if not employee:
            employee = self.create_employee(source_employee)

        return self.__create_destination_attribute(
            attribute_type=DestinationAttributeTypeEnum.EMPLOYEE.value,
            value=employee['name'],
            destination_id=employee['id'],
            email=source_employee.value
        )

    def get_or_create_vendor(
        self,
        vendor_name: str,
        email: str = None,
        create: bool = False,
    ) -> Optional[DestinationAttribute]:
        """
        Get or create vendor
        :param vendor_name: Name of the vendor
        :param email: Email of the vendor
        :param create: False to just Get and True to Get or Create if not exists
        :return: Vendor or None
        """
        vendor_from_db = DestinationAttribute.objects.filter(
            workspace_id=self.workspace_id,
            attribute_type=DestinationAttributeTypeEnum.VENDOR.value,
            active=True
        ).filter(
            Q(value__iexact=vendor_name.lower()) | Q(destination_id__iexact=vendor_name.lower())
        ).first()

        if vendor_from_db:
            return vendor_from_db

        try:
            if create:
                vendor_id = self.__sanitize_vendor_name(vendor_name)

                if len(vendor_id) > 20:
                    vendor_id = vendor_id[:17] + str(random.randint(100, 999))

                created_vendor = self.create_vendor(vendor_id, vendor_name, email)

                return self.__create_destination_attribute(
                    attribute_type=DestinationAttributeTypeEnum.VENDOR.value,
                    value=vendor_name,
                    destination_id=created_vendor['id'],
                    email=email
                )

        except BadRequestError as e:
            logger.info("Error while creating vendor %s in workspace %s: %s", vendor_name, self.workspace_id, e.response)

            try:
                error_response = json.loads(e.response) if isinstance(e.response, str) else e.response
            except (json.JSONDecodeError, TypeError):
                logger.error("Failed to parse error response for vendor %s in workspace %s", vendor_name, self.workspace_id)
                return None

            if 'ia::result' in error_response and 'ia::error' in error_response['ia::result']:
                sage_intacct_errors = error_response['ia::result']['ia::error']

                if 'Another record with the value' in str(sage_intacct_errors['details']):
                    logger.info('Searching for vendor: %s in Sage Intacct in workspace %s', vendor_name, self.workspace_id)
                    vendor_from_intacct = self.__get_vendor(vendor_name=vendor_name.replace("'", "\\'"))
                    vendor_name = vendor_name.replace(',', '').replace("'", ' ').replace('-', ' ')[:20]

                    if not vendor_from_intacct:
                        try:
                            vendor_id = vendor_id[:18] + '-1'
                            vendor_from_intacct = self.create_vendor(
                                vendor_id=vendor_id,
                                vendor_name=vendor_name,
                                email=email
                            )
                        except Exception as e:
                            logger.error("Error while creating vendor %s in workspace %s: %s", vendor_name, self.workspace_id, e.response)
                            return None

                    if vendor_from_intacct:
                        return self.__create_destination_attribute(
                            attribute_type=DestinationAttributeTypeEnum.VENDOR.value,
                            value=vendor_name,
                            destination_id=vendor_from_intacct['id'],
                            email=email
                        )

    def search_and_create_vendors(self, workspace_id: int, missing_vendors: list[str]) -> None:
        """
        Seach vendors in Intacct and Upsert Vendors in DB
        :param workspace_id: Workspace ID
        :param missing_vendors: Missing Vendors List
        """
        missing_vendors_batches = [missing_vendors[i:i + 50] for i in range(0, len(missing_vendors), 50)]
        fields = ['id', 'name', 'status', 'contacts.default.email1']

        for missing_vendors_batch in missing_vendors_batches:
            vendors_list = [vendor.replace("'", "\\'") for vendor in missing_vendors_batch]

            filters = [
                {
                    '$in': {
                        'name': vendors_list
                    }
                },
                {
                    '$eq': {
                        'status': 'active'
                    }
                }
            ]

            order_by = [
                {
                    'audit.modifiedDateTime': 'desc'
                }
            ]

            vendors_generator = self.connection.vendors.get_all_generator(fields=fields, filters=filters, order_by=order_by)

            # To Keep only most recently modified vendor for each name
            unique_vendors = {}

            for vendors in vendors_generator:
                for vendor in vendors:
                    name_key = vendor.get('name', '')

                    if name_key not in unique_vendors:
                        unique_vendors[name_key] = vendor

            for vendor in unique_vendors.values():
                logger.info("Upserting Vendor %s in Workspace %s", vendor['name'], workspace_id)
                self.__create_destination_attribute(
                    attribute_type=DestinationAttributeTypeEnum.VENDOR.value,
                    value=vendor['name'],
                    destination_id=vendor['id'],
                    email=vendor.get('contacts.default.email1')
                )

    def post_expense_report(
        self,
        expense_report: ExpenseReport,
        expense_report_line_items: list[ExpenseReportLineitem]
    ) -> None:
        """
        Post expense report to Sage Intacct
        :param expense_report: ExpenseReport object
        :param expense_report_line_items: ExpenseReportLineitem objects
        :return: None
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        try:
            expense_report_payload = construct_expense_report_payload(
                workspace_id=self.workspace_id,
                expense_report=expense_report,
                expense_report_line_items=expense_report_line_items
            )
            created_expense_report = self.connection.expense_reports.post(expense_report_payload)
            return created_expense_report

        except BadRequestError as e:
            logger.info(e.response)
            is_exception_handled = False

            try:
                error_response = json.loads(e.response) if isinstance(e.response, str) else e.response
            except (json.JSONDecodeError, TypeError):
                logger.error("Failed to parse error response for expense report in workspace %s", self.workspace_id)

            if 'ia::result' in error_response and 'ia::error' in error_response['ia::result']:
                sage_intacct_errors = error_response['ia::result']['ia::error']

                error_words_list = ['period', 'closed', 'Date must be on or after']
                if any(word in str(sage_intacct_errors['details']) for word in error_words_list):
                    if configuration.change_accounting_period:
                        first_day_of_month = datetime.today().date().replace(day=1)

                        expense_report_payload = construct_expense_report_payload(
                            workspace_id=self.workspace_id,
                            expense_report=expense_report,
                            expense_report_line_items=expense_report_line_items
                        )
                        expense_report_payload['createdDate'] = first_day_of_month.strftime('%Y-%m-%d'),
                        created_expense_report = self.connection.expense_reports.post(expense_report_payload)
                        is_exception_handled = True

                        return created_expense_report

            if not is_exception_handled:
                raise

    def post_bill(
        self,
        bill: Bill,
        bill_line_items: list[BillLineitem]
    ) -> dict:
        """
        Post bill to Sage Intacct
        :param bill: Bill object
        :param bill_line_items: BillLineitem objects
        :return: created bill
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        try:
            bill_payload = construct_bill_payload(
                workspace_id=self.workspace_id,
                bill=bill,
                bill_line_items=bill_line_items
            )
            created_bill = self.connection.bills.post(bill_payload)
            return created_bill

        except BadRequestError as e:
            logger.info(e.response)
            is_exception_handled = False

            try:
                error_response = json.loads(e.response) if isinstance(e.response, str) else e.response
            except (json.JSONDecodeError, TypeError):
                logger.error("Failed to parse error response for bill in workspace %s", self.workspace_id)

            if 'ia::result' in error_response and 'ia::error' in error_response['ia::result']:
                sage_intacct_errors = error_response['ia::result']['ia::error']
                error_words_list = ['period', 'closed', 'Date must be on or after']

                if any(word in str(sage_intacct_errors['details']) for word in error_words_list):
                    if configuration.change_accounting_period:
                        first_day_of_month = datetime.today().date().replace(day=1)

                        bill_payload = construct_bill_payload(
                            workspace_id=self.workspace_id,
                            bill=bill,
                            bill_line_items=bill_line_items
                        )
                        bill_payload['createdDate'] = first_day_of_month.strftime('%Y-%m-%d')
                        created_bill = self.connection.bills.post(bill_payload)
                        is_exception_handled = True

                        return created_bill

            if not is_exception_handled:
                raise

    def post_charge_card_transaction(
        self,
        charge_card_transaction: ChargeCardTransaction,
        charge_card_transaction_line_items: list[ChargeCardTransactionLineitem]
    ) -> dict:
        """
        Post charge card transaction to Sage Intacct
        :param charge_card_transaction: ChargeCardTransaction object
        :param charge_card_transaction_line_items: ChargeCardTransactionLineitem objects
        :return: created charge card transaction
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        try:
            charge_card_transaction_payload = construct_charge_card_transaction_payload(
                workspace_id=self.workspace_id,
                charge_card_transaction=charge_card_transaction,
                charge_card_transaction_line_items=charge_card_transaction_line_items
            )
            created_charge_card_transaction = self.connection.charge_card_transactions.post(charge_card_transaction_payload)
            return created_charge_card_transaction

        except BadRequestError as e:
            logger.info(e.response)
            is_exception_handled = False

            try:
                error_response = json.loads(e.response) if isinstance(e.response, str) else e.response
            except (json.JSONDecodeError, TypeError):
                logger.error("Failed to parse error response for charge card transaction in workspace %s", self.workspace_id)

            if 'ia::result' in error_response and 'ia::error' in error_response['ia::result']:
                sage_intacct_errors = error_response['ia::result']['ia::error']
                error_words_list = ['period', 'closed', 'Date must be on or after']

                if any(word in str(sage_intacct_errors['details']) for word in error_words_list):
                    if configuration.change_accounting_period:
                        first_day_of_month = datetime.today().date().replace(day=1)

                        charge_card_transaction_payload = construct_charge_card_transaction_payload(
                            workspace_id=self.workspace_id,
                            charge_card_transaction=charge_card_transaction,
                            charge_card_transaction_line_items=charge_card_transaction_line_items
                        )
                        charge_card_transaction_payload['txnDate'] = first_day_of_month.strftime('%Y-%m-%d')
                        created_charge_card_transaction = self.connection.charge_card_transactions.post(charge_card_transaction_payload)
                        is_exception_handled = True

                        return created_charge_card_transaction

            if not is_exception_handled:
                raise

    def post_journal_entry(
        self,
        journal_entry: JournalEntry,
        journal_entry_line_items: list[JournalEntryLineitem]
    ) -> dict:
        """
        Post journal_entry  to Sage Intacct
        :param journal_entry: JournalEntry object
        :param journal_entry_lineitems: JournalEntryLineitem objects
        :return: created journal_entry
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        try:
            journal_entry_payload = construct_journal_entry_payload(
                workspace_id=self.workspace_id,
                journal_entry=journal_entry,
                journal_entry_line_items=journal_entry_line_items
            )
            created_journal_entry = self.connection.journal_entries.post(journal_entry_payload)
            return created_journal_entry

        except BadRequestError as exception:
            logger.info(exception.response)
            is_exception_handled = False

            try:
                error_response = json.loads(exception.response) if isinstance(exception.response, str) else exception.response
            except (json.JSONDecodeError, TypeError):
                logger.error("Failed to parse error response for journal entry in workspace %s", self.workspace_id)

            if 'ia::result' in error_response and 'ia::error' in error_response['ia::result']:
                sage_intacct_errors = error_response['ia::result']['ia::error']
                error_words_list = ['period', 'closed', 'Date must be on or after']

                if any(word in str(sage_intacct_errors['details']) for word in error_words_list):
                    if configuration.change_accounting_period:
                        first_day_of_month = datetime.today().date().replace(day=1)
                        journal_entry_payload = construct_journal_entry_payload(
                            workspace_id=self.workspace_id,
                            journal_entry=journal_entry,
                            journal_entry_line_items=journal_entry_line_items
                        )
                        journal_entry_payload['postingDate'] = first_day_of_month.strftime('%Y-%m-%d')
                        created_journal_entry = self.connection.journal_entries.post(journal_entry_payload)
                        is_exception_handled = True

                        return created_journal_entry

            if not is_exception_handled:
                raise

    def post_ap_payment(self, ap_payment: APPayment, ap_payment_line_items: list[APPaymentLineitem]) -> dict:
        """
        Post AP Payment to Sage Intacct
        :param ap_payment: APPayment object
        :param ap_payment_line_items: APPaymentLineItem objects
        :return: created AP Payment
        """
        ap_payment_payload = construct_ap_payment_payload(
            workspace_id=self.workspace_id,
            ap_payment=ap_payment,
            ap_payment_line_items=ap_payment_line_items
        )
        created_ap_payment = self.connection.ap_payments.post(ap_payment_payload)
        return created_ap_payment

    def post_sage_intacct_reimbursement(
        self,
        reimbursement: SageIntacctReimbursement,
        reimbursement_line_items: list[SageIntacctReimbursementLineitem]
    ) -> dict:
        """
        Post Reimbursement to Sage Intacct
        :param reimbursement: SageIntacctReimbursement object
        :param reimbursement_line_items: SageIntacctReimbursementLineItem objects
        :return: created Reimbursement
        """
        reimbursement_payload = construct_reimbursement_payload(
            workspace_id=self.workspace_id,
            reimbursement=reimbursement,
            reimbursement_line_items=reimbursement_line_items
        )

        sdk_soap_connection = self.get_soap_connection()
        created_reimbursement = sdk_soap_connection.reimbursements.post(reimbursement_payload)

        return created_reimbursement

    def get_or_create_attachments_folder(self) -> None:
        """
        Get or Create attachments folder in Sage Intacct
        """
        params = {
            'fields': ['id', 'status'],
            'filters': [
                {
                    '$eq': {
                        'id': 'FyleAttachments'
                    }
                }
            ]
        }
        attachment_folder_generator = self.connection.attachment_folders.get_all_generator(**params)

        for attachment_folder in attachment_folder_generator:
            if not attachment_folder:
                return self.connection.attachment_folders.post({
                    'id': 'FyleAttachments'
                })

    def post_attachments(self, attachments: list[dict], attachment_id: str, attachment_number: int, attachment_key: str = None) -> tuple[str, str] | tuple[bool, None]:
        """
        Post attachments to Sage Intacct
        :param attachments: List of attachment dictionaries
        :param attachment_id: Supporting document ID to be used in Sage Intacct
        :param attachment_number: Number used to uniquely name attachments
        :param attachment_key: Attachment key
        :return: attachment_id if first attachment is successfully posted, else False
        """
        if not attachments:
            return False, None

        for attachment in attachments:
            payload = {
                'id': str(attachment_id),
                'name': str(attachment_id),
                'folder': {
                    'id': 'FyleAttachments'
                },
                'files': [{
                    'name': f'{attachment["id"]} - {attachment_number}',
                    'data': attachment['download_url'],
                }]
            }

            if attachment_number == 1:
                created_attachment = self.connection.attachments.post(payload)
            else:
                try:
                    payload.pop('id')
                    self.connection.attachments.update(key=attachment_key, data=payload)
                except Exception as e:
                    logger.info(f'Error updating attachment {attachment_number} for supdoc {attachment_id} - {e.response}')
                    continue

        if attachment_number == 1 and created_attachment['ia::result'] and created_attachment['ia::result'].get('key'):
            return attachment_id, created_attachment['ia::result'].get('key')

        return False, None

    def update_expense_report_attachments(self, object_key: str, attachment_id: str) -> dict:
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: expense report id
        :param attachment_id: attachments id
        :return: response from sage intacct
        """
        return self.connection.expense_reports.update_attachment(object_id=object_key, attachment_id=str(attachment_id))

    def update_bill_attachments(self, object_key: str, attachment_id: str) -> dict:
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: bill id
        :param attachment_id: attachments id
        :return: response from sage intacct
        """
        return self.connection.bills.update_attachment(object_id=object_key, attachment_id=str(attachment_id))

    def update_charge_card_transaction_attachments(self, object_key: str, attachment_id: str) -> dict:
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: charge card transaction id
        :param attachment_id: attachments id
        :return: response from sage intacct
        """
        return self.connection.charge_card_transactions.update_attachment(object_id=object_key, attachment_id=str(attachment_id))

    def update_journal_entry_attachments(self, object_key: str, attachment_id: str) -> dict:
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: journal entry id
        :param attachment_id: attachments id
        :return: response from sage intacct
        """
        return self.connection.journal_entries.update_attachment(object_id=object_key, attachment_id=str(attachment_id))

    def get_journal_entry(self, journal_entry_id: str, fields: list = None) -> dict:
        """
        Get journal entry from Sage Intacct
        :param journal_entry_id: Journal Entry Id
        :param fields: Fields to be fetched
        :return: Journal Entry
        """
        soap_sdk_connection = self.get_soap_connection()
        journal_entry = soap_sdk_connection.journal_entries.get(field='RECORDNO', value=journal_entry_id, fields=fields)

        return journal_entry

    def get_charge_card_transaction(self, charge_card_transaction_id: str, fields: list = None) -> dict:
        """
        GET charge card transaction from Sage Intacct
        :param charge_card_transaction_id: Charge Card Transaction Id
        :param fields: Fields to be fetched
        :return: Charge Card Transaction
        """
        soap_sdk_connection = self.get_soap_connection()
        charge_card_transaction = soap_sdk_connection.charge_card_transactions.get(
            field='RECORDNO',
            value=charge_card_transaction_id,
            fields=fields
        )

        return charge_card_transaction

    def get_bill(self, bill_id: str, fields: list = None) -> dict:
        """
        GET bill from Sage Intacct
        :param bill_id: Bill Id
        :param fields: Fields to be fetched
        :return: Bill
        """
        soap_sdk_connection = self.get_soap_connection()
        bill = soap_sdk_connection.bills.get(field='RECORDNO', value=bill_id, fields=fields)

        return bill

    def get_expense_report(self, expense_report_id: str, fields: list = None) -> dict:
        """
        GET expense reports from Sage Intacct
        :param expense_report_id: Expense Report Id
        :param fields: Fields to be fetched
        :return: Expense Report
        """
        soap_sdk_connection = self.get_soap_connection()
        expense_report = soap_sdk_connection.expense_reports.get(field='RECORDNO', value=expense_report_id, fields=fields)

        return expense_report
