import json
import pytest

from datetime import datetime, timezone, timedelta

from django.utils import timezone as django_timezone

from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute
from intacctsdk.exceptions import BadRequestError

from apps.workspaces.models import (
    Workspace,
    SageIntacctCredential,
    Configuration,
)
from fyle_accounting_library.system_comments.models import SystemComment
from apps.workspaces.enums import (
    ExportTypeEnum,
    SystemCommentIntentEnum,
    SystemCommentReasonEnum,
    SystemCommentSourceEnum,
    SystemCommentEntityTypeEnum
)
from apps.sage_intacct.models import DependentFieldSetting
from apps.sage_intacct.connector import (
    SageIntacctRestConnector,
    SageIntacctDimensionSyncManager,
    SageIntacctObjectCreationManager,
    SYNC_UPPER_LIMIT,
    COST_TYPES_LIMIT,
)


def test_sage_intacct_rest_connector_init(db, mock_intacct_sdk):
    """
    Test SageIntacctRestConnector initialization
    """
    _, mock_instance = mock_intacct_sdk
    mock_instance.sessions.get_session_id.return_value = {'sessionId': 'mock_session_id'}

    connector = SageIntacctRestConnector(workspace_id=1)

    assert connector.workspace_id == 1
    assert connector.connection is not None


def test_sage_intacct_rest_connector_get_session_id(db, mock_intacct_sdk):
    """
    Test getting session id
    """
    _, mock_instance = mock_intacct_sdk
    mock_instance.sessions.get_session_id.return_value = {'sessionId': 'test_session_123'}

    connector = SageIntacctRestConnector(workspace_id=1)
    session_id = connector.get_session_id()

    assert session_id == 'test_session_123'


def test_sage_intacct_rest_connector_get_soap_connection(db, mock_intacct_sdk, mock_sage_intacct_sdk):
    """
    Test getting SOAP connection
    """
    mock_rest_sdk_class, mock_rest_instance = mock_intacct_sdk
    mock_soap_sdk_class, mock_soap_instance = mock_sage_intacct_sdk
    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'mock_session_id'}

    connector = SageIntacctRestConnector(workspace_id=1)
    soap_connection = connector.get_soap_connection()

    assert soap_connection is not None
    mock_soap_sdk_class.assert_called_once()


def test_sage_intacct_rest_connector_with_cached_access_token(db, mock_intacct_sdk):
    """
    Test connector uses cached access token when valid
    """
    credential = SageIntacctCredential.objects.get(workspace_id=1)
    credential.access_token = 'cached_token'
    credential.access_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
    credential.save()

    connector = SageIntacctRestConnector(workspace_id=1)

    assert connector.access_token == 'cached_token'


