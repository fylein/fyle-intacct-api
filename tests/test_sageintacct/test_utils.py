import ast
import json
from datetime import datetime
import pytest
import logging
from unittest import mock
from apps.sage_intacct.models import CostType
from sageintacctsdk.exceptions import WrongParamsError
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, Mapping, CategoryMapping
from apps.sage_intacct.utils import SageIntacctConnector, SageIntacctCredential, Configuration, Workspace
from apps.mappings.models import GeneralMapping
from .fixtures import data
from tests.helper import dict_compare_keys

logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_sync_employees(mocker, db):
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
        'apps.mappings.imports.modules.categories.disable_categories'
    )

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    expense_type_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EXPENSE_TYPE').count()
    assert expense_type_count == 8

    sage_intacct_connection.sync_expense_types()

    new_expense_type_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EXPENSE_TYPE').count()
    assert new_expense_type_count == 8


def test_sync_charge_card_accounts(mocker, db):
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
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all_generator',
        return_value=data['get_projects']
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=5
    )

    mock = mocker.patch('apps.mappings.imports.modules.projects.PlatformConnector')
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
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Dimensions.get_all',
        return_value=data['get_user_defined_dimensions']
    )
    mocker.patch(
        'sageintacctsdk.apis.DimensionValues.get_all',
        return_value=data['get_dimension_value']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    user_defined_dimension_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PLACE').count()
    assert user_defined_dimension_count == 0

    sage_intacct_connection.sync_user_defined_dimensions()

    new_user_defined_dimension_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PLACE').count()
    assert new_user_defined_dimension_count == 2


def test_construct_bill(create_bill, db):
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
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    expense_report,expense_report_lineitems = create_expense_report
    expense_report_lineitems[0].user_defined_dimensions = [{'CLASS': 'sample'}]
    expense_report_object = sage_intacct_connection._SageIntacctConnector__construct_expense_report(expense_report=expense_report, expense_report_lineitems=expense_report_lineitems)

    assert dict_compare_keys(expense_report_object, data['expense_report_payload']) == [], 'construct expense_report_payload entry api return diffs in keys'


def test_construct_charge_card_transaction(create_charge_card_transaction, db):
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    charge_card_transaction,charge_card_transaction_lineitems = create_charge_card_transaction
    charge_card_transaction_lineitems[0].user_defined_dimensions = [{'CLASS': 'sample'}, {'USERDIM1': 'C000013'}]
    charge_card_transaction_object = sage_intacct_connection._SageIntacctConnector__construct_charge_card_transaction(charge_card_transaction=charge_card_transaction, charge_card_transaction_lineitems=charge_card_transaction_lineitems)

    assert dict_compare_keys(charge_card_transaction_object, data['charge_card_transaction_payload']) == [], 'construct credit_card_purchase_payload entry api return diffs in keys'


def test_construct_journal_entry(create_journal_entry, db):
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
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    sage_intacct_reimbursement,sage_intacct_reimbursement_lineitems = create_sage_intacct_reimbursement
    sage_intacct_reimbursement_object = sage_intacct_connection._SageIntacctConnector__construct_sage_intacct_reimbursement(reimbursement=sage_intacct_reimbursement,reimbursement_lineitems=sage_intacct_reimbursement_lineitems)

    assert dict_compare_keys(sage_intacct_reimbursement_object, data['sage_intacct_reimbursement_payload']) == [], 'construct expense api return diffs in keys'


def test_construct_ap_payment(create_ap_payment, db):
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    ap_payment,ap_payment_lineitems = create_ap_payment
    ap_payment_object = sage_intacct_connection._SageIntacctConnector__construct_ap_payment(ap_payment=ap_payment,ap_payment_lineitems=ap_payment_lineitems)

    assert dict_compare_keys(ap_payment_object, data['ap_payment_payload']) == [], 'construct ap_payment api return diffs in keys'


def test_get_bill(mocker, db):
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
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)
    
    expense_report, expense_report_lineitems = create_expense_report
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
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)
    tax_exclusive_amount, tax_amount = sage_intacct_connection.get_tax_exclusive_amount(100, 4)
    
    assert tax_exclusive_amount == 100.0


