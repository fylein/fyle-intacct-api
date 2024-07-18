import logging
import base64
from typing import List, Dict
from datetime import datetime, timedelta
import unidecode
import time
from django.conf import settings

from cryptography.fernet import Fernet

from django.conf import settings
from django.db.models import Q

from sageintacctsdk import SageIntacctSDK
from sageintacctsdk.exceptions import WrongParamsError

from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute
from apps.fyle.models import DependentFieldSetting
from apps.mappings.models import GeneralMapping, LocationEntityMapping
from apps.workspaces.models import SageIntacctCredential, FyleCredential, Workspace, Configuration

from .models import (
    ExpenseReport, ExpenseReportLineitem, Bill, BillLineitem, ChargeCardTransaction, 
    ChargeCardTransactionLineitem, APPayment, APPaymentLineitem, JournalEntry, JournalEntryLineitem, SageIntacctReimbursement,
    SageIntacctReimbursementLineitem, CostType, get_user_defined_dimension_object
)

logger = logging.getLogger(__name__)


SYNC_UPPER_LIMIT = {
    'projects': 25000,
    'customers': 15000,
    'items':15000,
    'classes': 15000
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


    def get_tax_solution_id_or_none(self, lineitems):

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


    def get_tax_exclusive_amount(self, amount, default_tax_code_id):

        tax_attribute = DestinationAttribute.objects.filter(destination_id=default_tax_code_id, attribute_type='TAX_DETAIL',workspace_id=self.workspace_id).first()
        tax_exclusive_amount = amount
        tax_amount = None
        if tax_attribute:
            tax_rate = int(tax_attribute.detail['tax_rate'])
            tax_exclusive_amount = round((amount - (amount/(tax_rate + 1))), 2)
            tax_amount = round((amount - tax_exclusive_amount), 2)

        return tax_exclusive_amount, tax_amount

    def sync_accounts(self):
        """
        Get accounts
        """
        accounts = self.connection.accounts.get_all()

        account_attributes = {
            'account': [],
            'ccc_account': []
        }
        destination_attributes = DestinationAttribute.objects.filter(workspace_id=self.workspace_id, 
                attribute_type= 'ACCOUNT', display_name='account').values('destination_id', 'value', 'detail')
        disabled_fields_map = {}

        for destination_attribute in destination_attributes:
            disabled_fields_map[destination_attribute['destination_id']] = {
                'value': destination_attribute['value'],
                'detail': destination_attribute['detail']
            }

        for account in accounts:
            if account['STATUS'] == 'active':
                account_attributes['account'].append({
                    'attribute_type': 'ACCOUNT',
                    'display_name': 'account',
                    'value': unidecode.unidecode(u'{0}'.format(account['TITLE'].replace('/', '-'))),
                    'destination_id': account['ACCOUNTNO'],
                    'active': True,
                    'detail': {
                        'account_type': account['ACCOUNTTYPE']
                    }
                })
                if account['ACCOUNTNO'] in disabled_fields_map:
                    disabled_fields_map.pop(account['ACCOUNTNO'])

        # For setting active to False
        # During the initial run we only pull in the active ones.
        # In the concurrent runs we get all the destination_attributes and store it in disable_field_map check if in the SDK call we get status = Active or not .
            # If yes then we pop the item from the disable_field_map else we set the active = True.
        # This should take care of delete as well as inactive case since we are checking the status=Active case.
        for destination_id in disabled_fields_map:
            account_attributes['account'].append({
                'attribute_type': 'ACCOUNT',
                'display_name': 'account',
                'value': disabled_fields_map[destination_id]['value'],
                'destination_id': destination_id,
                'active': False,
                'detail': disabled_fields_map[destination_id]['detail']
            })

        for attribute_type, account_attribute in account_attributes.items():
            if account_attribute:
                DestinationAttribute.bulk_create_or_update_destination_attributes(
                    account_attribute, attribute_type.upper(), self.workspace_id, True)
        return []

    def sync_departments(self):
        """
        Get departments
        """
        departments = self.connection.departments.get_all(field='STATUS', value='active')

        department_attributes = []

        for department in departments:
            department_attributes.append({
                'attribute_type': 'DEPARTMENT',
                'display_name': 'department',
                'value': department['TITLE'],
                'destination_id': department['DEPARTMENTID'],
                'active': True
            })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            department_attributes, 'DEPARTMENT', self.workspace_id, True)

        return []

    def sync_expense_types(self):
        """
        Get expense types
        """
        expense_types = self.connection.expense_types.get_all()

        expense_types_attributes = []
        destination_attributes = DestinationAttribute.objects.filter(workspace_id=self.workspace_id,
                attribute_type= 'EXPENSE_TYPE', display_name='Expense Types').values('destination_id', 'value', 'detail')
        disabled_fields_map = {}

        for destination_attribute in destination_attributes:
            disabled_fields_map[destination_attribute['destination_id']] = {
                'value': destination_attribute['value'],
                'detail': destination_attribute['detail']
            }

        for expense_type in expense_types:
            if expense_type['STATUS'] == 'active':
                expense_types_attributes.append({
                    'attribute_type': 'EXPENSE_TYPE',
                    'display_name': 'Expense Types',
                    'value': unidecode.unidecode(u'{0}'.format(expense_type['DESCRIPTION'].replace('/', '-'))),
                    'destination_id': expense_type['ACCOUNTLABEL'],
                    'active': True,
                    'detail': {
                        'gl_account_no': expense_type['GLACCOUNTNO'],
                        'gl_account_title': expense_type['GLACCOUNTTITLE']
                    }
                })
                if expense_type['ACCOUNTLABEL'] in disabled_fields_map:
                    disabled_fields_map.pop(expense_type['ACCOUNTLABEL'])
        
        # For setting active to False
        # During the initial run we only pull in the active ones.
        # In the concurrent runs we get all the destination_attributes and store it in disable_field_map check if in the SDK call we get status = Active or not .
            # If yes then we pop the item from the disable_field_map else we set the active = True.
        # This should take care of delete as well as inactive case since we are checking the status=Active case.
        for destination_id in disabled_fields_map:
            expense_types_attributes.append({
                'attribute_type': 'EXPENSE_TYPE',
                'display_name': 'Expense Types',
                'value': disabled_fields_map[destination_id]['value'],
                'destination_id': destination_id,
                'active': False,
                'detail': disabled_fields_map[destination_id]['detail']
            })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            expense_types_attributes, 'EXPENSE_TYPE', self.workspace_id, True)
        return []

    def sync_charge_card_accounts(self):
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

    def sync_payment_accounts(self):
        """
        Get Payment accounts
        """
        payment_accounts = self.connection.checking_accounts.get_all(field='STATUS', value='active') 

        payment_accounts_attributes = []

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

    def sync_cost_types(self):
        """
        Sync of Sage Intacct Cost Types
        """
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


    def sync_projects(self):
        """
        Get projects
        """
        projects_count = self.connection.projects.count()
        if projects_count < SYNC_UPPER_LIMIT['projects']:
            projects = self.connection.projects.get_all()

            project_attributes = []
            destination_attributes = DestinationAttribute.objects.filter(workspace_id=self.workspace_id,
                attribute_type= 'PROJECT', display_name='project').values('destination_id', 'value', 'detail')
            disabled_fields_map = {}

            for destination_attribute in destination_attributes:
                disabled_fields_map[destination_attribute['destination_id']] = {
                    'value': destination_attribute['value'],
                    'detail': destination_attribute['detail']
                }

            for project in projects:
                if project['STATUS'] == 'active':
                    detail = {
                        'customer_id': project['CUSTOMERID'],
                        'customer_name': project['CUSTOMERNAME']
                    }

                    project_attributes.append({
                        'attribute_type': 'PROJECT',
                        'display_name': 'project',
                        'value': project['NAME'],
                        'destination_id': project['PROJECTID'],
                        'active': True,
                        'detail': detail
                    })
                    if project['PROJECTID'] in disabled_fields_map:
                        disabled_fields_map.pop(project['PROJECTID'])

            # For setting active to False
            # During the initial run we only pull in the active ones.
            # In the concurrent runs we get all the destination_attributes and store it in disable_field_map check if in the SDK call we get status = Active or not .
                # If yes then we pop the item from the disable_field_map else we set the active = True.
            # This should take care of delete as well as inactive case since we are checking the status=Active case.
            for destination_id in disabled_fields_map:
                project_attributes.append({
                    'attribute_type': 'PROJECT',
                    'display_name': 'project',
                    'value': disabled_fields_map[destination_id]['value'],
                    'destination_id': destination_id,
                    'active': False,
                    'detail': disabled_fields_map[destination_id]['detail']
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                project_attributes, 'PROJECT', self.workspace_id, True)

        return []

    def sync_items(self):
        """
        Get items
        """
        count = self.connection.items.count()
        if count <= SYNC_UPPER_LIMIT['items']:
            items = self.connection.items.get_all(field='STATUS', value='active')

            item_attributes = []

            for item in items:
                # remove this check when we are mapping Fyle Categories with Sage Intacct Items
                if item['ITEMTYPE'] == 'Non-Inventory':
                    item_attributes.append({
                        'attribute_type': 'ITEM',
                        'display_name': 'item',
                        'value': item['NAME'],
                        'destination_id': item['ITEMID'],
                        'active': True
                    })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                item_attributes, 'ITEM', self.workspace_id, True)

        return []

    def sync_locations(self):
        """
        Get locations
        """
        locations = self.connection.locations.get_all(field='STATUS', value='active')

        location_attributes = []

        for location in locations:
            location_attributes.append({
                'attribute_type': 'LOCATION',
                'display_name': 'location',
                'value': location['NAME'],
                'destination_id': location['LOCATIONID'],
                'active': True
            })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            location_attributes, 'LOCATION', self.workspace_id, True)

        return []

    def __get_entity_slide_preference(self):
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


    def sync_location_entities(self):
        """
        Get location entities
        """
        if not self.__get_entity_slide_preference():
            location_entities = self.connection.location_entities.get_all(field='STATUS', value='active')

            location_entities_attributes = []

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


    def sync_expense_payment_types(self):
        """
        Get Expense Payment Types
        """
        expense_payment_types = self.connection.expense_payment_types.get_all(field='STATUS', value='active')

        expense_payment_type_attributes = []

        for expense_payment_type in expense_payment_types:
            expense_payment_type_attributes.append({
                'attribute_type': 'EXPENSE_PAYMENT_TYPE',
                'display_name': 'expense payment type',
                'value': expense_payment_type['NAME'],
                'destination_id': expense_payment_type['RECORDNO'],
                'detail': {
                    'is_reimbursable': True if expense_payment_type['NONREIMBURSABLE'] == 'false' else False
                },
                'active': True
            })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            expense_payment_type_attributes, 'EXPENSE_PAYMENT_TYPE', self.workspace_id, True)

        return []

    def sync_employees(self):
        """
        Get employees
        """
        employees = self.connection.employees.get_all(field='STATUS', value='active')

        employee_attributes = []

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

    def sync_allocation_entries(self):
        """
        Sync allocation entries from intacct
        """
        allocation_attributes = []
        allocations_generator = self.connection.allocations.get_all_generator(field='STATUS', value='active')

        for allocations in allocations_generator:
            for allocation in allocations:
                allocation_entry_generator = self.connection.allocation_entry.get_all_generator(field='allocation.ALLOCATIONID', value=allocation['ALLOCATIONID'])
                for allocation_entry in allocation_entry_generator:
                    detail = {}
                    for entry in allocation_entry:
                        value = entry['ALLOCATIONID']
                        destinaion_id = entry['ALLOCATIONKEY']
                        for field in entry.keys():
                            if entry[field] is not None and field not in detail:
                                detail[field] = True
                    
                    detail.pop('ALLOCATIONID')
                    detail.pop('ALLOCATIONKEY')

                    allocation_attributes.append(
                    {
                        'attribute_type': 'ALLOCATION_ENTRY',
                        'display_name': 'allocation_entry',
                        'value': value,
                        'destination_id': destinaion_id,
                        'active': True,
                        'detail': detail
                    })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            allocation_attributes, 'ALLOCATION_ENTRY', self.workspace_id
        )


    def sync_user_defined_dimensions(self):
        """
        Get User Defined Dimensions
        """

        dimensions = self.connection.dimensions.get_all()

        for dimension in dimensions:
            if dimension['userDefinedDimension'] == 'true':
                dimension_attributes = []
                dimension_name = dimension['objectName']
                dimension_values = self.connection.dimension_values.get_all(dimension_name)

                for value in dimension_values:
                    dimension_attributes.append({
                        'attribute_type': dimension_name,
                        'display_name': dimension_name.lower().replace('_', ' '),
                        'value': value['name'],
                        'destination_id': value['id'],
                        'active': True
                    })

                DestinationAttribute.bulk_create_or_update_destination_attributes(
                    dimension_attributes, dimension_name, self.workspace_id
                )

        return []

    def sync_classes(self):
        """
        Get classes
        """
        count = self.connection.classes.count()
        if count <= SYNC_UPPER_LIMIT['classes']:
            classes = self.connection.classes.get_all(field='STATUS', value='active', fields=['NAME', 'CLASSID'])
            class_attributes = []

            for _class in classes:
                class_attributes.append({
                    'attribute_type': 'CLASS',
                    'display_name': 'class',
                    'value': _class['NAME'],
                    'destination_id': _class['CLASSID'],
                    'active': True
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                class_attributes, 'CLASS', self.workspace_id, True)

        return []

    def sync_customers(self):
        """
        Get Customers
        """
        customers_count = self.connection.customers.count()
        if customers_count < SYNC_UPPER_LIMIT['customers']:
            customers = self.connection.customers.get_all(field='STATUS', value='active', fields=['NAME', 'CUSTOMERID'])

            customer_attributes = []

            for customer in customers:
                customer_attributes.append({
                    'attribute_type': 'CUSTOMER',
                    'display_name': 'customer',
                    'value': customer['NAME'],
                    'destination_id': customer['CUSTOMERID'],
                    'active': True
                })

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                customer_attributes, 'CUSTOMER', self.workspace_id, True)

        return []

    def sync_tax_details(self):
        """
        Get and Sync Tax Details
        """
        attributes = []
        tax_details = self.connection.tax_details.get_all(field='STATUS', value='active')
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
                attributes, 'TAX_DETAIL', self.workspace_id, True)

        return []

    def create_destination_attribute(self, attribute: str, name: str, destination_id: str, email: str = None):
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

    def get_or_create_employee(self, source_employee: ExpenseAttribute):
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

    def get_or_create_vendor(self, vendor_name: str, email: str = None, create: bool = False):
        """
        Call Sage Intacct api to get or create vendor
        :param vendor_name: Name of the vendor
        :param email: Email of the vendor
        :param create: False to just Get and True to Get or Create if not exists
        :return: Vendor
        """
        vendor_from_db = DestinationAttribute.objects.filter(workspace_id=self.workspace_id, attribute_type='VENDOR', value=vendor_name, active=True).first()

        if vendor_from_db:
            return vendor_from_db

        logger.info('Searching for vendor: %s in Sage Intacct', vendor_name)
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
            vendor = None

        if not vendor:
            if create:
                vendor_id = vendor_name
                created_vendor = self.post_vendor(vendor_id, vendor_name, email)
                return self.create_destination_attribute(
                    'vendor', vendor_name, created_vendor['VENDORID'], email)
            else:
                return
        else:
            return self.create_destination_attribute(
                'vendor', vendor['NAME'], vendor['VENDORID'], vendor['DISPLAYCONTACT.EMAIL1'])

    def get_expense_link(self, lineitem) -> str:
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

        expense_link = '{0}/app/admin/#/enterprise/view_expense/{1}?org_id={2}'.format(
            settings.FYLE_EXPENSE_URL, lineitem.expense.expense_id, org_id
        )

        return expense_link

    def post_employees(self, employee: ExpenseAttribute):
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


    def sync_vendors(self):
        """
        Get vendors
        """
        vendors = self.connection.vendors.get_all()
        vendor_attributes = []

        destination_attributes = DestinationAttribute.objects.filter(workspace_id=self.workspace_id,
                attribute_type= 'VENDOR', display_name='vendor').values('destination_id', 'value', 'detail')
        disabled_fields_map = {}

        for destination_attribute in destination_attributes:
            disabled_fields_map[destination_attribute['destination_id']] = {
                'value': destination_attribute['value'],
                'detail': destination_attribute['detail']
            }

        for vendor in vendors:
            if vendor['STATUS'] == 'active':
                detail = {
                    'email': vendor['DISPLAYCONTACT.EMAIL1'] if vendor['DISPLAYCONTACT.EMAIL1'] else None
                }
                vendor_attributes.append({
                    'attribute_type': 'VENDOR',
                    'display_name': 'vendor',
                    'value': vendor['NAME'],
                    'destination_id': vendor['VENDORID'],
                    'detail': detail,
                    'active': True
                })

                if vendor['VENDORID'] in disabled_fields_map:
                    disabled_fields_map.pop(vendor['VENDORID'])

        for destination_id in disabled_fields_map:
            vendor_attributes.append({
                'attribute_type': 'VENDOR',
                'display_name': 'vendor',
                'value': disabled_fields_map[destination_id]['value'],
                'destination_id': destination_id,
                'active': False,
                'detail': disabled_fields_map[destination_id]['detail']
            })

        if vendor_attributes:
            DestinationAttribute.bulk_create_or_update_destination_attributes(
                vendor_attributes, 'VENDOR', self.workspace_id, True
            )

        return []

    def post_vendor(self, vendor_id: str, vendor_name: str, email: str = None):
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

    def __construct_expense_report(self, expense_report: ExpenseReport,
                                   expense_report_lineitems: List[ExpenseReportLineitem]) -> Dict:
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

            expense = {
                'expensetype' if lineitem.expense_type_id else 'glaccountno': lineitem.expense_type_id \
                if lineitem.expense_type_id else lineitem.gl_account_number,
                'amount': lineitem.amount - lineitem.tax_amount if (lineitem.tax_code and lineitem.tax_amount) else tax_exclusive_amount,
                'expensedate': {
                    'year': transaction_date.year,
                    'month': transaction_date.month,
                    'day': transaction_date.day
                },
                'memo': lineitem.memo,
                'locationid': lineitem.location_id,
                'departmentid': lineitem.department_id,
                'customfields': {
                   'customfield': [
                    {
                        'customfieldname': 'FYLE_EXPENSE_URL',
                        'customfieldvalue': expense_link
                    },
                   ]
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

    def __construct_bill(self, bill: Bill, bill_lineitems: List[BillLineitem]) -> Dict:
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
                'TAXENTRIES': {
                    'TAXENTRY': {
                        'DETAILID': lineitem.tax_code if (lineitem.tax_code and lineitem.tax_amount) else general_mappings.default_tax_code_id
                    }
                },
                'customfields': {
                   'customfield': [
                    {
                        'customfieldname': 'FYLE_EXPENSE_URL',
                        'customfieldvalue': expense_link
                    },
                   ]
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

    def __construct_charge_card_transaction(self, charge_card_transaction: ChargeCardTransaction, \
                                            charge_card_transaction_lineitems: List[
                                                ChargeCardTransactionLineitem]) -> Dict:
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
                   'customfield': [
                    {
                        'customfieldname': 'FYLE_EXPENSE_URL',
                        'customfieldvalue': expense_link
                    },
                   ]
                },
                'totaltrxamount': lineitem.amount,
                'taxentries': {
                    'taxentry': {
                        'detailid': lineitem.tax_code if (lineitem.tax_code and lineitem.tax_amount) else general_mappings.default_tax_code_id,
                    }
                },
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

    def __construct_journal_entry(self, journal_entry: JournalEntry, journal_entry_lineitems: List[JournalEntryLineitem], recordno : str  = None) -> Dict:
        """
        Create a journal_entry
        :param journal_entry: JournalEntry object extracted from database
        :param journal_entry_lineitems: JournalEntryLineItem objects extracted from database
        :return: constructed journal_entry
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        general_mappings = GeneralMapping.objects.get(workspace_id=self.workspace_id)

        journal_entry_payload = []

        for lineitem in journal_entry_lineitems:
            expense_link = self.get_expense_link(lineitem)
            credit_line = {
                'accountno': general_mappings.default_credit_card_id if journal_entry.expense_group.fund_source == 'CCC' else general_mappings.default_gl_account_id,
                'currency': journal_entry.currency,
                'amount': lineitem.amount,
                'tr_type': -1,
                'description': lineitem.memo,
                'department': lineitem.department_id,
                'location': lineitem.location_id,
                'projectid': lineitem.project_id,
                'customerid': lineitem.customer_id,
                'vendorid': lineitem.vendor_id,
                'employeeid': lineitem.employee_id,
                'itemid': lineitem.item_id,
                'classid': lineitem.class_id,
                'itemid': lineitem.item_id,
                'taskid': lineitem.task_id,
                'costtypeid': lineitem.cost_type_id,
                'billable': lineitem.billable if configuration.is_journal_credit_billable else None,
                'customfields': {
                   'customfield': [
                    {
                        'customfieldname': 'FYLE_EXPENSE_URL',
                        'customfieldvalue': expense_link
                    },
                   ]
                }
            }

            tax_inclusive_amount, tax_amount = self.get_tax_exclusive_amount(abs(lineitem.amount), general_mappings.default_tax_code_id)

            debit_line = {
                'accountno': lineitem.gl_account_number,
                'currency': journal_entry.currency,
                'amount': round((lineitem.amount - lineitem.tax_amount), 2) if (lineitem.tax_code and lineitem.tax_amount) else tax_inclusive_amount,
                'tr_type': 1,
                'description': lineitem.memo,
                'department': lineitem.department_id,
                'location': lineitem.location_id,
                'projectid': lineitem.project_id,
                'customerid': lineitem.customer_id,
                'vendorid': lineitem.vendor_id,
                'employeeid': lineitem.employee_id,
                'itemid': lineitem.item_id,
                'taskid': lineitem.task_id,
                'costtypeid': lineitem.cost_type_id,
                'classid': lineitem.class_id,
                'billable': lineitem.billable,
                'taxentries': {
                    'taxentry': {
                        'trx_tax': lineitem.tax_amount if (lineitem.tax_code and lineitem.tax_amount) else tax_amount,
                        'detailid': lineitem.tax_code if (lineitem.tax_code and lineitem.tax_amount) else general_mappings.default_tax_code_id,
                    }
                },
                'customfields': {
                   'customfield': [
                    {
                        'customfieldname': 'FYLE_EXPENSE_URL',
                        'customfieldvalue': expense_link
                    },
                   ]
                }
            }

            # case of a refund
            if lineitem.amount < 0:
                amount = abs(lineitem.amount)
                debit_line['amount'] = amount
                credit_line['amount'] = round(amount - abs(lineitem.tax_amount) if (lineitem.tax_code and lineitem.tax_amount) else tax_inclusive_amount, 2)
                debit_line['tr_type'], credit_line['tr_type'] = credit_line['tr_type'], debit_line['tr_type']
                credit_line['taxentries'] = debit_line['taxentries'].copy()
                debit_line.pop('taxentries')

            for dimension in lineitem.user_defined_dimensions:
                for name, value in dimension.items():
                    credit_line[name] = value
                    debit_line[name] = value

            journal_entry_payload.append(credit_line)
            journal_entry_payload.append(debit_line)

        transaction_date = datetime.strptime(journal_entry.transaction_date, '%Y-%m-%dT%H:%M:%S')
        transaction_date = '{0}/{1}/{2}'.format(transaction_date.month, transaction_date.day, transaction_date.year)
        
        
        journal_entry_payload = {
            'recordno': recordno if recordno else None,
            'journal': 'FYLE_JE' if settings.BRAND_ID == 'fyle' else 'EM_JOURNAL',
            'batch_date': transaction_date,
            'batch_title': journal_entry.memo,
            'supdocid': journal_entry.supdoc_id if journal_entry.supdoc_id else None,
            'entries':[
                {
                    'glentry': journal_entry_payload
                }
            ]
        }

        if configuration.import_tax_codes:
            journal_entry_payload.update({
                'taximplications': 'Inbound',
                'taxsolutionid': self.get_tax_solution_id_or_none(journal_entry_lineitems),
            })

        logger.info("| Payload for the journal entry report creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, JOURNAL_ENTRY_PAYLOAD = {}}}".format(self.workspace_id, journal_entry.expense_group.id, journal_entry_payload))
        return journal_entry_payload

    def post_expense_report(self, expense_report: ExpenseReport, expense_report_lineitems: List[ExpenseReportLineitem]):
        """
        Post expense report to Sage Intacct
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

    def post_bill(self, bill: Bill, bill_lineitems: List[BillLineitem]):
        """
        Post expense report to Sage Intacct
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

    def post_journal_entry(self, journal_entry: JournalEntry, journal_entry_lineitems: List[JournalEntryLineitem]):
        """
        Post journal_entry  to Sage Intacct
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

    def get_bill(self, bill_id: str, fields: list = None):
        """
        GET bill from SAGE Intacct
        """
        bill = self.connection.bills.get(field='RECORDNO', value=bill_id, fields=fields)
        return bill

    def get_expense_report(self, expense_report_id: str, fields: list = None):
        """
        GET expense reports from SAGE
        """
        expense_report = self.connection.expense_reports.get(field='RECORDNO', value=expense_report_id, fields=fields)
        return expense_report

    def get_journal_entry(self, journal_entry_id: str, fields: list = None):
        """
        GET journal_entry from SAGE Intacct
        """
        journal_entry = self.connection.journal_entries.get(field='RECORDNO', value=journal_entry_id, fields=fields)
        return journal_entry    

    def post_charge_card_transaction(self, charge_card_transaction: ChargeCardTransaction, \
                                     charge_card_transaction_lineitems: List[ChargeCardTransactionLineitem]):
        """
        Post charge card transaction to Sage Intacct
        """
        configuration = Configuration.objects.get(workspace_id=self.workspace_id)
        try:
            created_charge_card_transaction_payload = self.__construct_charge_card_transaction \
                (charge_card_transaction, charge_card_transaction_lineitems)
            created_charge_card_transaction = self.connection.charge_card_transactions.post \
                (created_charge_card_transaction_payload)
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

    def get_charge_card_transaction(self, charge_card_transaction_id: str, fields: list = None):
        """
        GET charge card transaction from SAGE Intacct
        """
        charge_card_transaction = self.connection.charge_card_transactions.get(
            field='RECORDNO', value=charge_card_transaction_id, fields=fields)
        return charge_card_transaction

    def update_expense_report(self, object_key, supdocid: str):
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: expense report key
        :param supdocid: attachments id
        :return: response from sage intacct
        """
        return self.connection.expense_reports.update_attachment(key=object_key, supdocid=supdocid)

    def update_bill(self, object_key, supdocid: str):
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: expense report key
        :param supdocid: attachments id
        :return: response from sage intacct
        """
        return self.connection.bills.update_attachment(recordno=object_key, supdocid=supdocid)

    def update_charge_card_transaction(self, object_key, supdocid: str):
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: charge card transaction key
        :param supdocid: attachments id
        :return: response from sage intacct
        """
        return self.connection.charge_card_transactions.update_attachment(key=object_key, supdocid=supdocid)

    def update_journal_entry(self, journal_entry: JournalEntry, journal_entry_lineitems: List[JournalEntryLineitem], supdocid: str, recordno : str):
        """
        Map posted attachment with Sage Intacct Object
        :param supdocid: attachments id
        :param recordno: record no
        :return: response from sage intacct
        """
        journal_entry_payload = self.__construct_journal_entry(journal_entry, journal_entry_lineitems, supdocid, recordno)
        return self.connection.journal_entries.update(journal_entry_payload)

    def post_attachments(self, attachments: List[Dict], supdoc_id: str):
        """
        Post attachments to Sage Intacct
        :param attachments: attachment[dict()]
        :param supdoc_id: supdoc id
        :return: supdocid in sage intacct
        """

        if attachments:
            attachment_number = 1
            attachments_list = []
            for attachment in attachments:
                attachment_type = attachment['name'].split('.')[-1]
                attachment_to_append = {
                    'attachmentname': '{0} - {1}'.format(attachment['id'], attachment_number),
                    'attachmenttype': attachment_type,
                    'attachmentdata': attachment['download_url'],
                }

                attachments_list.append(attachment_to_append)
                attachment_number = attachment_number + 1

            first_attachment = [attachments_list[0]]

            data = {
                'supdocid': supdoc_id,
                'supdocfoldername': 'FyleAttachments',
                'attachments': {
                    'attachment': first_attachment
                }
            }

            created_attachment = self.connection.attachments.post(data)

            if len(attachments_list) > 1:
                for attachment in attachments_list[1:]:
                    attachment_data = {
                        'supdocid': supdoc_id,
                        'supdocfoldername': 'FyleAttachments',
                        'attachments': {
                            'attachment': [attachment]
                        }
                    }
                    self.connection.attachments.update(attachment_data)

            if created_attachment['status'] == 'success' and created_attachment['key']:
                return supdoc_id

            return False

    @staticmethod
    def __construct_ap_payment(ap_payment: APPayment, ap_payment_lineitems: List[APPaymentLineitem]) -> Dict:
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

    def post_ap_payment(self, ap_payment: APPayment, ap_payment_lineitems: List[APPaymentLineitem]):
        """
        Post AP Payment to Sage Intacct
        """
        ap_payment_payload = self.__construct_ap_payment(ap_payment, ap_payment_lineitems)
        created_ap_payment = self.connection.ap_payments.post(ap_payment_payload)
        return created_ap_payment

    @staticmethod
    def __construct_sage_intacct_reimbursement(reimbursement: SageIntacctReimbursement,
                                               reimbursement_lineitems: List[SageIntacctReimbursementLineitem]) -> Dict:
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

    def post_sage_intacct_reimbursement(self, reimbursement: SageIntacctReimbursement,
                                        reimbursement_lineitems: List[SageIntacctReimbursementLineitem]):
        """
        Post Reimbursement to Sage Intacct
        """
        reimbursement_payload = self.__construct_sage_intacct_reimbursement(reimbursement, reimbursement_lineitems)
        created_reimbursement = self.connection.reimbursements.post(reimbursement_payload)
        return created_reimbursement
