import pytest
from datetime import datetime
from apps.fyle.models import (
    ExpenseGroup, DependentFieldSetting, Expense
)
from apps.workspaces.models import Configuration
from apps.sage_intacct.models import (
    Bill, BillLineitem, ExpenseReport, ExpenseReportLineitem,
    JournalEntry, JournalEntryLineitem, SageIntacctReimbursement,
    SageIntacctReimbursementLineitem, ChargeCardTransaction,
    ChargeCardTransactionLineitem, APPayment, APPaymentLineitem,
    CostType
)
from apps.mappings.models import GeneralMapping
from apps.tasks.models import TaskLog


@pytest.fixture
def create_bill(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    bill = Bill.create_bill(expense_group)
    bill_lineitems = BillLineitem.create_bill_lineitems(expense_group, workspace_general_settings)

    return bill, bill_lineitems


@pytest.fixture
def create_expense_report(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    expense_report = ExpenseReport.create_expense_report(expense_group)
    expense_report_lineitems  = ExpenseReportLineitem.create_expense_report_lineitems(expense_group, workspace_general_settings)

    return expense_report,expense_report_lineitems


@pytest.fixture
def create_journal_entry(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    journal_entry = JournalEntry.create_journal_entry(expense_group)
    journal_entry_lineitems = JournalEntryLineitem.create_journal_entry_lineitems(expense_group,workspace_general_settings)

    return journal_entry,journal_entry_lineitems


@pytest.fixture
def create_sage_intacct_reimbursement(db):

    expense_group = ExpenseGroup.objects.get(id=1)
    sage_intacct_reimbursement = SageIntacctReimbursement.create_sage_intacct_reimbursement(expense_group)
    intacct_reimbursement_lineitems  = SageIntacctReimbursementLineitem.create_sage_intacct_reimbursement_lineitems(expense_group, '3032')

    return sage_intacct_reimbursement,intacct_reimbursement_lineitems


@pytest.fixture
def create_charge_card_transaction(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    expense_group.description.update({'employee_email': 'user4444@fyleforgotham.in'})
    expense_group.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id) 
    general_mappings.default_charge_card_id = 'sample'
    general_mappings.save()

    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    charge_card_transaction = ChargeCardTransaction.create_charge_card_transaction(expense_group)
    charge_card_transaction_lineitems  = ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(expense_group, workspace_general_settings)

    return charge_card_transaction,charge_card_transaction_lineitems


@pytest.fixture
def create_ap_payment(db):

    expense_group = ExpenseGroup.objects.get(id=1)
    ap_payment = APPayment.create_ap_payment(expense_group)
    ap_payment_lineitems = APPaymentLineitem.create_ap_payment_lineitems(expense_group, '3032')

    return ap_payment, ap_payment_lineitems


@pytest.fixture
def create_task_logs(db):
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
    workspace_id = 1
    CostType.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'record_number': 34234,
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

@pytest.fixture
def create_dependent_field_setting(db):
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
