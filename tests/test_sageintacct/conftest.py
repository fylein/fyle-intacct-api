import pytest
from unittest import mock

from datetime import datetime

from fyle_accounting_mappings.models import ExpenseAttribute, DestinationAttribute

from apps.tasks.models import TaskLog
from apps.mappings.models import GeneralMapping
from apps.workspaces.models import Configuration, Workspace, IntacctSyncedTimestamp
from apps.fyle.models import (
    Expense,
    ExpenseGroup,
    DependentFieldSetting,
)
from apps.sage_intacct.models import (
    Bill,
    BillLineitem,
    ExpenseReport,
    ExpenseReportLineitem,
    JournalEntry,
    JournalEntryLineitem,
    SageIntacctReimbursement,
    SageIntacctReimbursementLineitem,
    ChargeCardTransaction,
    ChargeCardTransactionLineitem,
    APPayment,
    APPaymentLineitem,
    CostType,
    SageIntacctAttributesCount,
)


@pytest.fixture
def create_bill(db):
    """
    Create bill and bill lineitems
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    bill = Bill.create_bill(expense_group)
    bill_lineitems = BillLineitem.create_bill_lineitems(expense_group, workspace_general_settings)

    return bill, bill_lineitems


@pytest.fixture
def create_expense_report(db, mocker):
    """
    Create expense report and expense report lineitems
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    expense_report = ExpenseReport.create_expense_report(expense_group)
    mocker.patch('apps.sage_intacct.models.import_string', return_value=lambda *args, **kwargs: (None, False))
    expense_report_lineitems = ExpenseReportLineitem.create_expense_report_lineitems(expense_group, workspace_general_settings)

    return expense_report,expense_report_lineitems


@pytest.fixture
def create_journal_entry(db, mocker):
    """
    Create journal entry and journal entry lineitems
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    journal_entry = JournalEntry.create_journal_entry(expense_group)
    sage_intacct_connection = mocker.patch('apps.sage_intacct.utils.SageIntacctConnector')
    sage_intacct_connection.return_value = mocker.Mock()
    journal_entry_lineitems = JournalEntryLineitem.create_journal_entry_lineitems(expense_group,workspace_general_settings, sage_intacct_connection)

    return journal_entry,journal_entry_lineitems


@pytest.fixture
def create_sage_intacct_reimbursement(db):
    """
    Create sage intacct reimbursement and lineitems
    """
    expense_group = ExpenseGroup.objects.get(id=1)
    sage_intacct_reimbursement = SageIntacctReimbursement.create_sage_intacct_reimbursement(expense_group)
    intacct_reimbursement_lineitems = SageIntacctReimbursementLineitem.create_sage_intacct_reimbursement_lineitems(expense_group, '3032')

    return sage_intacct_reimbursement,intacct_reimbursement_lineitems


@pytest.fixture
def create_charge_card_transaction(db, mocker):
    """
    Create charge card transaction and lineitems
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    expense_group.description.update({'employee_email': 'user4444@fyleforgotham.in'})
    expense_group.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_charge_card_id = 'sample'
    general_mappings.save()

    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    charge_card_transaction = ChargeCardTransaction.create_charge_card_transaction(expense_group, 'Yash')
    mocker.patch('apps.sage_intacct.models.import_string', return_value=lambda *args, **kwargs: (None, False))
    charge_card_transaction_lineitems = ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(expense_group, workspace_general_settings)

    return charge_card_transaction,charge_card_transaction_lineitems


@pytest.fixture
def create_ap_payment(db):
    """
    Create AP payment and lineitems
    """
    expense_group = ExpenseGroup.objects.get(id=1)
    ap_payment = APPayment.create_ap_payment(expense_group)
    ap_payment_lineitems = APPaymentLineitem.create_ap_payment_lineitems(expense_group, '3032')

    return ap_payment, ap_payment_lineitems


@pytest.fixture
def create_task_logs(db):
    """
    Create task logs
    """
    workspace_id = 1

    TaskLog.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_EXPENSES',
        defaults={
            'status': 'READY'
        }
    )


