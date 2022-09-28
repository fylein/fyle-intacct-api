import pytest
from apps.fyle.models import Expense, ExpenseGroup
from apps.workspaces.models import Configuration
from apps.sage_intacct.models import Bill, BillLineitem, ExpenseReport, ExpenseReportLineitem, JournalEntry, JournalEntryLineitem, \
    SageIntacctReimbursement, SageIntacctReimbursementLineitem, ChargeCardTransaction, ChargeCardTransactionLineitem, APPayment, APPaymentLineitem
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