def test_sync_tax_details(mocker, db):
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
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Accounts.count',
        return_value=5
    )
    mocker.patch(
        'sageintacctsdk.apis.Accounts.get_all_generator',
        return_value=data['get_accounts']
    )

    mock = mocker.patch('apps.mappings.imports.modules.categories.PlatformConnector')
    mocker.patch.object(mock.return_value.categories, 'post_bulk')

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    account_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='ACCOUNT').count()
    assert account_count == 170

    sage_intacct_connection.sync_accounts()

    new_account_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='ACCOUNT').count()
    assert new_account_count == 170


def test_sync_classes(mocker, db):
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Classes.get_all_generator',
        return_value=data['get_classes']
    )

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
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Customers.count',
        return_value=5
    )
    mocker.patch(
        'sageintacctsdk.apis.Customers.get_all_generator',
        return_value=data['get_customers']
    )
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    customer_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CUSTOMER').count()
    assert customer_count == 526

    sage_intacct_connection.sync_customers()

    new_customer_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CUSTOMER').count()
    assert new_customer_count == 526


def test_post_bill_exception(mocker, db, create_bill):
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
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': 'Date must be on or after', 'correction': ''}],
                'type': 'Invalid_params'
            }), None]
            sage_intacct_connection.post_expense_report(expense_report, expense_report_lineitems)
    except:
        logger.info("Account period error")


def test_post_charge_card_transaction_exception(mocker, db, create_charge_card_transaction):
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
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': 'Date must be on or after', 'correction': ''}],
                'type': 'Invalid_params'
            }), None]
            sage_intacct_connection.post_charge_card_transaction(charge_card_transaction, charge_card_transaction_lineitems)
    except:
        logger.info("Account period error")


def test_post_journal_entry_exception(mocker, db, create_journal_entry):
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
    except:
        logger.info("Account period error")


def test_post_ap_payment(mocker, db, create_ap_payment):
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
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Attachments.post',
        return_value={'status': 'success', 'key': '3032'}
    )

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    supdoc_id = sage_intacct_connection.post_attachments([{'download_url': 'sdfghj', 'name': 'ert.sdf.sdf', 'id': 'dfgh'}], 'asd')

    assert supdoc_id == 'asd'

def test_get_expense_link(mocker, db, create_journal_entry):
    workspace_id = 1

    workspace = Workspace.objects.get(id=workspace_id)
    workspace.cluster_domain = ''
    workspace.save()

    journal_entry, journal_entry_lineitems = create_journal_entry

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    expense_link = sage_intacct_connection.get_expense_link(journal_entry_lineitems[0])
    assert expense_link == 'None/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'


def test_get_or_create_vendor(mocker, db):
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

    assert vendor.value == 'Ashwin'

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

    # case insensitive not found in db -> search in intacct and found
    data['get_vendor'][0]['NAME'] = 'Non existing vendor in DB use all cases'

    get_call_mock.return_value = {'VENDOR': data['get_vendor'], '@totalcount': 2}

    vendor = sage_intacct_connection.get_or_create_vendor('non exiSting VENDOR iN Db UsE aLl CaSeS', create=True)

    assert vendor.value == 'Non existing vendor in DB use all cases'
    assert DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR', value='Non existing vendor in DB use all cases').exists() is True

    # case insensitive not found in db -> search in intacct and not found -> create new in intacct
    get_call_mock.return_value = {}

    new_post_vendors_data = data['post_vendors']
    new_post_vendors_data['data']['vendor']['NAME'] = 'non exiSting VENDOR iN intacct UsE aLl CaSeS'
    new_post_vendors_data['data']['vendor']['VENDORID'] = 'non exiSting VENDOR iN intacct UsE aLl CaSeS'

    post_call_mock.return_value = new_post_vendors_data

    vendor = sage_intacct_connection.get_or_create_vendor('non exiSting VENDOR iN intacct UsE aLl CaSeS', create=True)
    assert vendor.destination_id == 'non exiSting VENDOR iN intacct UsE aLl CaSeS'


def test_get_or_create_employee(mocker, db):
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
    vendor_name = "Vendor@ABC~!@#$%^&*()_+=|"
    expected_output = "VendorABC"
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