@pytest.fixture
def create_cost_type(db):
    """
    Create cost type
    """
    workspace_id = 1
    CostType.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'record_number': '34234',
            'project_key': 34,
            'project_id': 'pro1',
            'project_name': 'pro',
            'task_key': 34,
            'task_id': 'task1',
            'task_name': 'task',
            'status': 'ACTIVE',
            'cost_type_id': 'cost1',
            'name': 'cost'
        }
    )
    ExpenseAttribute.objects.create(
        attribute_type='PROJECT',
        value='pro',
        display_name='project',
        source_id='pro1',
        workspace_id=workspace_id
    )
    ExpenseAttribute.objects.create(
        attribute_type='COST_CODE',
        value='task',
        display_name='cost code',
        source_id='task1',
        workspace_id=workspace_id
    )


@pytest.fixture
def create_dependent_field_setting(db):
    """
    Create dependent field setting
    """
    created_field, _ = DependentFieldSetting.objects.update_or_create(
        workspace_id=1,
        defaults={
            'is_import_enabled': True,
            'project_field_id': 123,
            'cost_code_field_name': 'Cost Code',
            'cost_code_field_id': 456,
            'cost_type_field_name': 'Cost Type',
            'cost_type_field_id': 789
        }
    )

    return created_field


@pytest.fixture
def create_expense_group_expense(db):
    """
    Create expense group and expense
    """
    expense_group = ExpenseGroup.objects.create(
        workspace_id=1,
        fund_source='PERSONAL',
        description={}
    )

    expense, _ = Expense.objects.update_or_create(
        expense_id='dummy_id',
        defaults={
            'employee_email': 'employee_email',
            'category': 'category',
            'sub_category': 'sub_category',
            'project': 'pro',
            'expense_number': 'expense_number',
            'org_id': 'org_id',
            'claim_number': 'claim_number',
            'amount': round(123, 2),
            'currency': 'USD',
            'foreign_amount': 123,
            'foreign_currency': 'USD',
            'tax_amount': 123,
            'tax_group_id': 'tax_group_id',
            'settlement_id': 'settlement_id',
            'reimbursable': True,
            'billable': True,
            'state': 'state',
            'vendor': 'vendor',
            'cost_center': 'cost_center',
            'purpose': 'purpose',
            'report_id': 'report_id',
            'report_title': 'report_title',
            'spent_at': datetime.now(),
            'approved_at': datetime.now(),
            'expense_created_at': datetime.now(),
            'expense_updated_at': datetime.now(),
            'fund_source': 'PERSONAL',
            'verified_at': datetime.now(),
            'custom_properties': {'Cost Type': 'cost', 'Cost Code': 'task'},
            'payment_number': 'payment_number',
            'file_ids': [],
            'corporate_card_id': 'corporate_card_id',
        }
    )
    expense_group.expenses.add(expense)

    return expense_group, expense


@pytest.fixture
def create_expense_group_for_allocation(db):
    """
    Create expense group and expense for allocation
    """
    expense_group = ExpenseGroup.objects.create(
        workspace_id=1,
        fund_source='PERSONAL',
        description={'employee_email': 'ashwin.t@fyle.in'}
    )

    expense, _ = Expense.objects.update_or_create(
        expense_id='dummy_id',
        defaults={
            'employee_email': 'ashwin.t@fyle.in',
            'category': 'category',
            'sub_category': 'sub_category',
            'project': 'Aaron Abbott',
            'expense_number': 'expense_number',
            'org_id': 'org_id',
            'claim_number': 'claim_number',
            'amount': round(123, 2),
            'currency': 'USD',
            'foreign_amount': 123,
            'foreign_currency': 'USD',
            'tax_amount': 123,
            'tax_group_id': 'tax_group_id',
            'settlement_id': 'settlement_id',
            'reimbursable': True,
            'billable': True,
            'state': 'state',
            'vendor': 'vendor',
            'cost_center': 'Izio',
            'purpose': 'purpose',
            'report_id': 'report_id',
            'report_title': 'report_title',
            'spent_at': datetime.now(),
            'approved_at': datetime.now(),
            'expense_created_at': datetime.now(),
            'expense_updated_at': datetime.now(),
            'fund_source': 'PERSONAL',
            'verified_at': datetime.now(),
            'custom_properties': {'Cost Type': 'cost', 'Cost Code': 'task'},
            'payment_number': 'payment_number',
            'file_ids': [],
            'corporate_card_id': 'corporate_card_id',
        }
    )
    expense_group.expenses.add(expense)

    return expense_group, expense


