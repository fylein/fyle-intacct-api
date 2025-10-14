import logging
from datetime import datetime
from unittest import mock

import pytest
from fyle_accounting_mappings.models import CategoryMapping, DestinationAttribute, ExpenseAttribute, Mapping
from sageintacctsdk.exceptions import WrongParamsError

from apps.mappings.models import GeneralMapping
from apps.sage_intacct.models import CostCode, CostType
from apps.sage_intacct.utils import Configuration, SageIntacctConnector, SageIntacctCredential, Workspace
from fyle_intacct_api.utils import invalidate_sage_intacct_credentials
from tests.helper import dict_compare_keys
from tests.test_sageintacct.fixtures import data

logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_sync_employees(mocker, db):
    """
    Test sync employees
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Employees.get_all_generator',
        return_value=data['get_employees']
    )
    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)

    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
    )
    employee_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EMPLOYEE').count()
    assert employee_count == 55

    sage_intacct_connection.sync_employees()

    new_employee_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EMPLOYEE').count()
    assert new_employee_count == 55


def test_post_vendor(mocker, db):
    """
    Test post vendor
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Vendors.get',
        return_value=data['get_vendors']
    )
    mocker.patch(
        'sageintacctsdk.apis.Vendors.post',
        return_value=data['post_vendors']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    vendor = sage_intacct_connection.get_or_create_vendor(vendor_name='test Sharma',email='test@fyle.in', create=True)

    assert vendor.value == 'test Sharma'


def test_sync_vendors(mocker, db):
    """
    Test sync vendors
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Vendors.get_all_generator',
        return_value=data['get_vendors']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    vendor_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    assert vendor_count == 68

    sage_intacct_connection.sync_vendors()

    new_vendor_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    assert new_vendor_count == 68


def test_sync_departments(mocker, db):
    """
    Test sync departments
    """
    workspace_id = 1
    mocker.patch(
        'sageintacctsdk.apis.Departments.count',
        return_value=2
    )
    mocker.patch(
        'sageintacctsdk.apis.Departments.get_all_generator',
        return_value=data['get_departments']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    department_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='DEPARTMENT').count()
    assert department_count == 5

    sage_intacct_connection.sync_departments()

    new_department_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='DEPARTMENT').count()
    assert new_department_count == 5


def test_sync_expense_types(mocker, db):
    """
    Test sync expense types
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.ExpenseTypes.count',
        return_value=5
    )

    mocker.patch(
        'sageintacctsdk.apis.ExpenseTypes.get_all_generator',
        return_value=data['get_expense_types']
    )

    mocker.patch(
        'fyle_integrations_imports.modules.categories.disable_categories'
    )

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    expense_type_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EXPENSE_TYPE').count()
    assert expense_type_count == 8

    sage_intacct_connection.sync_expense_types()

    new_expense_type_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EXPENSE_TYPE').count()
    assert new_expense_type_count == 8


def test_sync_charge_card_accounts(mocker, db):
    """
    Test sync charge card accounts
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.ChargeCardAccounts.get_by_query',
        return_value=data['get_charge_card_accounts']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    charge_card_account_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CHARGE_CARD_NUMBER').count()
    assert charge_card_account_count == 5

    sage_intacct_connection.sync_charge_card_accounts()

    new_charge_card_account_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CHARGE_CARD_NUMBER').count()
    assert new_charge_card_account_count == 5


def test_sync_payment_accounts(mocker, db):
    """
    Test sync payment accounts
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.CheckingAccounts.get_all_generator',
        return_value=data['get_payment_accounts']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    payment_account_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PAYMENT_ACCOUNT').count()
    assert payment_account_count == 7

    sage_intacct_connection.sync_payment_accounts()

    new_payment_account_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PAYMENT_ACCOUNT').count()
    assert new_payment_account_count == 7


def test_sync_projects(mocker, db):
    """
    Test sync projects
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all_generator',
        return_value=data['get_projects']
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=5
    )

    mock = mocker.patch('fyle_integrations_imports.modules.projects.PlatformConnector')
    mocker.patch.object(mock.return_value.projects, 'post_bulk')
    mocker.patch.object(mock.return_value.projects, 'sync')

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    project_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert project_count == 16

    sage_intacct_connection.sync_projects()

    new_project_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert new_project_count == 16


def test_sync_items(mocker, db):
    """
    Test sync items
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Items.get_all_generator',
        return_value=data['get_items']
    )

    mocker.patch(
        'sageintacctsdk.apis.Items.count',
        return_value=5
    )

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    item_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='ITEM').count()
    assert item_count == 8

    sage_intacct_connection.sync_items()

    new_item_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='ITEM').count()
    assert new_item_count == 8


def test_sync_locations(mocker, db):
    """
    Test sync locations
    """
    workspace_id = 1
    mocker.patch(
        'sageintacctsdk.apis.Locations.count',
        return_value=5
    )
    mocker.patch(
        'sageintacctsdk.apis.Locations.get_all_generator',
        return_value=data['get_locations']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    location_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='LOCATION').count()
    assert location_count == 2

    sage_intacct_connection.sync_locations()

    new_location_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='LOCATION').count()
    assert new_location_count == 2


def test_sync_location_entities(mocker, db):
    """
    Test sync location entities
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.LocationEntities.get_all_generator',
        return_value=data['get_location_entities']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    location_entitie_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='LOCATION_ENTITY').count()
    assert location_entitie_count == 10

    sage_intacct_connection.sync_location_entities()

    new_location_entitie_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='LOCATION_ENTITY').count()
    assert new_location_entitie_count == 10


def test_sync_expense_payment_types(mocker, db):
    """
    Test sync expense payment types
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.ExpensePaymentTypes.get_all_generator',
        return_value=data['get_expense_payment_types']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    expense_payment_type_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EXPENSE_PAYMENT_TYPE').count()
    assert expense_payment_type_count == 1

    sage_intacct_connection.sync_expense_payment_types()

    new_expense_payment_type_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EXPENSE_PAYMENT_TYPE').count()
    assert new_expense_payment_type_count == 1


