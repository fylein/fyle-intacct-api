import pytest
from datetime import datetime, timezone, timedelta
from django.utils import timezone as django_timezone

from fyle_accounting_mappings.models import DestinationAttribute

from apps.sage_intacct.connector import (
    SageIntacctRestConnector,
    SageIntacctDimensionSyncManager,
    SageIntacctObjectCreationManager,
    SYNC_UPPER_LIMIT,
)
from apps.workspaces.models import (
    Workspace,
    SageIntacctCredential,
)


@pytest.mark.django_db
def test_sage_intacct_rest_connector_init(mock_intacct_sdk):
    """
    Test SageIntacctRestConnector initialization
    """
    _, mock_instance = mock_intacct_sdk
    mock_instance.sessions.get_session_id.return_value = {'sessionId': 'mock_session_id'}

    connector = SageIntacctRestConnector(workspace_id=1)

    assert connector.workspace_id == 1
    assert connector.connection is not None


@pytest.mark.django_db
def test_sage_intacct_rest_connector_get_session_id(mock_intacct_sdk):
    """
    Test getting session id
    """
    _, mock_instance = mock_intacct_sdk
    mock_instance.sessions.get_session_id.return_value = {'sessionId': 'test_session_123'}

    connector = SageIntacctRestConnector(workspace_id=1)
    session_id = connector.get_session_id()

    assert session_id == 'test_session_123'


@pytest.mark.django_db
def test_sage_intacct_rest_connector_get_soap_connection(mock_intacct_sdk, mock_sage_intacct_sdk):
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


@pytest.mark.django_db
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


# ---------------------
# SageIntacctDimensionSyncManager Tests
# ---------------------

@pytest.mark.django_db
def test_sync_accounts(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_accounts_skips_when_over_limit(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
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


@pytest.mark.django_db
def test_sync_departments(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_expense_types(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count, mocker):
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


@pytest.mark.django_db
def test_sync_vendors(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_employees(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_projects(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_customers(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_classes(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_locations(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_items(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_tax_details(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_payment_accounts(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_charge_card_accounts(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_expense_payment_types(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_user_defined_dimensions(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_sync_allocations(mock_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
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


@pytest.mark.django_db
def test_get_bills(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_get_expense_reports(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_sync_location_entities(mock_intacct_sdk, mock_sage_intacct_sdk, create_intacct_synced_timestamp, create_sage_intacct_attributes_count):
    """
    Test syncing location entities from Sage Intacct
    """
    mock_rest_sdk_class, mock_rest_instance = mock_intacct_sdk
    mock_soap_sdk_class, mock_soap_instance = mock_sage_intacct_sdk

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


@pytest.mark.django_db
def test_create_vendor(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_create_contact(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_get_or_create_vendor_existing(mock_intacct_sdk):
    """
    Test get_or_create_vendor returns existing vendor from database
    """
    _, mock_instance = mock_intacct_sdk

    # Create a vendor in database
    DestinationAttribute.objects.create(
        workspace_id=1,
        attribute_type='VENDOR',
        value='Existing Vendor',
        destination_id='VND_EXISTING',
        active=True
    )

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    vendor = manager.get_or_create_vendor(vendor_name='Existing Vendor')

    assert vendor is not None
    assert vendor.destination_id == 'VND_EXISTING'


@pytest.mark.django_db
def test_get_or_create_vendor_create_new(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_search_and_create_vendors(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_post_bill(mock_intacct_sdk, create_bill):
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


@pytest.mark.django_db
def test_post_expense_report(mock_intacct_sdk, create_expense_report):
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


@pytest.mark.django_db
def test_post_charge_card_transaction(mock_intacct_sdk, create_charge_card_transaction):
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


@pytest.mark.django_db
def test_post_journal_entry(mock_intacct_sdk, create_journal_entry):
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


@pytest.mark.django_db
def test_post_ap_payment(mock_intacct_sdk, create_ap_payment):
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


@pytest.mark.django_db
def test_post_sage_intacct_reimbursement(mock_intacct_sdk, mock_sage_intacct_sdk, create_sage_intacct_reimbursement):
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


@pytest.mark.django_db
def test_get_or_create_attachments_folder(mock_intacct_sdk):
    """
    Test getting or creating attachments folder
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.attachment_folders.get_all_generator.return_value = iter([[]])
    mock_instance.attachment_folders.post.return_value = {'ia::result': {'key': 'FOLDER1'}}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    manager.get_or_create_attachments_folder()

    mock_instance.attachment_folders.get_all_generator.assert_called_once()


@pytest.mark.django_db
def test_post_attachments(mock_intacct_sdk):
    """
    Test posting attachments to Sage Intacct
    """
    _, mock_instance = mock_intacct_sdk

    mock_instance.attachments.post.return_value = {
        'ia::result': {'key': 'ATT123'}
    }

    attachments = [{'id': 'att1', 'download_url': 'https://example.com/file.pdf'}]
    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result, key = manager.post_attachments(
        attachments=attachments,
        attachment_id='SUPDOC001',
        attachment_number=1
    )

    assert result == 'SUPDOC001'
    assert key == 'ATT123'


@pytest.mark.django_db
def test_post_attachments_empty(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_update_expense_report_attachments(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_update_bill_attachments(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_update_charge_card_transaction_attachments(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_update_journal_entry_attachments(mock_intacct_sdk):
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


@pytest.mark.django_db
def test_get_journal_entry(mock_intacct_sdk, mock_sage_intacct_sdk):
    """
    Test getting journal entry from Sage Intacct
    """
    mock_rest_sdk_class, mock_rest_instance = mock_intacct_sdk
    mock_soap_sdk_class, mock_soap_instance = mock_sage_intacct_sdk

    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'test'}
    mock_soap_instance.journal_entries.get.return_value = {'recordno': '123'}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.get_journal_entry(journal_entry_id='123')

    assert result is not None


@pytest.mark.django_db
def test_get_charge_card_transaction(mock_intacct_sdk, mock_sage_intacct_sdk):
    """
    Test getting charge card transaction from Sage Intacct
    """
    mock_rest_sdk_class, mock_rest_instance = mock_intacct_sdk
    mock_soap_sdk_class, mock_soap_instance = mock_sage_intacct_sdk

    mock_rest_instance.sessions.get_session_id.return_value = {'sessionId': 'test'}
    mock_soap_instance.charge_card_transactions.get.return_value = {'recordno': '123'}

    manager = SageIntacctObjectCreationManager(workspace_id=1)
    result = manager.get_charge_card_transaction(charge_card_transaction_id='123')

    assert result is not None


@pytest.mark.django_db
def test_get_bill(mock_intacct_sdk, mock_sage_intacct_sdk):
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


@pytest.mark.django_db
def test_get_expense_report(mock_intacct_sdk, mock_sage_intacct_sdk):
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