@pytest.fixture
def add_project_mappings(db):
    """
    Pytest fixture to add project mappings to a workspace
    """
    workspace_ids = [
        1
    ]
    for workspace_id in workspace_ids:
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Project',
            value='CRE Platform',
            destination_id='10065',
            detail={},
            active=True,
            code='10065'
        )
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Project',
            value='CRE Platform',
            source_id='10065',
            detail={},
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Project',
            value='Direct Mail Campaign',
            destination_id='10064',
            detail={},
            active=True,
            code='10064'
        )


@pytest.fixture
def mock_intacct_sdk():
    """Mock the IntacctRESTSDK"""
    with mock.patch('apps.sage_intacct.connector.IntacctRESTSDK') as mock_sdk:
        mock_instance = mock.Mock()
        mock_instance.access_token = 'mock_access_token'
        mock_instance.access_token_expires_in = 21600
        mock_sdk.return_value = mock_instance
        yield mock_sdk, mock_instance


@pytest.fixture
def mock_sage_intacct_sdk():
    """Mock the SageIntacctSDK"""
    with mock.patch('apps.sage_intacct.connector.SageIntacctSDK') as mock_sdk:
        mock_instance = mock.Mock()
        mock_sdk.return_value = mock_instance
        yield mock_sdk, mock_instance


@pytest.fixture
def create_intacct_synced_timestamp(db):
    """Create IntacctSyncedTimestamp for workspace_id=1"""
    timestamp, _ = IntacctSyncedTimestamp.objects.get_or_create(
        workspace_id=1,
        defaults={
            'account_synced_at': None,
            'vendor_synced_at': None,
            'customer_synced_at': None,
            'class_synced_at': None,
            'employee_synced_at': None,
            'item_synced_at': None,
            'location_synced_at': None,
            'department_synced_at': None,
            'project_synced_at': None,
            'expense_type_synced_at': None,
            'location_entity_synced_at': None,
            'payment_account_synced_at': None,
            'expense_payment_type_synced_at': None,
            'allocation_synced_at': None,
            'tax_detail_synced_at': None,
        }
    )
    return timestamp


@pytest.fixture
def create_sage_intacct_attributes_count(db):
    """Create SageIntacctAttributesCount for workspace_id=1"""
    workspace = Workspace.objects.get(id=1)
    count, _ = SageIntacctAttributesCount.objects.get_or_create(
        workspace=workspace,
        defaults={
            'accounts_count': 0,
            'vendors_count': 0,
        }
    )
    return count


@pytest.fixture
def create_existing_vendor_attribute(db):
    """Create an existing VENDOR DestinationAttribute for testing"""
    attribute = DestinationAttribute.objects.create(
        workspace_id=1,
        attribute_type='VENDOR',
        value='Existing Vendor',
        destination_id='VND_EXISTING',
        active=True
    )
    return attribute


@pytest.fixture
def create_tax_detail_attribute(db):
    """
    Create TAX_DETAIL DestinationAttribute for tax calculations
    """
    workspace_id = 1

    attribute = DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='TAX_DETAIL',
        display_name='Tax Detail',
        value='GST 10%',
        destination_id='TAX001',
        detail={'tax_rate': 10},
        active=True
    )

    return attribute


@pytest.fixture
def create_tax_detail_with_solution_id(db):
    """
    Create TAX_DETAIL DestinationAttribute with tax_solution_id
    """
    workspace_id = 1

    attribute = DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='TAX_DETAIL',
        display_name='Tax Detail',
        value='TestTaxCode',
        destination_id='TAX_TEST',
        detail={'tax_solution_id': 'TAX_SOL_001'},
        active=True
    )

    return attribute


@pytest.fixture
def create_allocation_attribute(db):
    """
    Create ALLOCATION DestinationAttribute for allocation tests
    """
    workspace_id = 1

    attribute = DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='ALLOCATION',
        display_name='Allocation',
        value='ALLOC001',
        destination_id='ALLOC001',
        detail={'location': 'LOC001', 'department': 'DEPT001'},
        active=True
    )

    return attribute