def test_sync_user_defined_dimensions(mocker, db):
    """
    Test sync user defined dimensions
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Dimensions.get_all',
        return_value=data['get_user_defined_dimensions']
    )
    mocker.patch(
        'sageintacctsdk.apis.DimensionValues.get_all',
        return_value=data['get_dimension_value']
    )
    mocker.patch(
        'sageintacctsdk.apis.DimensionValues.count',
        return_value=1
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    user_defined_dimension_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PLACE').count()
    assert user_defined_dimension_count == 0

    sage_intacct_connection.sync_user_defined_dimensions()

    new_user_defined_dimension_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PLACE').count()
    assert new_user_defined_dimension_count == 2


def test_sync_user_defined_dimensions_case_2(mocker, db):
    """
    Test sync user defined dimensions
    Upper Sync limit exceeded
    """
    workspace_id = 1
    Workspace.objects.filter(id=workspace_id).update(created_at=datetime.now())

    mocker.patch(
        'sageintacctsdk.apis.Dimensions.get_all',
        return_value=data['get_user_defined_dimensions_case_2']
    )
    mocker.patch(
        'sageintacctsdk.apis.DimensionValues.count',
        return_value=5001
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    user_defined_dimension_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='UDD').count()
    assert user_defined_dimension_count == 0

    sage_intacct_connection.sync_user_defined_dimensions()

    new_user_defined_dimension_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='UDD').count()
    assert new_user_defined_dimension_count == 0


def test_construct_bill(create_bill, db):
    """
    Test construct bill
    """
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    bill, bill_lineitems = create_bill
    bill_lineitems[0].user_defined_dimensions = [{'CLASS': 'sample'}]

    bill_lineitems[0].amount = -abs(bill_lineitems[0].amount)
    bill_object = sage_intacct_connection._SageIntacctConnector__construct_bill(bill=bill,bill_lineitems=bill_lineitems)

    assert dict_compare_keys(bill_object, data['bill_payload']) == [], 'construct bill_payload entry api return diffs in keys'

    bill_lineitems[0].amount = abs(bill_lineitems[0].amount)
    bill_object = sage_intacct_connection._SageIntacctConnector__construct_bill(bill=bill,bill_lineitems=bill_lineitems)

    assert dict_compare_keys(bill_object, data['bill_payload']) == [], 'construct bill_payload entry api return diffs in keys'


def test_construct_expense_report(create_expense_report, db):
    """
    Test construct expense report
    """
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    expense_report,expense_report_lineitems = create_expense_report
    expense_report_lineitems[0].user_defined_dimensions = [{'CLASS': 'sample'}]
    expense_report_object = sage_intacct_connection._SageIntacctConnector__construct_expense_report(expense_report=expense_report, expense_report_lineitems=expense_report_lineitems)

    assert dict_compare_keys(expense_report_object, data['expense_report_payload']) == [], 'construct expense_report_payload entry api return diffs in keys'


def test_construct_charge_card_transaction(create_charge_card_transaction, db):
    """
    Test construct charge card transaction
    """
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    charge_card_transaction,charge_card_transaction_lineitems = create_charge_card_transaction
    charge_card_transaction_lineitems[0].user_defined_dimensions = [{'CLASS': 'sample'}, {'USERDIM1': 'C000013'}]
    charge_card_transaction_object = sage_intacct_connection._SageIntacctConnector__construct_charge_card_transaction(charge_card_transaction=charge_card_transaction, charge_card_transaction_lineitems=charge_card_transaction_lineitems)

    assert dict_compare_keys(charge_card_transaction_object, data['charge_card_transaction_payload']) == [], 'construct credit_card_purchase_payload entry api return diffs in keys'


def test_construct_journal_entry(create_journal_entry, db):
    """
    Test construct journal entry
    """
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    general_settings = Configuration.objects.filter(workspace_id=workspace_id).first()
    general_settings.import_tax_codes = True
    general_settings.save()

    general_mappings = GeneralMapping.objects.filter(workspace_id=workspace_id).first()
    general_mappings.default_tax_code_id = 4
    general_mappings.save()

    journal_entry,journal_entry_lineitems = create_journal_entry
    journal_entry_lineitems[0].user_defined_dimensions = [{'CLASS': 'sample'}]

    journal_entry_lineitems[0].amount = -abs(journal_entry_lineitems[0].amount)
    journal_entry_object = sage_intacct_connection._SageIntacctConnector__construct_journal_entry(journal_entry=journal_entry, journal_entry_lineitems=journal_entry_lineitems)

    assert dict_compare_keys(journal_entry_object, data['journal_entry_payload_refund']) == [], 'construct journal entry api return diffs in keys'

    journal_entry_lineitems[0].amount = abs(journal_entry_lineitems[0].amount)
    journal_entry_object = sage_intacct_connection._SageIntacctConnector__construct_journal_entry(journal_entry=journal_entry, journal_entry_lineitems=journal_entry_lineitems)

    assert dict_compare_keys(journal_entry_object, data['journal_entry_payload']) == [], 'construct journal entry api return diffs in keys'

    journal_entry_lineitems[0].amount = abs(journal_entry_lineitems[0].amount)
    journal_entry_object = sage_intacct_connection._SageIntacctConnector__construct_journal_entry(journal_entry=journal_entry, journal_entry_lineitems=journal_entry_lineitems)

    assert dict_compare_keys(journal_entry_object, data['journal_entry_re_payload']) == [], 'construct journal entry api return diffs in keys'


def test_construct_sage_intacct_reimbursement(create_sage_intacct_reimbursement, db):
    """
    Test construct sage intacct reimbursement
    """
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    sage_intacct_reimbursement,sage_intacct_reimbursement_lineitems = create_sage_intacct_reimbursement
    sage_intacct_reimbursement_object = sage_intacct_connection._SageIntacctConnector__construct_sage_intacct_reimbursement(reimbursement=sage_intacct_reimbursement,reimbursement_lineitems=sage_intacct_reimbursement_lineitems)

    assert dict_compare_keys(sage_intacct_reimbursement_object, data['sage_intacct_reimbursement_payload']) == [], 'construct expense api return diffs in keys'


def test_construct_ap_payment(create_ap_payment, db):
    """
    Test construct ap payment
    """
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    ap_payment,ap_payment_lineitems = create_ap_payment
    ap_payment_object = sage_intacct_connection._SageIntacctConnector__construct_ap_payment(ap_payment=ap_payment,ap_payment_lineitems=ap_payment_lineitems)

    assert dict_compare_keys(ap_payment_object, data['ap_payment_payload']) == [], 'construct ap_payment api return diffs in keys'


def test_get_bill(mocker, db):
    """
    Test get bill
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Bills.get',
        return_value=data['get_bill']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    bill = sage_intacct_connection.get_bill(1, ['RECORD_URL'])

    assert dict_compare_keys(bill, data['get_bill']) == []


def test_get_tax_solution_id_or_none(mocker, db, create_expense_report):
    """
    Test get tax solution id or none
    """
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    _, expense_report_lineitems = create_expense_report
    tax_solution_id = sage_intacct_connection.get_tax_solution_id_or_none(expense_report_lineitems)
    assert tax_solution_id == 'Australia - GST'

    expense_report_lineitems[0].tax_code = 'No Input VAT'
    tax_solution_id = sage_intacct_connection.get_tax_solution_id_or_none(expense_report_lineitems)
    assert tax_solution_id == 'South Africa - VAT'

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.location_entity_id = 20600
    general_mappings.save()

    tax_solution_id = sage_intacct_connection.get_tax_solution_id_or_none(expense_report_lineitems)
    assert tax_solution_id == None


def test_get_tax_exclusive_amount(db):
    """
    Test get tax exclusive amount
    """
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)
    tax_exclusive_amount, _ = sage_intacct_connection.get_tax_exclusive_amount(100, 4)

    assert tax_exclusive_amount == 100.0


def test_sync_tax_details(mocker, db):
    """
    Test sync tax details
    """
    workspace_id = 1
    mocker.patch(
        'sageintacctsdk.apis.TaxDetails.count',
        return_value=5
    )
    mocker.patch(
        'sageintacctsdk.apis.TaxDetails.get_all_generator',
        return_value=data['get_tax_details']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    tax_code_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_CODE').count()
    assert tax_code_count == 0

    sage_intacct_connection.sync_tax_details()

    new_tax_code_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_CODE').count()
    assert new_tax_code_count == 0


def tests_sync_accounts(mocker, db):
    """
    Test sync accounts
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Accounts.count',
        return_value=5
    )
    mocker.patch(
        'sageintacctsdk.apis.Accounts.get_all_generator',
        return_value=data['get_accounts']
    )

    mock = mocker.patch('fyle_integrations_imports.modules.categories.PlatformConnector')
    mocker.patch.object(mock.return_value.categories, 'post_bulk')

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    account_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='ACCOUNT').count()
    assert account_count == 170

    sage_intacct_connection.sync_accounts()

    new_account_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='ACCOUNT').count()
    assert new_account_count == 170


def test_sync_classes(mocker, db):
    """
    Test sync classes
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Classes.get_all_generator',
        return_value=data['get_classes']
    )
    # Patch the mock data to include 'STATUS'
    for class_list in data['get_classes']:
        for class_dict in class_list:
            class_dict['STATUS'] = 'active'

    mocker.patch(
        'sageintacctsdk.apis.Classes.count',
        return_value=5
    )

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    class_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CLASS').count()
    assert class_count == 6

    sage_intacct_connection.sync_classes()

    new_class_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CLASS').count()
    assert new_class_count == 6