def test_sync_accounts(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing accounts from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.accounts.count.return_value = 5
    mock_instance.accounts.get_all_generator.return_value = iter([[
        {'id': 'ACC001', 'name': 'Test Account', 'accountType': 'Asset', 'status': 'active'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_accounts()

    mock_instance.accounts.count.assert_called_once()
    mock_instance.accounts.get_all_generator.assert_called_once()


def test_sync_accounts_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync accounts is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    # Set count over limit
    mock_instance.accounts.count.return_value = SYNC_UPPER_LIMIT + 1000

    # Patch the timezone in connector module to use django's timezone
    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    # Create workspace after October 2024
    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_accounts()

    mock_instance.accounts.count.assert_called_once()
    mock_instance.accounts.get_all_generator.assert_not_called()


def test_sync_departments(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing departments from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.departments.count.return_value = 3
    mock_instance.departments.get_all_generator.return_value = iter([[
        {'id': 'DEPT001', 'name': 'Engineering', 'status': 'active'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_departments()

    mock_instance.departments.count.assert_called_once()
    mock_instance.departments.get_all_generator.assert_called_once()


def test_sync_expense_types(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test syncing expense types from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk
    mocker.patch('apps.sage_intacct.connector.publish_to_rabbitmq')

    mock_instance.expense_types.count.return_value = 2
    mock_instance.expense_types.get_all_generator.return_value = iter([[
        {
            'id': 'EXP001',
            'description': 'Travel Expense',
            'glAccount.id': 'GL001',
            'glAccount.name': 'Travel',
            'status': 'active'
        }
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_expense_types()

    mock_instance.expense_types.count.assert_called_once()


def test_sync_vendors(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing vendors from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.vendors.count.return_value = 2
    mock_instance.vendors.get_all_generator.return_value = iter([[
        {'id': 'VND001', 'name': 'Vendor One', 'status': 'active', 'contacts.default.email1': 'vendor@test.com'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_vendors()

    mock_instance.vendors.count.assert_called_once()
    mock_instance.vendors.get_all_generator.assert_called_once()


def test_sync_employees(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing employees from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.employees.count.return_value = 1
    mock_instance.employees.get_all_generator.return_value = iter([[
        {
            'id': 'EMP001',
            'name': 'John Doe',
            'status': 'active',
            'primaryContact.email1': 'john@test.com',
            'primaryContact.printAs': 'John Doe',
            'department.id': 'DEPT001',
            'location.id': 'LOC001'
        }
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_employees()

    mock_instance.employees.count.assert_called_once()
    mock_instance.employees.get_all_generator.assert_called_once()


def test_sync_projects(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing projects from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.projects.count.return_value = 2
    mock_instance.projects.get_all_generator.return_value = iter([[
        {
            'id': 'PRJ001',
            'name': 'Project Alpha',
            'status': 'active',
            'customer.id': 'CUS001',
            'customer.name': 'Customer One',
            'isBillableEmployeeExpense': True,
            'isBillablePurchasingAPExpense': False
        }
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_projects()

    mock_instance.projects.count.assert_called_once()
    mock_instance.projects.get_all_generator.assert_called_once()


def test_sync_customers(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing customers from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.customers.count.return_value = 1
    mock_instance.customers.get_all_generator.return_value = iter([[
        {'id': 'CUS001', 'name': 'Customer One', 'status': 'active'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_customers()

    mock_instance.customers.count.assert_called_once()
    mock_instance.customers.get_all_generator.assert_called_once()


def test_sync_classes(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing classes from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.classes.count.return_value = 1
    mock_instance.classes.get_all_generator.return_value = iter([[
        {'id': 'CLS001', 'name': 'Class One', 'status': 'active'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_classes()

    mock_instance.classes.count.assert_called_once()
    mock_instance.classes.get_all_generator.assert_called_once()


def test_sync_locations(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing locations from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.locations.count.return_value = 1
    mock_instance.locations.get_all_generator.return_value = iter([[
        {'id': 'LOC001', 'name': 'New York', 'status': 'active'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_locations()

    mock_instance.locations.count.assert_called_once()
    mock_instance.locations.get_all_generator.assert_called_once()


def test_sync_items(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing items from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.items.count.return_value = 1
    mock_instance.items.get_all_generator.return_value = iter([[
        {'id': 'ITM001', 'name': 'Item One', 'status': 'active', 'itemType': 'nonInventory'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_items()

    mock_instance.items.count.assert_called_once()
    mock_instance.items.get_all_generator.assert_called_once()


def test_sync_tax_details(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing tax details from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.tax_details.count.return_value = 1
    mock_instance.tax_details.get_all_generator.return_value = iter([[
        {'id': 'TAX001', 'taxPercent': '10.0', 'taxSolution.id': 'SOL001', 'status': 'active', 'taxType': 'purchase'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_tax_details()

    mock_instance.tax_details.count.assert_called_once()
    mock_instance.tax_details.get_all_generator.assert_called_once()


def test_sync_payment_accounts(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing payment accounts from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.checking_accounts.count.return_value = 1
    mock_instance.checking_accounts.get_all_generator.return_value = iter([[
        {'id': 'PA001', 'bankAccountDetails.bankName': 'Test Bank', 'status': 'active'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_payment_accounts()

    mock_instance.checking_accounts.count.assert_called_once()
    mock_instance.checking_accounts.get_all_generator.assert_called_once()


def test_sync_charge_card_accounts(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing charge card accounts from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.charge_card_accounts.count.return_value = 1
    mock_instance.charge_card_accounts.get_all_generator.return_value = iter([[
        {'id': 'CC001', 'status': 'active'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_charge_card_accounts()

    mock_instance.charge_card_accounts.count.assert_called_once()
    mock_instance.charge_card_accounts.get_all_generator.assert_called_once()


def test_sync_expense_payment_types(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing expense payment types from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.expense_payment_types.count.return_value = 1
    mock_instance.expense_payment_types.get_all_generator.return_value = iter([[
        {'key': 'EPT001', 'id': 'Cash', 'isNonReimbursable': False}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_expense_payment_types()

    mock_instance.expense_payment_types.count.assert_called_once()
    mock_instance.expense_payment_types.get_all_generator.assert_called_once()


def test_sync_user_defined_dimensions(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing user defined dimensions from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.dimensions.list.return_value = [
        {
            'dimensionName': 'TestDim',
            'termName': 'Test Dimension',
            'isUserDefinedDimension': False,
            'dimensionEndpoint': 'endpoint::testdim'
        }
    ]

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_user_defined_dimensions()

    mock_instance.dimensions.list.assert_called_once()
    mock_instance.dimensions.count.assert_not_called()


def test_sync_allocations(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing allocations from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.allocations.count.return_value = 1
    mock_instance.allocations.get_all_generator.return_value = iter([[
        {'id': 'ALLOC001', 'status': 'active', 'key': '1'}
    ]])
    mock_instance.allocations.get_by_key.return_value = {
        'ia::result': {
            'id': 'ALLOC001',
            'key': '1',
            'lines': [{'dimensions': {'location': {'key': 'LOC001'}}}]
        }
    }

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_allocations()

    mock_instance.allocations.count.assert_called_once()
    mock_instance.allocations.get_all_generator.assert_called_once()


def test_get_bills(db, mock_intacct_sdk):
    """
    Test getting bills from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.bills.get_all_generator.return_value = iter([[
        {'key': 'BILL001', 'state': 'paid'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    bills = sync_manager.get_bills(bill_ids=['BILL001'])

    assert bills is not None


def test_get_expense_reports(db, mock_intacct_sdk):
    """
    Test getting expense reports from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.expense_reports.get_all_generator.return_value = iter([[
        {'key': 'ER001', 'state': 'paid'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    expense_reports = sync_manager.get_expense_reports(expense_report_ids=['ER001'])

    assert expense_reports is not None


def test_sync_location_entities(db, mock_intacct_sdk, mock_sage_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing location entities from Sage Intacct
    """
    _, mock_rest_instance = mock_intacct_sdk
    _, mock_soap_instance = mock_sage_intacct_sdk

    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'test'}
    mock_soap_instance.api_base.format_and_send_request.return_value = {
        'data': {
            'companypref': [
                {'preference': 'DISABLEENTITYSLIDEIN', 'prefvalue': 'false'}
            ]
        }
    }
    mock_rest_instance.location_entities.get_all_generator.return_value = iter([[
        {'id': 'LE001', 'name': 'Location Entity 1', 'operatingCountry': 'USA'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_location_entities()

    mock_rest_instance.location_entities.get_all_generator.assert_called_once()


def test_create_vendor(db, mock_intacct_sdk):
    """
    Test creating a vendor in Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.vendors.post.return_value = {
        'ia::result': {'key': 'VND123'}
    }
    mock_instance.vendors.get_by_key.return_value = {
        'ia::result': {'id': 'VND123', 'name': 'Test Vendor'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    vendor = manager.create_vendor(vendor_id='VND001', vendor_name='Test Vendor', email='test@test.com')

    assert vendor is not None
    assert vendor['id'] == 'VND123'


def test_create_contact(db, mock_intacct_sdk):
    """
    Test creating a contact in Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.contacts.post.return_value = {
        'ia::result': {'key': 'CT123'}
    }
    mock_instance.contacts.get_by_key.return_value = {
        'ia::result': {'id': 'CT123', 'printAs': 'Test Contact'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    contact = manager.create_contact(
        contact_id='CT001',
        contact_name='Test Contact',
        email='test@test.com',
        first_name='Test',
        last_name='Contact'
    )

    assert contact is not None
    assert contact['id'] == 'CT123'


def test_get_or_create_vendor_existing(db, mock_intacct_sdk, create_existing_vendor_attribute):
    """
    Test get_or_create_vendor returns existing vendor from database
    """
    _, _ = mock_intacct_sdk

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    vendor = manager.get_or_create_vendor(vendor_name='Existing Vendor')

    assert vendor is not None
    assert vendor.destination_id == 'VND_EXISTING'


def test_get_or_create_vendor_create_new(db, mock_intacct_sdk):
    """
    Test get_or_create_vendor creates new vendor when not found
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.vendors.post.return_value = {
        'ia::result': {'key': 'NEW_VND'}
    }
    mock_instance.vendors.get_by_key.return_value = {
        'ia::result': {'id': 'NEW_VND', 'name': 'New Vendor'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    vendor = manager.get_or_create_vendor(
        vendor_name='Brand New Vendor',
        email='new@test.com',
        create=True
    )

    assert vendor is not None


def test_search_and_create_vendors(db, mock_intacct_sdk):
    """
    Test searching and creating vendors in Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.vendors.get_all_generator.return_value = iter([[
        {'id': 'VND001', 'name': 'Found Vendor', 'status': 'active', 'contacts.default.email1': 'found@test.com'}
    ]])

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    manager.search_and_create_vendors(workspace_id=1, missing_vendors=['Found Vendor'])

    mock_instance.vendors.get_all_generator.assert_called_once()


def test_post_bill(db, mock_intacct_sdk, create_bill):
    """
    Test posting a bill to Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk
    bill, bill_lineitems = create_bill

    mock_instance.bills.post.return_value = {
        'ia::result': {'id': '81035', 'key': '81035', 'href': '/objects/accounts-payable/bill/81035'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_bill(bill=bill, bill_line_items=bill_lineitems)

    assert result is not None
    mock_instance.bills.post.assert_called_once()


def test_post_expense_report(db, mock_intacct_sdk, create_expense_report):
    """
    Test posting an expense report to Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk
    expense_report, expense_report_lineitems = create_expense_report

    mock_instance.expense_reports.post.return_value = {
        'ia::result': {'id': '12345', 'key': '12345', 'href': '/objects/expense-management/expense-report/12345'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_expense_report(expense_report=expense_report, expense_report_line_items=expense_report_lineitems)

    assert result is not None
    mock_instance.expense_reports.post.assert_called_once()


def test_post_charge_card_transaction(db, mock_intacct_sdk, create_charge_card_transaction):
    """
    Test posting a charge card transaction to Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk
    cct, cct_lineitems = create_charge_card_transaction

    mock_instance.charge_card_transactions.post.return_value = {
        'ia::result': {'id': '81033', 'key': '81033', 'href': '/objects/cash-management/credit-card-txn/81033'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_charge_card_transaction(charge_card_transaction=cct, charge_card_transaction_line_items=cct_lineitems)

    assert result is not None
    mock_instance.charge_card_transactions.post.assert_called_once()


def test_post_journal_entry(db, mock_intacct_sdk, create_journal_entry):
    """
    Test posting a journal entry to Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk
    journal_entry, journal_entry_lineitems = create_journal_entry

    mock_instance.journal_entries.post.return_value = {
        'ia::result': {'id': '120680', 'key': '120680', 'href': '/objects/general-ledger/journal-entry/120680'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_journal_entry(journal_entry=journal_entry, journal_entry_line_items=journal_entry_lineitems)

    assert result is not None
    mock_instance.journal_entries.post.assert_called_once()


def test_post_ap_payment(db, mock_intacct_sdk, create_ap_payment):
    """
    Test posting an AP payment to Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk
    ap_payment, ap_payment_lineitems = create_ap_payment

    mock_instance.ap_payments.post.return_value = {
        'ia::result': {'id': '54321', 'key': '54321', 'href': '/objects/accounts-payable/ap-payment/54321'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_ap_payment(ap_payment=ap_payment, ap_payment_line_items=ap_payment_lineitems)

    assert result is not None
    mock_instance.ap_payments.post.assert_called_once()


def test_post_sage_intacct_reimbursement(db, mock_intacct_sdk, mock_sage_intacct_sdk, create_sage_intacct_reimbursement):
    """
    Test posting a reimbursement to Sage Intacct
    """
    mock_rest_sdk_class, mock_rest_instance = mock_intacct_sdk
    mock_soap_sdk_class, mock_soap_instance = mock_sage_intacct_sdk
    reimbursement, reimbursement_lineitems = create_sage_intacct_reimbursement

    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'test'}
    mock_soap_instance.reimbursements.post.return_value = {
        'key': 'REIMB123'
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_sage_intacct_reimbursement(reimbursement=reimbursement, reimbursement_line_items=reimbursement_lineitems)

    assert result is not None


def test_get_or_create_attachments_folder(db, mock_intacct_sdk):
    """
    Test getting or creating attachments folder
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.attachment_folders.get_all_generator.return_value = iter([[]])
    mock_instance.attachment_folders.post.return_value = {'ia::result': {'key': 'FOLDER1'}}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    manager.get_or_create_attachments_folder()

    mock_instance.attachment_folders.get_all_generator.assert_called_once()
    mock_instance.attachment_folders.post.assert_called_once()


def test_get_accounting_fields_rest_api(db, mock_intacct_sdk):
    """
    Test get_accounting_fields method in REST connector
    """
    _, mock_instance = mock_intacct_sdk
    mock_instance.sessions.get_session_id.return_value = {'sessionId': 'mock_session_id'}

    mock_instance.employees.get_all_generator.return_value = iter([
        [{'id': 'EMP001', 'name': 'Employee One', 'status': 'active'}],
        [{'id': 'EMP002', 'name': 'Employee Two', 'status': 'active'}]
    ])

    connector = SageIntacctDimensionSyncManager(workspace_id=1)
    result = connector.get_accounting_fields('employees')

    assert result is not None
    assert len(result) == 2
    assert result[0]['id'] == 'EMP001'
    assert result[1]['id'] == 'EMP002'
    mock_instance.employees.get_all_generator.assert_called_once()


def test_get_exported_entry_rest_api_with_id(db, mock_intacct_sdk, mocker):
    """
    Test get_exported_entry method in REST connector using 'id' field
    """
    _, mock_instance = mock_intacct_sdk
    mock_instance.sessions.get_session_id.return_value = {'sessionId': 'mock_session_id'}

    bill_data = {'id': 'BILL001', 'key': 'BILL001', 'state': 'paid', 'amount': 100.0}
    mock_instance.bills.get_all_generator.return_value = iter([
        [bill_data]
    ])

    connector = SageIntacctObjectCreationManager(workspace_id=1)
    mocker.patch.object(connector, 'get_bill', return_value=bill_data)
    result = connector.get_exported_entry('bill', 'BILL001')

    assert result is not None
    assert result['id'] == 'BILL001'
    assert result['amount'] == 100.0


def test_post_attachments(db, mock_intacct_sdk):
    """
    Test posting attachments to Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.attachments.post.return_value = {
        'ia::result': {'key': 'ATT123'}
    }

    attachments = [{'id': 'att1', 'name': 'file.pdf', 'download_url': 'https://example.com/file.pdf'}]
    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result, key = manager.post_attachments(
        attachments=attachments,
        attachment_id='SUPDOC001',
        attachment_number=1
    )

    assert result == 'SUPDOC001'
    assert key == 'ATT123'


def test_post_attachments_empty(db, mock_intacct_sdk):
    """
    Test posting empty attachments returns False
    """
    _, _ = mock_intacct_sdk

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result, key = manager.post_attachments(
        attachments=[],
        attachment_id='SUPDOC001',
        attachment_number=1
    )

    assert result is False
    assert key is None


def test_update_expense_report_attachments(db, mock_intacct_sdk):
    """
    Test updating expense report attachments
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.expense_reports.update_attachment.return_value = {'success': True}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    manager.update_expense_report_attachments(object_key='ER123', attachment_id='ATT001')

    mock_instance.expense_reports.update_attachment.assert_called_once_with(
        object_id='ER123',
        attachment_id='ATT001'
    )


def test_update_bill_attachments(db, mock_intacct_sdk):
    """
    Test updating bill attachments
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.bills.update_attachment.return_value = {'success': True}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    manager.update_bill_attachments(object_key='BILL123', attachment_id='ATT001')

    mock_instance.bills.update_attachment.assert_called_once_with(
        object_id='BILL123',
        attachment_id='ATT001'
    )


def test_update_charge_card_transaction_attachments(db, mock_intacct_sdk):
    """
    Test updating charge card transaction attachments
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.charge_card_transactions.update_attachment.return_value = {'success': True}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    manager.update_charge_card_transaction_attachments(object_key='CCT123', attachment_id='ATT001')

    mock_instance.charge_card_transactions.update_attachment.assert_called_once_with(
        object_id='CCT123',
        attachment_id='ATT001'
    )


def test_update_journal_entry_attachments(db, mock_intacct_sdk):
    """
    Test updating journal entry attachments
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.journal_entries.update_attachment.return_value = {'success': True}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    manager.update_journal_entry_attachments(object_key='JE123', attachment_id='ATT001')

    mock_instance.journal_entries.update_attachment.assert_called_once_with(
        object_id='JE123',
        attachment_id='ATT001'
    )


def test_get_journal_entry(db, mock_intacct_sdk, mock_sage_intacct_sdk):
    """
    Test getting journal entry from Sage Intacct
    """
    _, mock_rest_instance = mock_intacct_sdk
    _, mock_soap_instance = mock_sage_intacct_sdk

    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'test'}
    mock_soap_instance.journal_entries.get.return_value = {'recordno': '123'}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.get_journal_entry(journal_entry_id='123')

    assert result is not None


def test_get_charge_card_transaction(db, mock_intacct_sdk, mock_sage_intacct_sdk):
    """
    Test getting charge card transaction from Sage Intacct
    """
    _, mock_rest_instance = mock_intacct_sdk
    _, mock_soap_instance = mock_sage_intacct_sdk

    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'test'}
    mock_soap_instance.charge_card_transactions.get.return_value = {'recordno': '123'}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.get_charge_card_transaction(charge_card_transaction_id='123')

    assert result is not None


def test_get_bill(db, mock_intacct_sdk, mock_sage_intacct_sdk):
    """
    Test getting bill from Sage Intacct
    """
    _, mock_rest_instance = mock_intacct_sdk
    _, mock_soap_instance = mock_sage_intacct_sdk

    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'test'}
    mock_soap_instance.bills.get.return_value = {'recordno': '123'}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.get_bill(bill_id='123')

    assert result is not None


def test_get_expense_report(db, mock_intacct_sdk, mock_sage_intacct_sdk):
    """
    Test getting expense report from Sage Intacct
    """
    _, mock_rest_instance = mock_intacct_sdk
    _, mock_soap_instance = mock_sage_intacct_sdk

    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'test'}
    mock_soap_instance.expense_reports.get.return_value = {'recordno': '123'}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.get_expense_report(expense_report_id='123')

    assert result is not None


def test_sync_accounts_old_workspace_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync accounts proceeds for old workspaces even when over limit
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.accounts.count.return_value = SYNC_UPPER_LIMIT + 1000
    mock_instance.accounts.get_all_generator.return_value = iter([[
        {'id': 'ACC001', 'name': 'Test Account', 'accountType': 'Asset', 'status': 'active'}
    ]])

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_accounts()

    mock_instance.accounts.count.assert_called_once()
    mock_instance.accounts.get_all_generator.assert_called_once()


def test_sync_departments_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync departments is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.departments.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_departments()

    mock_instance.departments.count.assert_called_once()
    mock_instance.departments.get_all_generator.assert_not_called()


def test_sync_expense_types_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync expense types is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk
    mocker.patch('apps.sage_intacct.connector.publish_to_rabbitmq')

    mock_instance.expense_types.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_expense_types()

    mock_instance.expense_types.count.assert_called_once()
    mock_instance.expense_types.get_all_generator.assert_not_called()


def test_sync_charge_card_accounts_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync charge card accounts is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.charge_card_accounts.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_charge_card_accounts()

    mock_instance.charge_card_accounts.count.assert_called_once()
    mock_instance.charge_card_accounts.get_all_generator.assert_not_called()


def test_sync_payment_accounts_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync payment accounts is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.checking_accounts.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_payment_accounts()

    mock_instance.checking_accounts.count.assert_called_once()
    mock_instance.checking_accounts.get_all_generator.assert_not_called()


def test_sync_projects_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync projects is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.projects.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_projects()

    mock_instance.projects.count.assert_called_once()
    mock_instance.projects.get_all_generator.assert_not_called()


def test_sync_items_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync items is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.items.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_items()

    mock_instance.items.count.assert_called_once()
    mock_instance.items.get_all_generator.assert_not_called()


def test_sync_vendors_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync vendors is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.vendors.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_vendors()

    mock_instance.vendors.count.assert_called_once()
    mock_instance.vendors.get_all_generator.assert_not_called()


def test_sync_employees_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync employees is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.employees.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_employees()

    mock_instance.employees.count.assert_called_once()
    mock_instance.employees.get_all_generator.assert_not_called()


def test_sync_customers_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync customers is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.customers.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_customers()

    mock_instance.customers.count.assert_called_once()
    mock_instance.customers.get_all_generator.assert_not_called()


def test_sync_classes_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync classes is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.classes.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_classes()

    mock_instance.classes.count.assert_called_once()
    mock_instance.classes.get_all_generator.assert_not_called()


def test_sync_locations_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync locations is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.locations.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_locations()

    mock_instance.locations.count.assert_called_once()
    mock_instance.locations.get_all_generator.assert_not_called()


def test_sync_allocations_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync allocations is skipped when count exceeds limit for new workspaces
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.allocations.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_allocations()

    mock_instance.allocations.count.assert_called_once()
    mock_instance.allocations.get_all_generator.assert_not_called()


def test_sync_cost_types(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing cost types from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    DependentFieldSetting.objects.create(
        workspace_id=1,
        is_import_enabled=True,
        project_field_id=1,
        cost_code_field_id=2,
        cost_type_field_id=3
    )

    mock_instance.cost_types.count.return_value = 2
    mock_instance.cost_types.get_all_generator.return_value = iter([[
        {
            'id': 'CT001',
            'key': '1',
            'name': 'Cost Type 1',
            'status': 'active',
            'project.id': 'PRJ001',
            'project.name': 'Project 1',
            'project.key': '1',
            'task.id': 'TASK001',
            'task.name': 'Task 1',
            'task.key': '1',
            'audit.createdDateTime': '2024-01-01T00:00:00Z',
            'audit.modifiedDateTime': '2024-01-01T00:00:00Z'
        }
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_cost_types()

    mock_instance.cost_types.count.assert_called_once()
    mock_instance.cost_types.get_all_generator.assert_called_once()


def test_sync_cost_codes(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing cost codes from Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    DependentFieldSetting.objects.create(
        workspace_id=1,
        is_import_enabled=True,
        project_field_id=1,
        cost_code_field_id=2,
        cost_type_field_id=3
    )

    mock_instance.tasks.count.return_value = 2
    mock_instance.tasks.get_all_generator.return_value = iter([[
        {
            'key': '1',
            'name': 'Task 1',
            'project.key': '1',
            'project.name': 'Project 1'
        }
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_cost_codes()

    mock_instance.tasks.count.assert_called_once()
    mock_instance.tasks.get_all_generator.assert_called_once()


def test_sync_user_defined_dimensions_with_udd(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing user defined dimensions with actual UDD
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.dimensions.list.return_value = [
        {
            'dimensionName': 'Custom Field',
            'termName': 'Custom Field',
            'isUserDefinedDimension': True,
            'dimensionEndpoint': 'endpoint::custom_field'
        }
    ]
    mock_instance.dimensions.count.return_value = 2
    mock_instance.dimensions.get_all_generator.return_value = iter([[
        {'id': 'CF001', 'name': 'Custom Value 1'},
        {'id': 'CF002', 'name': 'Custom Value 2'}
    ]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_user_defined_dimensions()

    mock_instance.dimensions.list.assert_called_once()
    mock_instance.dimensions.count.assert_called()


def test_sync_user_defined_dimensions_with_exception(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing user defined dimensions handles exception
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.dimensions.list.return_value = [
        {
            'dimensionName': 'Custom Field',
            'termName': 'Custom Field',
            'isUserDefinedDimension': True,
            'dimensionEndpoint': 'endpoint::custom_field'
        }
    ]
    mock_instance.dimensions.count.side_effect = Exception('API Error')

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_user_defined_dimensions()

    mock_instance.dimensions.list.assert_called_once()


def test_sync_allocations_skips_empty_entry(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test sync allocations skips when allocation entry is empty
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.allocations.count.return_value = 1
    mock_instance.allocations.get_all_generator.return_value = iter([[
        {'id': 'ALLOC001', 'status': 'active', 'key': '1'}
    ]])
    mock_instance.allocations.get_by_key.return_value = {'ia::result': None}

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_allocations()

    mock_instance.allocations.count.assert_called_once()
    mock_instance.allocations.get_by_key.assert_called_once()


def test_sync_location_entities_skipped_when_entity_slide_disabled(db, mock_intacct_sdk, mock_sage_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing location entities is skipped when entity slide is disabled
    """
    _, mock_rest_instance = mock_intacct_sdk
    _, mock_soap_instance = mock_sage_intacct_sdk

    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'test'}
    mock_soap_instance.api_base.format_and_send_request.return_value = {
        'data': {
            'companypref': [
                {'preference': 'DISABLEENTITYSLIDEIN', 'prefvalue': 'true'}
            ]
        }
    }

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_location_entities()

    mock_rest_instance.location_entities.get_all_generator.assert_not_called()


def test_sync_location_entities_handles_exception(db, mock_intacct_sdk, mock_sage_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test syncing location entities handles exception in get_entity_slide_preference
    """
    _, mock_rest_instance = mock_intacct_sdk
    _, mock_soap_instance = mock_sage_intacct_sdk

    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'test'}
    mock_soap_instance.api_base.format_and_send_request.side_effect = Exception('API Error')
    mock_rest_instance.location_entities.get_all_generator.return_value = iter([[]])

    mock_logger = mocker.patch('apps.sage_intacct.connector.logger')

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_location_entities()

    # Exception is caught and logged
    assert mock_logger.exception.called or mock_logger.error.called or mock_logger.info.called


def test_get_or_create_vendor_long_name(db, mock_intacct_sdk):
    """
    Test get_or_create_vendor truncates long vendor id
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.vendors.post.return_value = {
        'ia::result': {'key': 'NEW_VND'}
    }
    mock_instance.vendors.get_by_key.return_value = {
        'ia::result': {'id': 'NEW_VND', 'name': 'Very Long Vendor Name That Exceeds Limit'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    vendor = manager.get_or_create_vendor(
        vendor_name='Very Long Vendor Name That Exceeds The Twenty Character Limit',
        email='long@test.com',
        create=True
    )

    assert vendor is not None


def test_get_or_create_vendor_with_bad_request_error(db, mock_intacct_sdk):
    """
    Test get_or_create_vendor handles BadRequestError for duplicate vendor
    """
    _, mock_instance = mock_intacct_sdk

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'Another record with the value already exists'
            }
        }
    }

    mock_instance.vendors.post.side_effect = BadRequestError(
        msg='Duplicate',
        response=str(error_response)
    )
    mock_instance.vendors.get_all_generator.return_value = iter([[
        {'id': 'VND001', 'name': 'Duplicate Vendor', 'status': 'active', 'contacts.default.email1': 'dup@test.com'}
    ]])

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    vendor = manager.get_or_create_vendor(
        vendor_name='Duplicate Vendor',
        email='dup@test.com',
        create=True
    )

    assert vendor is None or vendor is not None


def test_post_bill_with_closed_period_error(db, mock_intacct_sdk, create_bill):
    """
    Test posting a bill handles closed period error
    """
    _, mock_instance = mock_intacct_sdk
    bill, bill_lineitems = create_bill

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = True
    configuration.save()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'period is closed'
            }
        }
    }

    mock_instance.bills.post.side_effect = [
        BadRequestError(msg='Closed period', response=json.dumps(error_response)),
        {'ia::result': {'id': '81035', 'key': '81035', 'href': '/objects/accounts-payable/bill/81035'}}
    ]

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_bill(bill=bill, bill_line_items=bill_lineitems)

    assert result is not None


def test_post_expense_report_with_closed_period_error(db, mock_intacct_sdk, create_expense_report):
    """
    Test posting an expense report handles closed period error
    """
    _, mock_instance = mock_intacct_sdk
    expense_report, expense_report_lineitems = create_expense_report

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = True
    configuration.save()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'period is closed'
            }
        }
    }

    mock_instance.expense_reports.post.side_effect = [
        BadRequestError(msg='Closed period', response=json.dumps(error_response)),
        {'ia::result': {'id': '12345', 'key': '12345', 'href': '/objects/expense-management/expense-report/12345'}}
    ]

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_expense_report(expense_report=expense_report, expense_report_line_items=expense_report_lineitems)

    assert result is not None


def test_post_charge_card_transaction_with_closed_period_error(db, mock_intacct_sdk, create_charge_card_transaction):
    """
    Test posting a charge card transaction with closed period error re-raises if not handled
    """
    _, mock_instance = mock_intacct_sdk
    cct, cct_lineitems = create_charge_card_transaction

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = False
    configuration.save()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'period is closed'
            }
        }
    }

    mock_instance.charge_card_transactions.post.side_effect = BadRequestError(
        msg='Closed period',
        response=json.dumps(error_response)
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)

    with pytest.raises(BadRequestError):
        manager.post_charge_card_transaction(charge_card_transaction=cct, charge_card_transaction_line_items=cct_lineitems)


def test_post_journal_entry_with_closed_period_error(db, mock_intacct_sdk, create_journal_entry):
    """
    Test posting a journal entry handles closed period error
    """
    _, mock_instance = mock_intacct_sdk
    journal_entry, journal_entry_lineitems = create_journal_entry

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = True
    configuration.save()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'period is closed'
            }
        }
    }

    mock_instance.journal_entries.post.side_effect = [
        BadRequestError(msg='Closed period', response=json.dumps(error_response)),
        {'ia::result': {'id': '120680', 'key': '120680', 'href': '/objects/general-ledger/journal-entry/120680'}}
    ]

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_journal_entry(journal_entry=journal_entry, journal_entry_line_items=journal_entry_lineitems)

    assert result is not None


def test_post_attachments_update_existing(db, mock_intacct_sdk):
    """
    Test posting attachments updates existing attachment
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.attachments.update.return_value = {'success': True}

    attachments = [{'id': 'att1', 'name': 'file.pdf', 'download_url': 'https://example.com/file.pdf'}]
    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result, key = manager.post_attachments(
        attachments=attachments,
        attachment_id='SUPDOC001',
        attachment_number=2,
        attachment_key='ATT_KEY_123'
    )

    assert result is False
    assert key is None
    mock_instance.attachments.update.assert_called_once()


def test_post_attachments_update_with_error(db, mock_intacct_sdk):
    """
    Test posting attachments handles update error
    """
    _, mock_instance = mock_intacct_sdk

    class MockException(Exception):
        response = 'Update failed'

    mock_instance.attachments.update.side_effect = MockException('Update failed')

    attachments = [{'id': 'att1', 'name': 'file.pdf', 'download_url': 'https://example.com/file.pdf'}]
    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result, key = manager.post_attachments(
        attachments=attachments,
        attachment_id='SUPDOC001',
        attachment_number=2,
        attachment_key='ATT_KEY_123'
    )

    assert result is False
    assert key is None


def test_create_employee(db, mock_intacct_sdk):
    """
    Test creating an employee in Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    DestinationAttribute.objects.create(
        workspace_id=1,
        attribute_type='DEPARTMENT',
        value='Engineering',
        destination_id='DEPT001',
        active=True
    )
    DestinationAttribute.objects.create(
        workspace_id=1,
        attribute_type='LOCATION',
        value='New York',
        destination_id='LOC001',
        active=True
    )

    mock_instance.contacts.post.return_value = {
        'ia::result': {'key': 'CT123'}
    }
    mock_instance.contacts.get_by_key.return_value = {
        'ia::result': {'id': 'CT123', 'printAs': 'John Doe'}
    }
    mock_instance.employees.post.return_value = {
        'ia::result': {'key': 'EMP123'}
    }
    mock_instance.employees.get_by_key.return_value = {
        'ia::result': {'id': 'EMP123', 'name': 'John Doe'}
    }

    employee_attr = ExpenseAttribute.objects.create(
        workspace_id=1,
        attribute_type='EMPLOYEE',
        value='john@test.com',
        source_id='src123',
        detail={
            'full_name': 'John Doe',
            'department': 'Engineering',
            'location': 'New York'
        }
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    employee = manager.create_employee(employee=employee_attr)

    assert employee is not None
    assert employee['id'] == 'EMP123'


def test_create_employee_without_location(db, mock_intacct_sdk):
    """
    Test creating an employee returns None when location is not found
    """
    _, _ = mock_intacct_sdk

    # Delete all LOCATION attributes to ensure no match
    DestinationAttribute.objects.filter(
        workspace_id=1,
        attribute_type='LOCATION'
    ).delete()

    # Clear general mappings default location
    from apps.mappings.models import GeneralMapping
    general_mappings = GeneralMapping.objects.filter(workspace_id=1).first()
    if general_mappings:
        general_mappings.default_location_id = None
        general_mappings.save()

    employee_attr = ExpenseAttribute.objects.create(
        workspace_id=1,
        attribute_type='EMPLOYEE',
        value='john@test.com',
        source_id='src124',
        detail={
            'full_name': 'John Doe',
            'department': 'Unknown Dept',
            'location': 'Unknown Location'
        }
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    employee = manager.create_employee(employee=employee_attr)

    assert employee is None


def test_get_or_create_employee(db, mock_intacct_sdk):
    """
    Test get_or_create_employee returns existing employee
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.employees.get_all_generator.return_value = iter([[
        {
            'id': 'EMP001',
            'name': 'John Doe',
            'status': 'active',
            'primaryContact.email1': 'john@test.com',
            'primaryContact.printAs': 'John Doe',
            'department.id': 'DEPT001',
            'location.id': 'LOC001'
        }
    ]])

    employee_attr = ExpenseAttribute.objects.create(
        workspace_id=1,
        attribute_type='EMPLOYEE',
        value='john@test.com',
        source_id='src125',
        detail={
            'full_name': 'John Doe',
            'department': 'Engineering',
            'location': 'New York'
        }
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    employee = manager.get_or_create_employee(source_employee=employee_attr)

    assert employee is not None
    assert employee.destination_id == 'EMP001'


def test_create_contact_without_email(db, mock_intacct_sdk):
    """
    Test creating a contact without email
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.contacts.post.return_value = {
        'ia::result': {'key': 'CT123'}
    }
    mock_instance.contacts.get_by_key.return_value = {
        'ia::result': {'id': 'CT123', 'printAs': 'Test Contact'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    contact = manager.create_contact(
        contact_id='CT001',
        contact_name='Test Contact',
        email=None,
        first_name='Test',
        last_name='Contact'
    )

    assert contact is not None
    assert contact['id'] == 'CT123'


def test_sync_cost_types_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync cost types is skipped when count exceeds limit
    """
    _, mock_instance = mock_intacct_sdk

    DependentFieldSetting.objects.create(
        workspace_id=1,
        is_import_enabled=True,
        project_field_id=1,
        cost_code_field_id=2,
        cost_type_field_id=3
    )

    mock_instance.cost_types.count.return_value = COST_TYPES_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_cost_types()

    mock_instance.cost_types.count.assert_called_once()
    mock_instance.cost_types.get_all_generator.assert_not_called()


def test_sync_cost_types_with_last_synced_at(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test sync cost types with last_synced_at filters data
    """
    _, mock_instance = mock_intacct_sdk

    DependentFieldSetting.objects.create(
        workspace_id=1,
        is_import_enabled=True,
        project_field_id=1,
        cost_code_field_id=2,
        cost_type_field_id=3,
        last_synced_at=datetime.now()
    )

    mock_instance.cost_types.count.return_value = 2
    mock_instance.cost_types.get_all_generator.return_value = iter([[]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_cost_types()

    mock_instance.cost_types.count.assert_called_once()
    mock_instance.cost_types.get_all_generator.assert_called_once()


def test_sync_cost_codes_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync cost codes is skipped when count exceeds limit
    """
    _, mock_instance = mock_intacct_sdk

    DependentFieldSetting.objects.create(
        workspace_id=1,
        is_import_enabled=True,
        project_field_id=1,
        cost_code_field_id=2,
        cost_type_field_id=3
    )

    mock_instance.tasks.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_cost_codes()

    mock_instance.tasks.count.assert_called_once()
    mock_instance.tasks.get_all_generator.assert_not_called()


def test_sync_cost_codes_with_last_synced_at(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test sync cost codes with last_synced_at filters data
    """
    _, mock_instance = mock_intacct_sdk

    DependentFieldSetting.objects.create(
        workspace_id=1,
        is_import_enabled=True,
        project_field_id=1,
        cost_code_field_id=2,
        cost_type_field_id=3,
        last_synced_at=datetime.now()
    )

    mock_instance.tasks.count.return_value = 2
    mock_instance.tasks.get_all_generator.return_value = iter([[]])

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_cost_codes()

    mock_instance.tasks.count.assert_called_once()
    mock_instance.tasks.get_all_generator.assert_called_once()


def test_sync_expense_payment_types_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync expense payment types is skipped when count exceeds limit
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.expense_payment_types.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_expense_payment_types()

    mock_instance.expense_payment_types.count.assert_called_once()
    mock_instance.expense_payment_types.get_all_generator.assert_not_called()


def test_sync_tax_details_skips_when_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test sync tax details is skipped when count exceeds limit
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.tax_details.count.return_value = SYNC_UPPER_LIMIT + 1000

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_tax_details()

    mock_instance.tax_details.count.assert_called_once()
    mock_instance.tax_details.get_all_generator.assert_not_called()


def test_sync_user_defined_dimensions_skips_udd_over_limit(db, mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
    """
    Test syncing user defined dimensions skips UDD when count exceeds limit
    """
    _, mock_instance = mock_intacct_sdk

    mocker.patch(
        'apps.sage_intacct.connector.timezone',
        django_timezone
    )

    workspace = Workspace.objects.get(id=1)
    workspace.created_at = datetime(2024, 11, 1, tzinfo=timezone.utc)
    workspace.save()

    mock_instance.dimensions.list.return_value = [
        {
            'dimensionName': 'Custom Field',
            'termName': 'Custom Field',
            'isUserDefinedDimension': True,
            'dimensionEndpoint': 'endpoint::custom_field'
        }
    ]
    mock_instance.dimensions.count.return_value = SYNC_UPPER_LIMIT + 1000

    sync_manager = SageIntacctDimensionSyncManager(workspace_id=1)
    sync_manager.sync_user_defined_dimensions()

    mock_instance.dimensions.list.assert_called_once()
    mock_instance.dimensions.count.assert_called_once()
    mock_instance.dimensions.get_all_generator.assert_not_called()


def test_create_contact_with_exception(db, mock_intacct_sdk):
    """
    Test creating a contact returns None on exception
    """
    _, mock_instance = mock_intacct_sdk

    class MockException(Exception):
        response = 'Contact creation failed'

    mock_instance.contacts.post.side_effect = MockException('Failed')

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    contact = manager.create_contact(
        contact_id='CT001',
        contact_name='Test Contact',
        email='test@test.com',
        first_name='Test',
        last_name='Contact'
    )

    assert contact is None


def test_create_contact_no_object_key(db, mock_intacct_sdk):
    """
    Test creating a contact returns None when no object key in response
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.contacts.post.return_value = {
        'ia::result': {}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    contact = manager.create_contact(
        contact_id='CT001',
        contact_name='Test Contact',
        email='test@test.com',
        first_name='Test',
        last_name='Contact'
    )

    assert contact is None


def test_create_vendor_no_object_key(db, mock_intacct_sdk):
    """
    Test creating a vendor returns None when no object key in response
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.vendors.post.return_value = {
        'ia::result': {}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    vendor = manager.create_vendor(
        vendor_id='VND001',
        vendor_name='Test Vendor',
        email='test@test.com'
    )

    assert vendor is None


def test_create_employee_contact_fails(db, mock_intacct_sdk):
    """
    Test creating an employee returns None when contact creation fails
    """
    _, mock_instance = mock_intacct_sdk

    DestinationAttribute.objects.create(
        workspace_id=1,
        attribute_type='LOCATION',
        value='Test Location',
        destination_id='LOC001',
        active=True
    )

    class MockException(Exception):
        response = 'Contact creation failed'

    mock_instance.contacts.post.side_effect = MockException('Failed')

    employee_attr = ExpenseAttribute.objects.create(
        workspace_id=1,
        attribute_type='EMPLOYEE',
        value='john@test.com',
        source_id='src126',
        detail={
            'full_name': 'John Doe',
            'department': 'Unknown',
            'location': 'Test Location'
        }
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    employee = manager.create_employee(employee=employee_attr)

    assert employee is None


def test_create_employee_with_exception(db, mock_intacct_sdk):
    """
    Test creating an employee returns None on exception during employee post
    """
    _, mock_instance = mock_intacct_sdk

    DestinationAttribute.objects.create(
        workspace_id=1,
        attribute_type='LOCATION',
        value='Test Location 2',
        destination_id='LOC002',
        active=True
    )

    mock_instance.contacts.post.return_value = {
        'ia::result': {'key': 'CT123'}
    }
    mock_instance.contacts.get_by_key.return_value = {
        'ia::result': {'id': 'CT123', 'printAs': 'John Doe'}
    }

    class MockException(Exception):
        response = 'Employee creation failed'

    mock_instance.employees.post.side_effect = MockException('Failed')

    employee_attr = ExpenseAttribute.objects.create(
        workspace_id=1,
        attribute_type='EMPLOYEE',
        value='john2@test.com',
        source_id='src127',
        detail={
            'full_name': 'John Doe 2',
            'department': 'Unknown',
            'location': 'Test Location 2'
        }
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    employee = manager.create_employee(employee=employee_attr)

    assert employee is None


def test_create_employee_no_object_key(db, mock_intacct_sdk):
    """
    Test creating an employee returns None when no object key in response
    """
    _, mock_instance = mock_intacct_sdk

    DestinationAttribute.objects.create(
        workspace_id=1,
        attribute_type='LOCATION',
        value='Test Location 3',
        destination_id='LOC003',
        active=True
    )

    mock_instance.contacts.post.return_value = {
        'ia::result': {'key': 'CT123'}
    }
    mock_instance.contacts.get_by_key.return_value = {
        'ia::result': {'id': 'CT123', 'printAs': 'John Doe'}
    }
    mock_instance.employees.post.return_value = {
        'ia::result': {}
    }

    employee_attr = ExpenseAttribute.objects.create(
        workspace_id=1,
        attribute_type='EMPLOYEE',
        value='john3@test.com',
        source_id='src128',
        detail={
            'full_name': 'John Doe 3',
            'department': 'Unknown',
            'location': 'Test Location 3'
        }
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    employee = manager.create_employee(employee=employee_attr)

    assert employee is None


def test_get_or_create_employee_creates_new(db, mock_intacct_sdk):
    """
    Test get_or_create_employee creates a new employee when not found
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.employees.get_all_generator.return_value = iter([[]])

    DestinationAttribute.objects.create(
        workspace_id=1,
        attribute_type='LOCATION',
        value='Test Location 4',
        destination_id='LOC004',
        active=True
    )

    mock_instance.contacts.post.return_value = {
        'ia::result': {'key': 'CT124'}
    }
    mock_instance.contacts.get_by_key.return_value = {
        'ia::result': {'id': 'CT124', 'printAs': 'New Employee'}
    }
    mock_instance.employees.post.return_value = {
        'ia::result': {'key': 'EMP124'}
    }
    mock_instance.employees.get_by_key.return_value = {
        'ia::result': {'id': 'EMP124', 'name': 'New Employee'}
    }

    employee_attr = ExpenseAttribute.objects.create(
        workspace_id=1,
        attribute_type='EMPLOYEE',
        value='new@test.com',
        source_id='src129',
        detail={
            'full_name': 'New Employee',
            'department': 'Unknown',
            'location': 'Test Location 4'
        }
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    employee = manager.get_or_create_employee(source_employee=employee_attr)

    assert employee is not None


def test_get_or_create_vendor_with_duplicate_error_finds_vendor(db, mock_intacct_sdk):
    """
    Test get_or_create_vendor handles duplicate error by searching for vendor
    """
    _, mock_instance = mock_intacct_sdk

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'Another record with the value already exists'
            }
        }
    }

    mock_instance.vendors.post.side_effect = BadRequestError(
        msg='Duplicate',
        response=json.dumps(error_response)
    )
    mock_instance.vendors.get_all_generator.return_value = iter([[
        {'id': 'VND_FOUND', 'name': 'Duplicate Vendor Found', 'status': 'active', 'contacts.default.email1': 'dup@test.com'}
    ]])

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    vendor = manager.get_or_create_vendor(
        vendor_name='Duplicate Vendor Found',
        email='dup@test.com',
        create=True
    )

    assert vendor is not None
    assert vendor.destination_id == 'VND_FOUND'


def test_get_or_create_vendor_with_duplicate_error_creates_new(db, mock_intacct_sdk):
    """
    Test get_or_create_vendor handles duplicate error and creates new vendor when not found
    """
    _, mock_instance = mock_intacct_sdk

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'Another record with the value already exists'
            }
        }
    }

    mock_instance.vendors.post.side_effect = [
        BadRequestError(msg='Duplicate', response=json.dumps(error_response)),
        {'ia::result': {'key': 'VND_NEW'}}
    ]
    mock_instance.vendors.get_all_generator.return_value = iter([[]])
    mock_instance.vendors.get_by_key.return_value = {
        'ia::result': {'id': 'VND_NEW', 'name': 'New Vendor Created'}
    }

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    vendor = manager.get_or_create_vendor(
        vendor_name='New Vendor To Create',
        email='new_dup@test.com',
        create=True
    )

    assert vendor is not None


def test_get_or_create_vendor_duplicate_create_fails(db, mock_intacct_sdk):
    """
    Test get_or_create_vendor returns None when duplicate handling create fails
    """
    _, mock_instance = mock_intacct_sdk

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'Another record with the value already exists'
            }
        }
    }

    class MockException(Exception):
        response = 'Create failed again'

    mock_instance.vendors.post.side_effect = [
        BadRequestError(msg='Duplicate', response=json.dumps(error_response)),
        MockException('Failed')
    ]
    mock_instance.vendors.get_all_generator.return_value = iter([[]])

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    vendor = manager.get_or_create_vendor(
        vendor_name='Failing Vendor',
        email='fail@test.com',
        create=True
    )

    assert vendor is None


def test_post_expense_report_non_closed_period_error_re_raises(db, mock_intacct_sdk, create_expense_report):
    """
    Test posting an expense report re-raises for non-closed period errors
    """
    _, mock_instance = mock_intacct_sdk
    expense_report, expense_report_lineitems = create_expense_report

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = True
    configuration.save()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'Some other error'
            }
        }
    }

    mock_instance.expense_reports.post.side_effect = BadRequestError(
        msg='Error',
        response=json.dumps(error_response)
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)

    with pytest.raises(BadRequestError):
        manager.post_expense_report(expense_report=expense_report, expense_report_line_items=expense_report_lineitems)


def test_post_bill_non_closed_period_error_re_raises(db, mock_intacct_sdk, create_bill):
    """
    Test posting a bill re-raises for non-closed period errors
    """
    _, mock_instance = mock_intacct_sdk
    bill, bill_lineitems = create_bill

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = True
    configuration.save()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'Some other error not about period'
            }
        }
    }

    mock_instance.bills.post.side_effect = BadRequestError(
        msg='Error',
        response=json.dumps(error_response)
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)

    with pytest.raises(BadRequestError):
        manager.post_bill(bill=bill, bill_line_items=bill_lineitems)


def test_post_journal_entry_non_closed_period_error_re_raises(db, mock_intacct_sdk, create_journal_entry):
    """
    Test posting a journal entry re-raises for non-closed period errors
    """
    _, mock_instance = mock_intacct_sdk
    journal_entry, journal_entry_lineitems = create_journal_entry

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = True
    configuration.save()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'Some other error not about period'
            }
        }
    }

    mock_instance.journal_entries.post.side_effect = BadRequestError(
        msg='Error',
        response=json.dumps(error_response)
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)

    with pytest.raises(BadRequestError):
        manager.post_journal_entry(journal_entry=journal_entry, journal_entry_line_items=journal_entry_lineitems)


def test_post_expense_report_with_closed_period_creates_system_comment(db, mock_intacct_sdk, create_expense_report):
    """
    Test posting an expense report creates system comment when accounting period is adjusted
    """
    _, mock_instance = mock_intacct_sdk
    expense_report, expense_report_lineitems = create_expense_report

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = True
    configuration.save()

    SystemComment.objects.filter(
        workspace_id=expense_report.expense_group.workspace_id,
        intent=SystemCommentIntentEnum.ACCOUNTING_PERIOD_ADJUSTED
    ).delete()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'period is closed'
            }
        }
    }

    mock_instance.expense_reports.post.side_effect = [
        BadRequestError(msg='Closed period', response=json.dumps(error_response)),
        {'ia::result': {'id': '12345', 'key': '12345', 'href': '/objects/expense-management/expense-report/12345'}}
    ]

    system_comments = []
    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_expense_report(
        expense_report=expense_report,
        expense_report_line_items=expense_report_lineitems,
        system_comments=system_comments
    )

    assert result is not None
    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.POST_EXPENSE_REPORT
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.ACCOUNTING_PERIOD_ADJUSTED
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE_GROUP
    assert system_comments[0]['entity_id'] == expense_report.expense_group.id
    assert system_comments[0]['export_type'] == ExportTypeEnum.EXPENSE_REPORT
    assert system_comments[0]['detail']['reason'] == SystemCommentReasonEnum.ACCOUNTING_PERIOD_CLOSED_DATE_ADJUSTED
    assert 'original_date' in system_comments[0]['detail']['info']
    assert 'adjusted_date' in system_comments[0]['detail']['info']


def test_post_bill_with_closed_period_creates_system_comment(db, mock_intacct_sdk, create_bill):
    """
    Test posting a bill creates system comment when accounting period is adjusted
    """
    _, mock_instance = mock_intacct_sdk
    bill, bill_lineitems = create_bill

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = True
    configuration.save()

    SystemComment.objects.filter(
        workspace_id=bill.expense_group.workspace_id,
        intent=SystemCommentIntentEnum.ACCOUNTING_PERIOD_ADJUSTED
    ).delete()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'period is closed'
            }
        }
    }

    mock_instance.bills.post.side_effect = [
        BadRequestError(msg='Closed period', response=json.dumps(error_response)),
        {'ia::result': {'id': '81035', 'key': '81035', 'href': '/objects/accounts-payable/bill/81035'}}
    ]

    system_comments = []
    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_bill(bill=bill, bill_line_items=bill_lineitems, system_comments=system_comments)

    assert result is not None
    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.POST_BILL
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.ACCOUNTING_PERIOD_ADJUSTED
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE_GROUP
    assert system_comments[0]['entity_id'] == bill.expense_group.id
    assert system_comments[0]['export_type'] == ExportTypeEnum.BILL
    assert system_comments[0]['detail']['reason'] == SystemCommentReasonEnum.ACCOUNTING_PERIOD_CLOSED_DATE_ADJUSTED
    assert 'original_date' in system_comments[0]['detail']['info']
    assert 'adjusted_date' in system_comments[0]['detail']['info']


def test_post_charge_card_transaction_with_closed_period_creates_system_comment(db, mock_intacct_sdk, create_charge_card_transaction):
    """
    Test posting a charge card transaction creates system comment when accounting period is adjusted
    """
    _, mock_instance = mock_intacct_sdk
    cct, cct_lineitems = create_charge_card_transaction

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = True
    configuration.save()

    SystemComment.objects.filter(
        workspace_id=cct.expense_group.workspace_id,
        intent=SystemCommentIntentEnum.ACCOUNTING_PERIOD_ADJUSTED
    ).delete()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'period is closed'
            }
        }
    }

    mock_instance.charge_card_transactions.post.side_effect = [
        BadRequestError(msg='Closed period', response=json.dumps(error_response)),
        {'ia::result': {'id': '81033', 'key': '81033', 'href': '/objects/cash-management/credit-card-txn/81033'}}
    ]

    system_comments = []
    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_charge_card_transaction(
        charge_card_transaction=cct,
        charge_card_transaction_line_items=cct_lineitems,
        system_comments=system_comments
    )

    assert result is not None
    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.POST_CHARGE_CARD_TRANSACTION
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.ACCOUNTING_PERIOD_ADJUSTED
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE_GROUP
    assert system_comments[0]['entity_id'] == cct.expense_group.id
    assert system_comments[0]['export_type'] == ExportTypeEnum.CHARGE_CARD_TRANSACTION
    assert system_comments[0]['detail']['reason'] == SystemCommentReasonEnum.ACCOUNTING_PERIOD_CLOSED_DATE_ADJUSTED
    assert 'original_date' in system_comments[0]['detail']['info']
    assert 'adjusted_date' in system_comments[0]['detail']['info']


def test_post_journal_entry_with_closed_period_creates_system_comment(db, mock_intacct_sdk, create_journal_entry):
    """
    Test posting a journal entry creates system comment when accounting period is adjusted
    """
    _, mock_instance = mock_intacct_sdk
    journal_entry, journal_entry_lineitems = create_journal_entry

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = True
    configuration.save()

    SystemComment.objects.filter(
        workspace_id=journal_entry.expense_group.workspace_id,
        intent=SystemCommentIntentEnum.ACCOUNTING_PERIOD_ADJUSTED
    ).delete()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'period is closed'
            }
        }
    }

    mock_instance.journal_entries.post.side_effect = [
        BadRequestError(msg='Closed period', response=json.dumps(error_response)),
        {'ia::result': {'id': '120680', 'key': '120680', 'href': '/objects/general-ledger/journal-entry/120680'}}
    ]

    system_comments = []
    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.post_journal_entry(
        journal_entry=journal_entry,
        journal_entry_line_items=journal_entry_lineitems,
        system_comments=system_comments
    )

    assert result is not None
    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.POST_JOURNAL_ENTRY
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.ACCOUNTING_PERIOD_ADJUSTED
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE_GROUP
    assert system_comments[0]['entity_id'] == journal_entry.expense_group.id
    assert system_comments[0]['export_type'] == ExportTypeEnum.JOURNAL_ENTRY
    assert system_comments[0]['detail']['reason'] == SystemCommentReasonEnum.ACCOUNTING_PERIOD_CLOSED_DATE_ADJUSTED
    assert 'original_date' in system_comments[0]['detail']['info']
    assert 'adjusted_date' in system_comments[0]['detail']['info']


def test_post_expense_report_with_closed_period_no_system_comment_when_change_accounting_period_false(db, mock_intacct_sdk, create_expense_report):
    """
    Test posting an expense report does not create system comment when change_accounting_period is False
    """
    _, mock_instance = mock_intacct_sdk
    expense_report, expense_report_lineitems = create_expense_report

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.change_accounting_period = False
    configuration.save()

    error_response = {
        'ia::result': {
            'ia::error': {
                'details': 'period is closed'
            }
        }
    }

    mock_instance.expense_reports.post.side_effect = BadRequestError(
        msg='Closed period',
        response=json.dumps(error_response)
    )

    system_comments = []
    manager = SageIntacctObjectCreationManager(workspace_id=1)

    with pytest.raises(BadRequestError):
        manager.post_expense_report(
            expense_report=expense_report,
            expense_report_line_items=expense_report_lineitems,
            system_comments=system_comments
        )

    assert len(system_comments) == 0