def test_sync_customers(mocker, db):
    """
    Test sync customers
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Customers.get_all_generator',
        return_value=data['get_customers']
    )
    # Patch the mock data to include 'STATUS'
    for customer_list in data['get_customers']:
        for customer_dict in customer_list:
            customer_dict['STATUS'] = 'active'

    mocker.patch(
        'sageintacctsdk.apis.Customers.count',
        return_value=5
    )

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    customer_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CUSTOMER').count()
    assert customer_count == 526

    sage_intacct_connection.sync_customers()

    new_customer_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CUSTOMER').count()
    assert new_customer_count == 526


def test_get_dimensions_values_without_allocation(mocker, db):
    """
    Test __get_dimensions_values method without allocation_id
    """
    workspace_id = 1

    # Create a mock lineitem without allocation_id
    lineitem = type('MockLineitem', (), {
        'project_id': 'PROJECT_123',
        'location_id': 'LOCATION_456',
        'department_id': 'DEPT_789',
        'class_id': 'CLASS_001',
        'customer_id': 'CUSTOMER_002',
        'item_id': 'ITEM_003',
        'task_id': 'TASK_004',
        'cost_type_id': 'COST_TYPE_005',
        'allocation_id': None,
        'user_defined_dimensions': []
    })()

    # Mock Fernet to avoid encryption key issues
    mocker.patch('apps.sage_intacct.utils.Fernet')

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
    )

    # Call the private method
    result = sage_intacct_connection._SageIntacctConnector__get_dimensions_values(lineitem, workspace_id)

    # Verify all dimensions are preserved
    expected_result = {
        'project_id': 'PROJECT_123',
        'location_id': 'LOCATION_456',
        'department_id': 'DEPT_789',
        'class_id': 'CLASS_001',
        'customer_id': 'CUSTOMER_002',
        'item_id': 'ITEM_003',
        'task_id': 'TASK_004',
        'cost_type_id': 'COST_TYPE_005'
    }

    assert result == expected_result


def test_get_dimensions_values_with_allocation(mocker, db):
    """
    Test __get_dimensions_values method with allocation_id
    """
    workspace_id = 1

    # Create allocation destination attribute
    allocation_detail = {
        'LOCATIONID': 'ALLOC_LOCATION',
        'DEPARTMENTID': 'ALLOC_DEPT',
        'PROJECTID': 'ALLOC_PROJECT'
    }

    DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='ALLOCATION',
        value='ALLOCATION_123',
        destination_id='ALLOCATION_123',
        display_name='Test Allocation',
        detail=allocation_detail
    )

    # Create a mock lineitem with allocation_id
    lineitem = type('MockLineitem', (), {
        'project_id': 'PROJECT_123',
        'location_id': 'LOCATION_456',
        'department_id': 'DEPT_789',
        'class_id': 'CLASS_001',
        'customer_id': 'CUSTOMER_002',
        'item_id': 'ITEM_003',
        'task_id': 'TASK_004',
        'cost_type_id': 'COST_TYPE_005',
        'allocation_id': 'ALLOCATION_123',
        'user_defined_dimensions': [
            {'LOCATIONID': 'UDD_LOCATION'},
            {'DEPARTMENTID': 'UDD_DEPT'},
            {'CUSTOM_FIELD': 'CUSTOM_VALUE'}
        ]
    })()

    # Mock Fernet to avoid encryption key issues
    mocker.patch('apps.sage_intacct.utils.Fernet')

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
    )

    # Call the private method
    result = sage_intacct_connection._SageIntacctConnector__get_dimensions_values(lineitem, workspace_id)

    # Verify dimensions affected by allocation are set to None
    expected_result = {
        'project_id': None,  # Should be None due to PROJECTID in allocation
        'location_id': None,  # Should be None due to LOCATIONID in allocation
        'department_id': None,  # Should be None due to DEPARTMENTID in allocation
        'class_id': 'CLASS_001',  # Should remain unchanged
        'customer_id': 'CUSTOMER_002',  # Should remain unchanged
        'item_id': 'ITEM_003',  # Should remain unchanged
        'task_id': 'TASK_004',  # Should remain unchanged
        'cost_type_id': 'COST_TYPE_005'  # Should remain unchanged
    }

    assert result == expected_result

    # Verify user_defined_dimensions are filtered
    expected_filtered_dimensions = [
        {'CUSTOM_FIELD': 'CUSTOM_VALUE'}  # Only non-allocation dimensions should remain
    ]

    assert lineitem.user_defined_dimensions == expected_filtered_dimensions


def test_get_dimensions_values_with_partial_allocation(mocker, db):
    """
    Test __get_dimensions_values method with allocation_id containing only some dimensions
    """
    workspace_id = 1

    # Create allocation destination attribute with only some dimensions
    allocation_detail = {
        'CLASSID': 'ALLOC_CLASS',
        'CUSTOMERID': 'ALLOC_CUSTOMER'
    }

    DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='ALLOCATION',
        value='PARTIAL_ALLOCATION',
        destination_id='PARTIAL_ALLOCATION',
        display_name='Partial Allocation',
        detail=allocation_detail
    )

    # Create a mock lineitem with allocation_id
    lineitem = type('MockLineitem', (), {
        'project_id': 'PROJECT_123',
        'location_id': 'LOCATION_456',
        'department_id': 'DEPT_789',
        'class_id': 'CLASS_001',
        'customer_id': 'CUSTOMER_002',
        'item_id': 'ITEM_003',
        'task_id': 'TASK_004',
        'cost_type_id': 'COST_TYPE_005',
        'allocation_id': 'PARTIAL_ALLOCATION',
        'user_defined_dimensions': [
            {'CLASSID': 'UDD_CLASS'},
            {'OTHER_FIELD': 'OTHER_VALUE'}
        ]
    })()

    # Mock Fernet to avoid encryption key issues
    mocker.patch('apps.sage_intacct.utils.Fernet')

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
    )

    # Call the private method
    result = sage_intacct_connection._SageIntacctConnector__get_dimensions_values(lineitem, workspace_id)

    # Verify only dimensions in allocation are set to None
    expected_result = {
        'project_id': 'PROJECT_123',  # Should remain unchanged
        'location_id': 'LOCATION_456',  # Should remain unchanged
        'department_id': 'DEPT_789',  # Should remain unchanged
        'class_id': None,  # Should be None due to CLASSID in allocation
        'customer_id': None,  # Should be None due to CUSTOMERID in allocation
        'item_id': 'ITEM_003',  # Should remain unchanged
        'task_id': 'TASK_004',  # Should remain unchanged
        'cost_type_id': 'COST_TYPE_005'  # Should remain unchanged
    }

    assert result == expected_result

    # Verify user_defined_dimensions are filtered correctly
    expected_filtered_dimensions = [
        {'OTHER_FIELD': 'OTHER_VALUE'}  # Only non-allocation dimensions should remain
    ]

    assert lineitem.user_defined_dimensions == expected_filtered_dimensions


def test_get_dimensions_values_with_empty_allocation(mocker, db):
    """
    Test __get_dimensions_values method with allocation_id but empty allocation details
    """
    workspace_id = 1

    # Create allocation destination attribute with empty details
    DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='ALLOCATION',
        value='EMPTY_ALLOCATION',
        destination_id='EMPTY_ALLOCATION',
        display_name='Empty Allocation',
        detail={}
    )

    # Create a mock lineitem with allocation_id
    lineitem = type('MockLineitem', (), {
        'project_id': 'PROJECT_123',
        'location_id': 'LOCATION_456',
        'department_id': 'DEPT_789',
        'class_id': 'CLASS_001',
        'customer_id': 'CUSTOMER_002',
        'item_id': 'ITEM_003',
        'task_id': 'TASK_004',
        'cost_type_id': 'COST_TYPE_005',
        'allocation_id': 'EMPTY_ALLOCATION',
        'user_defined_dimensions': [
            {'CUSTOM_FIELD': 'CUSTOM_VALUE'}
        ]
    })()

    # Mock Fernet to avoid encryption key issues
    mocker.patch('apps.sage_intacct.utils.Fernet')

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
    )

    # Call the private method
    result = sage_intacct_connection._SageIntacctConnector__get_dimensions_values(lineitem, workspace_id)

    # Verify all dimensions remain unchanged since allocation is empty
    expected_result = {
        'project_id': 'PROJECT_123',
        'location_id': 'LOCATION_456',
        'department_id': 'DEPT_789',
        'class_id': 'CLASS_001',
        'customer_id': 'CUSTOMER_002',
        'item_id': 'ITEM_003',
        'task_id': 'TASK_004',
        'cost_type_id': 'COST_TYPE_005'
    }

    assert result == expected_result

    # Verify user_defined_dimensions remain unchanged
    expected_filtered_dimensions = [
        {'CUSTOM_FIELD': 'CUSTOM_VALUE'}
    ]

    assert lineitem.user_defined_dimensions == expected_filtered_dimensions


def test_get_dimensions_values_with_all_allocation_dimensions(mocker, db):
    """
    Test __get_dimensions_values method with allocation containing all possible dimensions
    """
    workspace_id = 1

    # Create allocation destination attribute with all dimensions
    allocation_detail = {
        'LOCATIONID': 'ALLOC_LOCATION',
        'DEPARTMENTID': 'ALLOC_DEPT',
        'CLASSID': 'ALLOC_CLASS',
        'CUSTOMERID': 'ALLOC_CUSTOMER',
        'ITEMID': 'ALLOC_ITEM',
        'TASKID': 'ALLOC_TASK',
        'COSTTYPEID': 'ALLOC_COST_TYPE',
        'PROJECTID': 'ALLOC_PROJECT'
    }

    DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='ALLOCATION',
        value='FULL_ALLOCATION',
        destination_id='FULL_ALLOCATION',
        display_name='Full Allocation',
        detail=allocation_detail
    )

    # Create a mock lineitem with allocation_id
    lineitem = type('MockLineitem', (), {
        'project_id': 'PROJECT_123',
        'location_id': 'LOCATION_456',
        'department_id': 'DEPT_789',
        'class_id': 'CLASS_001',
        'customer_id': 'CUSTOMER_002',
        'item_id': 'ITEM_003',
        'task_id': 'TASK_004',
        'cost_type_id': 'COST_TYPE_005',
        'allocation_id': 'FULL_ALLOCATION',
        'user_defined_dimensions': [
            {'PROJECTID': 'UDD_PROJECT'},
            {'LOCATIONID': 'UDD_LOCATION'},
            {'CUSTOM_FIELD': 'CUSTOM_VALUE'}
        ]
    })()

    # Mock Fernet to avoid encryption key issues
    mocker.patch('apps.sage_intacct.utils.Fernet')

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
    )

    # Call the private method
    result = sage_intacct_connection._SageIntacctConnector__get_dimensions_values(lineitem, workspace_id)

    # Verify all dimensions are set to None due to allocation
    expected_result = {
        'project_id': None,
        'location_id': None,
        'department_id': None,
        'class_id': None,
        'customer_id': None,
        'item_id': None,
        'task_id': None,
        'cost_type_id': None
    }

    assert result == expected_result

    # Verify user_defined_dimensions are filtered to only non-allocation dimensions
    expected_filtered_dimensions = [
        {'CUSTOM_FIELD': 'CUSTOM_VALUE'}
    ]

    assert lineitem.user_defined_dimensions == expected_filtered_dimensions


def test_get_dimensions_values_with_missing_allocation(mocker, db):
    """
    Test __get_dimensions_values method with allocation_id that doesn't exist in DestinationAttribute
    This should raise an AttributeError when trying to access .detail on None
    """
    workspace_id = 1

    # Create a mock lineitem with allocation_id that doesn't exist
    lineitem = type('MockLineitem', (), {
        'project_id': 'PROJECT_123',
        'location_id': 'LOCATION_456',
        'department_id': 'DEPT_789',
        'class_id': 'CLASS_001',
        'customer_id': 'CUSTOMER_002',
        'item_id': 'ITEM_003',
        'task_id': 'TASK_004',
        'cost_type_id': 'COST_TYPE_005',
        'allocation_id': 'NONEXISTENT_ALLOCATION',
        'user_defined_dimensions': []
    })()

    # Mock Fernet to avoid encryption key issues
    mocker.patch('apps.sage_intacct.utils.Fernet')

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
    )

    # Call the private method and expect an AttributeError
    with pytest.raises(AttributeError):
        sage_intacct_connection._SageIntacctConnector__get_dimensions_values(lineitem, workspace_id)


def test_post_bill_exception(mocker, db, create_bill):
    """
    Test post bill exception
    """
    mocker.patch(
        'sageintacctsdk.apis.Bills.post',
        return_value=data['bill_response']
    )
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    bill, bill_lineitems = create_bill

    workspace_general_setting = Configuration.objects.get(workspace_id=workspace_id)
    workspace_general_setting.change_accounting_period = True
    workspace_general_setting.save()

    with mock.patch('sageintacctsdk.apis.Bills.post') as mock_call:
        mock_call.return_value = data['bill_response']
        mock_call.side_effect = [WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': 'Date must be on or after', 'correction': ''}],
                'type': 'Invalid_params'
            }), None]
        sage_intacct_connection.post_bill(bill, bill_lineitems)


def test_post_sage_intacct_reimbursement_exception(mocker, db, create_sage_intacct_reimbursement):
    """
    Test post sage intacct reimbursement exception
    """
    mocker.patch(
        'sageintacctsdk.apis.Reimbursements.post',
        return_value=data['reimbursements']
    )
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    sage_intacct_reimbursement, sage_intacct_reimbursement_lineitems = create_sage_intacct_reimbursement

    sage_intacct_connection.post_sage_intacct_reimbursement(sage_intacct_reimbursement, sage_intacct_reimbursement_lineitems)


def test_post_expense_report_exception(mocker, db, create_expense_report):
    """
    Test post expense report exception
    """
    mocker.patch(
        'sageintacctsdk.apis.ExpenseReports.post',
        return_value=data['expense_report_post_response']
    )
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    expense_report, expense_report_lineitems = create_expense_report

    workspace_general_setting = Configuration.objects.get(workspace_id=workspace_id)
    workspace_general_setting.change_accounting_period = True
    workspace_general_setting.save()

    try:
        with mock.patch('sageintacctsdk.apis.ExpenseReports.post') as mock_call:
            mock_call.side_effect = [WrongParamsError(
                msg = {
                    'Message': 'Invalid parametrs'
                }, response={
                    'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': 'Date must be on or after', 'correction': ''}],
                    'type': 'Invalid_params'
                }), None]
            sage_intacct_connection.post_expense_report(expense_report, expense_report_lineitems)
    except Exception:
        logger.info("Account period error")


def test_post_charge_card_transaction_exception(mocker, db, create_charge_card_transaction):
    """
    Test post charge card transaction exception
    """
    mocker.patch(
        'sageintacctsdk.apis.ChargeCardTransactions.post',
        return_value=data['credit_card_response']
    )
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    charge_card_transaction, charge_card_transaction_lineitems = create_charge_card_transaction

    workspace_general_setting = Configuration.objects.get(workspace_id=workspace_id)
    workspace_general_setting.change_accounting_period = True
    workspace_general_setting.save()

    try:
        with mock.patch('sageintacctsdk.apis.ChargeCardTransactions.post') as mock_call:
            mock_call.side_effect = [WrongParamsError(
                msg = {
                    'Message': 'Invalid parametrs'
                }, response={
                    'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': 'Date must be on or after', 'correction': ''}],
                    'type': 'Invalid_params'
                }), None]
            sage_intacct_connection.post_charge_card_transaction(charge_card_transaction, charge_card_transaction_lineitems)
    except Exception:
        logger.info("Account period error")


def test_post_journal_entry_exception(mocker, db, create_journal_entry):
    """
    Test post journal entry exception
    """
    mocker.patch(
        'sageintacctsdk.apis.JournalEntries.post',
        return_value=data['journal_entry_response']
    )
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    journal_entry, journal_entry_lineitems = create_journal_entry

    workspace_general_setting = Configuration.objects.get(workspace_id=workspace_id)
    workspace_general_setting.change_accounting_period = True
    workspace_general_setting.save()

    try:
        with mock.patch('sageintacctsdk.apis.JournalEntries.post') as mock_call:
            mock_call.side_effect = [WrongParamsError(
                msg={
                    'Message': 'Invalid parametrs'
                }, response={
                    'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': 'Date must be on or after', 'correction': ''}],
                    'type': 'Invalid_params'
                }), None]
            sage_intacct_connection.post_journal_entry(journal_entry, journal_entry_lineitems)
    except Exception:
        logger.info("Account period error")


def test_post_ap_payment(mocker, db, create_ap_payment):
    """
    Test post ap payment
    """
    mocker.patch(
        'sageintacctsdk.apis.APPayments.post',
        return_value=data['reimbursements']
    )
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    ap_payment, ap_payment_lineitems = create_ap_payment

    sage_intacct_connection.post_ap_payment(ap_payment, ap_payment_lineitems)


def test_post_attachments(mocker, db):
    """
    Test post attachments
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Attachments.post',
        return_value={'status': 'success', 'key': '3032'}
    )

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    supdoc_id = sage_intacct_connection.post_attachments([{'download_url': 'sdfghj', 'name': 'ert.sdf.sdf', 'id': 'dfgh'}], 'asd', 1)

    assert supdoc_id == 'asd'


def test_post_attachments_2(mocker, db):
    """
    Test post attachments
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Attachments.post',
        return_value={'status': 'success', 'key': '3032'}
    )

    mocker.patch(
        'sageintacctsdk.apis.Attachments.update',
        return_value={'status': 'success', 'key': '3032'}
    )

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    attachment_1 = [
        {'download_url': 'sdfghj', 'name': 'ert.sdf.sdf', 'id': 'dfgh'}
    ]
    supdoc_id = sage_intacct_connection.post_attachments(attachment_1, 'asd', 1)
    assert supdoc_id == 'asd'

    attachment_2 = [
        {'download_url': 'abcd', 'name': 'abc.abc.abc', 'id': 'abc'}
    ]
    supdoc_id = sage_intacct_connection.post_attachments(attachment_2, 'asd', 2)
    assert supdoc_id == False


def test_get_expense_link(mocker, db, create_journal_entry):
    """
    Test get expense link
    """
    workspace_id = 1

    workspace = Workspace.objects.get(id=workspace_id)
    workspace.cluster_domain = ''
    workspace.save()

    journal_entry, journal_entry_lineitems = create_journal_entry

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    expense_link = sage_intacct_connection.get_expense_link(journal_entry_lineitems[0])
    assert expense_link == 'None/app/admin/#/company_expenses?txnId=txCqLqsEnAjf&org_id=or79Cob97KSh'


def test_get_or_create_vendor(mocker, db):
    """
    Test get or create vendor
    """
    workspace_id = 1
    get_call_mock = mocker.patch(
        'sageintacctsdk.apis.Vendors.get',
        return_value={'vendor': data['get_vendor'], '@totalcount': 2}
    )
    post_call_mock = mocker.patch(
        'sageintacctsdk.apis.Vendors.post',
        return_value=data['post_vendors']
    )

    employee_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    assert employee_count == 68

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    sage_intacct_connection.get_or_create_vendor('Ashwin', 'ashwin.t@fyle.in', False)

    new_employee_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    assert new_employee_count == 68

    new_vendor = DestinationAttribute.objects.create(
        attribute_type='VENDOR',
        active=True,
        workspace_id=workspace_id,
        value='Already existing vendor in DB',
        destination_id='summaaaaaaa'
    )

    vendor = sage_intacct_connection.get_or_create_vendor('Already existing vendor in DB', 'ashwin.t@fyle.in', False)

    assert vendor.id == new_vendor.id
    assert vendor.value == 'Already existing vendor in DB'

    get_call_mock.return_value = {'VENDOR': data['get_vendor'], '@totalcount': 2}

    vendor = sage_intacct_connection.get_or_create_vendor('Non existing vendor in DB', 'ashwin.t@fyle.in', False)

    assert vendor is None

    # case insensitive search in db
    vendor_from_db = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').first()
    vendor_from_db.value = 'already Existing VENDOR iN Db UsE aLl CaSeS'
    vendor_from_db.active = True
    vendor_from_db.save()

    assert DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR', value='already Existing VENDOR iN Db UsE aLl CaSeS').exists() is True
    vendor_to_create = 'Already eXisting VeNdor In dB UsE aLl caSES'
    vendor = sage_intacct_connection.get_or_create_vendor(vendor_to_create, create=True)

    assert vendor.value == vendor_from_db.value
    assert vendor.id == vendor_from_db.id

    get_call_mock.return_value = {}

    new_post_vendors_data = data['post_vendors']
    new_post_vendors_data['data']['vendor']['NAME'] = 'non exiSting VENDOR iN intacct UsE aLl CaSeS'
    new_post_vendors_data['data']['vendor']['VENDORID'] = 'non exiSting VENDOR iN intacct UsE aLl CaSeS'

    post_call_mock.return_value = new_post_vendors_data

    vendor = sage_intacct_connection.get_or_create_vendor('non exiSting VENDOR iN intacct UsE aLl CaSeS', create=True)
    assert vendor.destination_id == 'non exiSting VENDOR iN intacct UsE aLl CaSeS'


def test_get_or_create_employee(mocker, db):
    """
    Test get or create employee
    """
    workspace_id = 1
    mocker.patch(
        'sageintacctsdk.apis.Employees.get',
        return_value={'employee': data['get_employee'], '@totalcount': 2}
    )
    mocker.patch(
        'sageintacctsdk.apis.Employees.post',
        return_value={'data': {'employee': data['get_employee'][0]}}
    )

    employee_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EMPLOYEE').count()
    assert employee_count == 55

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    employee = ExpenseAttribute.objects.filter(value='ashwin.t@fyle.in').first()
    sage_intacct_connection.get_or_create_employee(employee)

    new_employee_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EMPLOYEE').count()
    assert new_employee_count == 55


def test_sanitize_vendor_name(db):
    """
    Test sanitize vendor name
    """
    workspace_id = 1
    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)

    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
    )

    # Test case 1: Vendor name with special characters
    vendor_name = "ABC@123"
    expected_output = "ABC123"
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 2: Vendor name without any special characters
    vendor_name = "VendorName"
    expected_output = "VendorName"
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 3: Vendor name with multiple special characters
    vendor_name = "Vendor@Name!123"
    expected_output = "VendorName123"
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 4: Vendor name with special characters and spaces
    vendor_name = "Vendor Name @ 123"
    expected_output = "Vendor Name 123"
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 5: Vendor name with special characters and numbers
    vendor_name = "Vendor@123"
    expected_output = "Vendor123"
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 6: Vendor name with special characters and uppercase letters
    vendor_name = "@ABC~!@#$%^&*()_+=|"
    expected_output = "ABC"
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 7: Vendor name None
    vendor_name = None
    expected_output = None
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 8: Vendor name with only special characters
    vendor_name = "@#$%^&*()"
    expected_output = None
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 9: Vendor name with spaces only
    vendor_name = "     "
    expected_output = None
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 10: Vendor name with leading and trailing special characters
    vendor_name = "@VendorName@"
    expected_output = "VendorName"
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 11: Vendor name that is an empty string
    vendor_name = ""
    expected_output = None
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output

    # Test case 12: Vendor name with tabs and newlines
    vendor_name = "Vendor\tName\n123"
    expected_output = "Vendor Name 123"
    assert sage_intacct_connection.sanitize_vendor_name(vendor_name) == expected_output


def test_sync_allocations(mocker, db):
    """
    Test sync allocations
    """
    workspace_id = 1

    def mock_allocation_entry_generator(field, value):
        for allocation_entry_list in data['allocation_entries']:
            if allocation_entry_list and allocation_entry_list[0]['ALLOCATIONID'] == value:
                yield allocation_entry_list

    def mock_allocations_generator(field, value, updated_at=None):
        yield data['allocations']

    mocker.patch(
        'sageintacctsdk.apis.AllocationEntry.get_all_generator',
        side_effect=mock_allocation_entry_generator
    )

    mocker.patch(
        'sageintacctsdk.apis.Allocations.get_all_generator',
        side_effect = mock_allocations_generator
    )

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    sage_intacct_connection.sync_allocations()

    allocation_attributes = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='ALLOCATION')

    assert allocation_attributes.count() == 2

    for allocation_attribute in allocation_attributes:
        if allocation_attribute.value == 'RENT':
            assert set(allocation_attribute.detail.keys()) == {'LOCATIONID'}
        else:
            assert set(allocation_attribute.detail.keys()) == {'LOCATIONID', 'GLDIMWHAT_IS_NILESH_PANT'}


def test_skip_sync_attributes(mocker, db):
    """
    Test skip sync attributes
    """
    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=25001
    )
    mocker.patch(
        'sageintacctsdk.apis.Classes.count',
        return_value=1001
    )
    mocker.patch(
        'sageintacctsdk.apis.Accounts.count',
        return_value=2001
    )
    mocker.patch(
        'sageintacctsdk.apis.Locations.count',
        return_value=1001
    )
    mocker.patch(
        'sageintacctsdk.apis.Departments.count',
        return_value=1001
    )
    mocker.patch(
        'sageintacctsdk.apis.Customers.count',
        return_value=10001
    )
    mocker.patch(
        'sageintacctsdk.apis.Vendors.count',
        return_value=20001
    )

    mocker.patch(
        'sageintacctsdk.apis.TaxDetails.count',
        return_value=201
    )

    mocker.patch(
        'sageintacctsdk.apis.CostTypes.count',
        return_value=500001
    )

    mocker.patch(
        'sageintacctsdk.apis.ExpenseTypes.count',
        return_value=1001
    )

    today = datetime.today()
    Workspace.objects.filter(id=1).update(created_at=today)
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=1)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=1)

    Mapping.objects.filter(workspace_id=1).delete()
    CategoryMapping.objects.filter(workspace_id=1).delete()

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT').delete()

    sage_intacct_connection.sync_projects()

    new_project_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT').count()
    assert new_project_count == 0

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='CLASS').delete()

    sage_intacct_connection.sync_classes()

    classifications = DestinationAttribute.objects.filter(attribute_type='CLASS', workspace_id=1).count()
    assert classifications == 0

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='ACCOUNT').delete()

    sage_intacct_connection.sync_accounts()

    new_project_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='ACCOUNT').count()
    assert new_project_count == 0

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='LOCATION').delete()

    sage_intacct_connection.sync_locations()

    new_project_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='LOCATION').count()
    assert new_project_count == 0

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='DEPARTMENT').delete()

    sage_intacct_connection.sync_departments()

    new_project_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='DEPARTMENT').count()
    assert new_project_count == 0

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='CUSTOMER').delete()

    sage_intacct_connection.sync_customers()

    new_project_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='CUSTOMER').count()
    assert new_project_count == 0

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='TAX_DETAIL').delete()

    sage_intacct_connection.sync_tax_details()

    new_project_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='TAX_DETAIL').count()
    assert new_project_count == 0

    CostType.objects.filter(workspace_id=1).delete()

    sage_intacct_connection.sync_cost_types()

    new_project_count = CostType.objects.filter(workspace_id=1).count()
    assert new_project_count == 0

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='EXPENSE_TYPE').delete()

    sage_intacct_connection.sync_expense_types()

    new_project_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='EXPENSE_TYPE').count()
    assert new_project_count == 0


def test_sync_cost_codes(db, mocker, create_dependent_field_setting):
    """
    Test sync cost codes
    """
    workspace_id = 1

    sage_intacct_mock = mocker.patch('sageintacctsdk.apis.Tasks.count')
    sage_intacct_mock.return_value = 1

    data = [[
        {'RECORDNO': '38', 'TASKID': '111', 'PARENTKEY': None, 'PARENTID': None, 'NAME': 'HrishabhCostCode', 'PARENTTASKNAME': None, 'PROJECTKEY': '172', 'PROJECTID': '1171', 'PROJECTNAME': 'Sage Project 10', 'ITEMKEY': None, 'ITEMID': None, 'ITEMNAME': None, 'DESCRIPTION': None, 'BILLABLE': 'false', 'TASKNO': None, 'TASKSTATUS': 'In Progress', 'CLASSID': None, 'CLASSNAME': None, 'CLASSKEY': None, 'ROOTPARENTKEY': '38', 'ROOTPARENTID': '111', 'ROOTPARENTNAME': 'HrishabhCostType_v3'},
        {'RECORDNO': '39', 'TASKID': '111', 'PARENTKEY': None, 'PARENTID': None, 'NAME': 'HrishabhCostCode', 'PARENTTASKNAME': None, 'PROJECTKEY': '173', 'PROJECTID': '1172', 'PROJECTNAME': 'Sage Project 11', 'ITEMKEY': None, 'ITEMID': None, 'ITEMNAME': None, 'DESCRIPTION': None, 'BILLABLE': 'false', 'TASKNO': None, 'TASKSTATUS': 'In Progress', 'CLASSID': None, 'CLASSNAME': None, 'CLASSKEY': None, 'ROOTPARENTKEY': '39', 'ROOTPARENTID': '112', 'ROOTPARENTNAME': 'HrishabhCostType_v4'}
    ]]

    mocker.patch('sageintacctsdk.apis.Tasks.get_all_generator', return_value=data)

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=1)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=1)

    sage_intacct_connection.sync_cost_codes()

    assert CostCode.objects.filter(workspace_id=workspace_id).count() == 2
    attribute = CostCode.objects.filter(workspace_id=workspace_id, project_id='1171').first()

    assert attribute.task_name == 'HrishabhCostCode'
    assert attribute.project_id == '1171'
    assert attribute.project_name == 'Sage Project 10'
    assert attribute.task_id == '111'


def test_search_and_create_vendors(db, mocker):
    """
    Test search and create vendors
    """
    workspace_id = 1
    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)

    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
    )

    missing_vendors = ['Missing Vendor 1', 'Missing Vendor 2']

    mocker.patch(
        'sageintacctsdk.apis.Vendors.get_by_query',
        return_value=[
            {'NAME': 'Missing Vendor 1', 'VENDORID': '20002', 'DISPLAYCONTACT.EMAIL1': None, 'WHENMODIFIED': '11/27/2023 06:51:12'},
            {'NAME': 'Missing Vendor 2', 'VENDORID': '20003', 'DISPLAYCONTACT.EMAIL1': None, 'WHENMODIFIED': '07/01/2022 08:30:59'},
            {'NAME': 'Missing Vendor 2', 'VENDORID': '20004', 'DISPLAYCONTACT.EMAIL1': None, 'WHENMODIFIED': '07/01/2023 08:30:59'}

        ]
    )

    sage_intacct_connection.search_and_create_vendors(workspace_id=workspace_id, missing_vendors=missing_vendors)
    vendor_1 = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR', value='Missing Vendor 1').first()

    assert vendor_1 is not None
    assert vendor_1.value == 'Missing Vendor 1'
    assert vendor_1.destination_id == '20002'

    vendor_2 = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR', value='Missing Vendor 2').first()

    assert vendor_2 is not None
    assert vendor_2.value == 'Missing Vendor 2'
    assert vendor_2.destination_id == '20004'


def test_construct_single_itemized_credit_line(create_journal_entry, db):
    """
    Test construct single itemized credit line
    """
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    general_mappings = GeneralMapping.objects.filter(workspace_id=workspace_id).first()
    general_mappings.default_credit_card_id = 'CC123'
    general_mappings.default_gl_account_id = 'GL456'
    general_mappings.save()

    journal_entry, journal_entry_lineitems = create_journal_entry

    # Test case 1: Multiple line items for same vendor
    journal_entry_lineitems[0].vendor_id = 'VENDOR1'
    journal_entry_lineitems[0].amount = 100
    journal_entry_lineitems[0].employee_id = 'EMP1'
    journal_entry_lineitems[0].user_defined_dimensions = []  # Initialize empty list

    # Add second line item for same vendor with a different expense_id
    second_lineitem = journal_entry_lineitems[0].__class__.objects.create(
        journal_entry=journal_entry,
        vendor_id='VENDOR1',
        amount=200,
        employee_id='EMP1',
        expense_id=journal_entry_lineitems[0].expense_id + 1,  # Use a different expense_id
        user_defined_dimensions=[]  # Initialize empty list
    )
    journal_entry_lineitems.append(second_lineitem)

    # Ensure fund source is not CCC
    journal_entry.expense_group.fund_source = 'PERSONAL'
    journal_entry.expense_group.save()

    credit_lines = sage_intacct_connection._SageIntacctConnector__construct_single_itemized_credit_line(
        journal_entry_lineitems=journal_entry_lineitems,
        general_mappings=general_mappings,
        journal_entry=journal_entry,
        configuration=Configuration.objects.get(workspace_id=workspace_id)
    )

    assert len(credit_lines) == 1
    assert credit_lines[0]['vendorid'] == 'VENDOR1'
    assert credit_lines[0]['amount'] == 300  # Sum of 100 + 200
    assert credit_lines[0]['tr_type'] == -1  # Positive amount
    assert credit_lines[0]['accountno'] == general_mappings.default_gl_account_id

    # Test case 2: Multiple vendors
    journal_entry_lineitems[0].vendor_id = 'VENDOR1'
    journal_entry_lineitems[0].amount = 100
    journal_entry_lineitems[1].vendor_id = 'VENDOR2'
    journal_entry_lineitems[1].amount = 200

    credit_lines = sage_intacct_connection._SageIntacctConnector__construct_single_itemized_credit_line(
        journal_entry_lineitems=journal_entry_lineitems,
        general_mappings=general_mappings,
        journal_entry=journal_entry,
        configuration=Configuration.objects.get(workspace_id=workspace_id)
    )

    assert len(credit_lines) == 2
    vendor_amounts = {line['vendorid']: line['amount'] for line in credit_lines}
    assert vendor_amounts['VENDOR1'] == 100
    assert vendor_amounts['VENDOR2'] == 200

    # Test case 3: Refund case (negative amount)
    journal_entry_lineitems[0].amount = -100
    credit_lines = sage_intacct_connection._SageIntacctConnector__construct_single_itemized_credit_line(
        journal_entry_lineitems=journal_entry_lineitems,
        general_mappings=general_mappings,
        journal_entry=journal_entry,
        configuration=Configuration.objects.get(workspace_id=workspace_id)
    )

    assert len(credit_lines) == 2
    assert credit_lines[0]['amount'] == 100  # Absolute value
    assert credit_lines[0]['vendorid'] == 'VENDOR1'

    # Test case 4: Zero amount line item
    journal_entry_lineitems[0].amount = 0
    credit_lines = sage_intacct_connection._SageIntacctConnector__construct_single_itemized_credit_line(
        journal_entry_lineitems=journal_entry_lineitems,
        general_mappings=general_mappings,
        journal_entry=journal_entry,
        configuration=Configuration.objects.get(workspace_id=workspace_id)
    )

    assert len(credit_lines) == 1  # Only VENDOR2 should be present
    assert credit_lines[0]['vendorid'] == 'VENDOR2'

    # Test case 5: CCC fund source
    journal_entry.expense_group.fund_source = 'CCC'
    journal_entry.expense_group.save()
    credit_lines = sage_intacct_connection._SageIntacctConnector__construct_single_itemized_credit_line(
        journal_entry_lineitems=journal_entry_lineitems,
        general_mappings=general_mappings,
        journal_entry=journal_entry,
        configuration=Configuration.objects.get(workspace_id=workspace_id)
    )

    assert credit_lines[0]['accountno'] == general_mappings.default_credit_card_id


def test_construct_journal_entry_with_single_credit_line(create_journal_entry, db):
    """
    Test construct journal entry with single credit line enabled
    """
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    # Enable single credit line and tax codes
    general_settings = Configuration.objects.filter(workspace_id=workspace_id).first()
    general_settings.import_tax_codes = True
    general_settings.je_single_credit_line = True
    general_settings.save()

    general_mappings = GeneralMapping.objects.filter(workspace_id=workspace_id).first()
    general_mappings.default_tax_code_id = 4
    general_mappings.default_credit_card_id = 'CC123'
    general_mappings.default_gl_account_id = 'GL456'
    general_mappings.save()

    journal_entry, journal_entry_lineitems = create_journal_entry

    # Test case 1: Multiple line items for same vendor
    journal_entry_lineitems[0].vendor_id = 'VENDOR1'
    journal_entry_lineitems[0].amount = 100
    journal_entry_lineitems[0].employee_id = 'EMP1'
    journal_entry_lineitems[0].user_defined_dimensions = []  # Initialize empty list

    # Add second line item for same vendor with a different expense_id
    second_lineitem = journal_entry_lineitems[0].__class__.objects.create(
        journal_entry=journal_entry,
        vendor_id='VENDOR1',
        amount=200,
        employee_id='EMP1',
        expense_id=journal_entry_lineitems[0].expense_id + 1,  # Use a different expense_id
        user_defined_dimensions=[]  # Initialize empty list
    )
    journal_entry_lineitems.append(second_lineitem)

    # Ensure fund source is not CCC
    journal_entry.expense_group.fund_source = 'PERSONAL'
    journal_entry.expense_group.save()

    journal_entry_object = sage_intacct_connection._SageIntacctConnector__construct_journal_entry(
        journal_entry=journal_entry,
        journal_entry_lineitems=journal_entry_lineitems
    )

    # Verify credit lines are grouped by vendor
    credit_lines = [entry for entry in journal_entry_object['entries'][0]['glentry']
                   if entry['tr_type'] == -1 and entry.get('description') == 'Total Credit Line']
    assert len(credit_lines) == 1
    assert credit_lines[0]['vendorid'] == 'VENDOR1'
    assert credit_lines[0]['amount'] == 300  # Sum of 100 + 200
    assert credit_lines[0]['accountno'] == general_mappings.default_gl_account_id

    # Test case 2: Multiple vendors
    journal_entry_lineitems[0].vendor_id = 'VENDOR1'
    journal_entry_lineitems[0].amount = 100
    journal_entry_lineitems[1].vendor_id = 'VENDOR2'
    journal_entry_lineitems[1].amount = 200

    journal_entry_object = sage_intacct_connection._SageIntacctConnector__construct_journal_entry(
        journal_entry=journal_entry,
        journal_entry_lineitems=journal_entry_lineitems
    )

    # Verify credit lines for multiple vendors
    credit_lines = [entry for entry in journal_entry_object['entries'][0]['glentry']
                   if entry['tr_type'] == -1 and entry.get('description', '').startswith('Total Credit Line')]
    assert len(credit_lines) == 2
    vendor_amounts = {line['vendorid']: line['amount'] for line in credit_lines}
    assert vendor_amounts['VENDOR1'] == 100
    assert vendor_amounts['VENDOR2'] == 200

    # Test case 3: Refund case (negative amount)
    # Set both line items to negative amounts for the same vendor
    journal_entry_lineitems[0].amount = -100
    journal_entry_lineitems[1].amount = -200
    journal_entry_lineitems[1].vendor_id = 'VENDOR1'  # Ensure both are for same vendor

    journal_entry_object = sage_intacct_connection._SageIntacctConnector__construct_journal_entry(
        journal_entry=journal_entry,
        journal_entry_lineitems=journal_entry_lineitems
    )

    # Verify refund handling - should have one credit line with positive amount
    credit_lines = [entry for entry in journal_entry_object['entries'][0]['glentry']
                   if entry['tr_type'] == 1 and entry.get('description') == 'Total Credit Line']
    assert len(credit_lines) == 1
    assert credit_lines[0]['amount'] == 300  # Sum of absolute values
    assert credit_lines[0]['vendorid'] == 'VENDOR1'

    # Test case 4: Zero amount line item
    journal_entry_lineitems[0].amount = 0
    journal_entry_object = sage_intacct_connection._SageIntacctConnector__construct_journal_entry(
        journal_entry=journal_entry,
        journal_entry_lineitems=journal_entry_lineitems
    )

    # Verify zero amount handling
    credit_lines = [entry for entry in journal_entry_object['entries'][0]['glentry']
                   if entry['tr_type'] == 1 and entry.get('description', '').startswith('Total Credit Line')]
    assert len(credit_lines) == 1  # Only VENDOR1 should be present with non-zero amount
    assert credit_lines[0]['vendorid'] == 'VENDOR1'
    assert credit_lines[0]['amount'] == 200  # Only the non-zero amount

    # Test case 5: CCC fund source
    journal_entry.expense_group.fund_source = 'CCC'
    journal_entry.expense_group.save()
    journal_entry_object = sage_intacct_connection._SageIntacctConnector__construct_journal_entry(
        journal_entry=journal_entry,
        journal_entry_lineitems=journal_entry_lineitems
    )

    # Verify CCC fund source handling
    credit_lines = [entry for entry in journal_entry_object['entries'][0]['glentry']
                   if entry['tr_type'] == 1 and entry.get('description', '').startswith('Total Credit Line')]
    assert credit_lines[0]['accountno'] == general_mappings.default_credit_card_id


def test_invalidate_sage_intacct_credentials(mocker, db):
    """
    Test invalidate sage intacct credentials
    """
    workspace_id = 1
    sage_intacct_credentials = SageIntacctCredential.objects.filter(workspace_id=workspace_id, is_expired=False).first()

    mocked_patch = mocker.MagicMock()
    mocker.patch('apps.workspaces.tasks.patch_integration_settings', side_effect=mocked_patch)

    # Should not fail if sage_intacct_credentials was not found
    sage_intacct_credentials.delete()
    invalidate_sage_intacct_credentials(workspace_id)
    assert not mocked_patch.called

    # Should not call patch_integration_settings if sage_intacct_credentials.is_expired is True
    sage_intacct_credentials.is_expired = True
    sage_intacct_credentials.save()
    invalidate_sage_intacct_credentials(workspace_id)
    assert not mocked_patch.called

    # TODO: Uncomment this when we have a FE Changes ready
    # # Should call patch_integration_settings with the correct arguments if sage_intacct_credentials.is_expired is False
    # sage_intacct_credentials.is_expired = False
    # sage_intacct_credentials.save()

    # invalidate_sage_intacct_credentials(workspace_id)

    # args, kwargs = mocked_patch.call_args
    # assert args[0] == workspace_id
    # assert kwargs['is_token_expired'] == True

    # # Verify the credentials were marked as expired
    # sage_intacct_credentials.refresh_from_db()
    # assert sage_intacct_credentials.is_expired == True


def test_get_or_create_vendor_fallback_creation_error(mocker, db):
    """
    Test get or create vendor when fallback vendor creation fails
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Vendors.get',
        return_value={}
    )

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    vendor_name = 'Test Vendor'
    email = 'test@example.com'

    class CustomException(Exception):
        def __init__(self, message):
            super().__init__(message)
            self.response = "Custom error response"

    mocker.patch('apps.sage_intacct.utils.logger')

    with mock.patch.object(sage_intacct_connection, 'post_vendor') as mock_post_vendor:
        mock_post_vendor.side_effect = [
            WrongParamsError(
                msg={
                    'Message': 'Invalid parameters'
                },
                response={
                    'error': [{'description2': 'Another record with the value already exists'}],
                    'type': 'Invalid_params'
                }
            ),
            CustomException('General vendor creation error')
        ]

        mocker.patch.object(sage_intacct_connection.connection.vendors, 'get', return_value={})

        try:
            vendor = sage_intacct_connection.get_or_create_vendor(vendor_name, email, create=True)

            assert vendor is None
            assert mock_post_vendor.call_count == 2

            calls = mock_post_vendor.call_args_list
            assert calls[0][0][0] == 'Test Vendor'
            assert calls[1][0][0] == 'Test Vendor-1'
        except Exception:
            assert False, "Exception should have been handled and None returned"
