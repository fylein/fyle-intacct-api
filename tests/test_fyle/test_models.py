from dateutil import parser

from apps.fyle.models import (
    Expense,
    ExpenseGroup,
    Reimbursement,
    _format_date,
    _group_expenses,
    ExpenseGroupSettings,
    get_default_expense_state,
    get_default_ccc_expense_state,
    get_default_expense_group_fields
)
from apps.workspaces.models import Configuration, Workspace
from .fixtures import data


def test_default_fields():
    """
    Test default fields
    """
    expense_group_field = get_default_expense_group_fields()
    expense_state = get_default_expense_state()
    ccc_expense_state = get_default_ccc_expense_state()

    assert expense_group_field == ['employee_email', 'report_id', 'claim_number', 'fund_source']
    assert expense_state == 'PAYMENT_PROCESSING'
    assert ccc_expense_state == 'PAID'


def test_create_expense_objects(db):
    """
    Test create expense objects
    """
    workspace_id = 1
    payload = data['expenses']

    Expense.create_expense_objects(payload, workspace_id)
    expense = Expense.objects.last()

    assert expense.expense_id == 'tx4ziVSAyIsv'


def test_create_eliminated_expense_objects(db):
    """
    Test create eliminated expense objects
    """
    workspace_id = 1
    payload = data['eliminated_expenses']

    Expense.create_expense_objects(payload, workspace_id)
    expense = Expense.objects.filter(expense_id='tx6wOnBVaumk')

    assert len(expense) == 1


def test_expense_group_settings(db):
    """
    Test expense group settings
    """
    workspace_id = 1
    payload = data['expense_group_settings_payload']

    user = Workspace.objects.get(id=workspace_id).user

    ExpenseGroupSettings.update_expense_group_settings(
        payload, workspace_id, user
    )

    settings = ExpenseGroupSettings.objects.last()

    assert settings.expense_state == 'PAYMENT_PROCESSING'
    assert settings.ccc_export_date_type == 'spent_at'
    assert settings.ccc_expense_state == 'PAID'


def test_create_reimbursement(db):
    """
    Test create reimbursement
    """
    workspace_id = 1
    reimbursements = data['reimbursements']

    Reimbursement.create_or_update_reimbursement_objects(reimbursements=reimbursements, workspace_id=workspace_id)

    pending_reimbursement = Reimbursement.objects.get(reimbursement_id='reimgCW1Og0BcM')

    pending_reimbursement.state = 'PENDING'
    pending_reimbursement.settlement_id = 'setgCxsr2vTmZ'

    reimbursements[0]['is_paid'] = True

    Reimbursement.create_or_update_reimbursement_objects(reimbursements=reimbursements, workspace_id=workspace_id)

    paid_reimbursement = Reimbursement.objects.get(reimbursement_id='reimgCW1Og0BcM')
    paid_reimbursement.state == 'PAID'


def test_create_expense_groups_by_report_id_fund_source(db):
    """
    Test create expense groups by report id and fund source
    """
    workspace_id = 1
    payload = data['expenses']

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    Expense.create_expense_objects(payload, workspace_id)
    expense_objects = Expense.objects.last()

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'last_spent_at'
    expense_group_settings.ccc_export_date_type = 'last_spent_at'
    expense_group_settings.save()

    expense_groups = _group_expenses([], ['claim_number', 'fund_source', 'projects', 'employee_email', 'report_id'], 4)
    assert expense_groups == []

    ExpenseGroup.create_expense_groups_by_report_id_fund_source([expense_objects], configuration, workspace_id)

    expense_groups = ExpenseGroup.objects.last()
    assert expense_groups.exported_at == None


def test_split_expenses_no_bank_transaction_id(db):
    """
    Test split expenses with no bank transaction id
    """
    # Grouping of expenses with no bank transaction id
    expenses = data['ccc_expenses_split_no_bank_transaction_id']
    configuration = Configuration.objects.get(workspace_id=1)
    configuration.corporate_credit_card_expenses_object = 'CREDIT CARD PURCHASE'
    configuration.save()

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=1)
    expense_group_settings.ccc_export_date_type = 'last_spent_at'
    expense_group_settings.split_expense_grouping = 'SINGLE_LINE_ITEM'
    expense_group_settings.save()

    expense_objects = Expense.create_expense_objects(expenses, 1)
    assert len(expense_objects) == 2

    expense_groups = _group_expenses(expense_objects, ['expense_id', 'fund_source', 'employee_email', 'spent_at'], 4)
    assert len(expense_groups) == 2

    expense_group_settings.split_expense_grouping = 'MULTIPLE_LINE_ITEM'
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['expense_id', 'fund_source', 'employee_email', 'spent_at'], 4)
    assert len(expense_groups) == 2


def test_split_expenses_same_bank_transaction_id(db):
    """
    Test split expenses with same bank transaction id
    """
    # Grouping of expenses with same bank transaction id
    expenses = data['ccc_expenses_split_same_bank_transaction_id']
    configuration = Configuration.objects.get(workspace_id=1)
    configuration.corporate_credit_card_expenses_object = 'CREDIT CARD PURCHASE'
    configuration.save()

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=1)
    expense_group_settings.ccc_export_date_type = 'last_spent_at'
    expense_group_settings.split_expense_grouping = 'SINGLE_LINE_ITEM'
    expense_group_settings.save()

    expense_objects = Expense.create_expense_objects(expenses, 1)
    assert len(expense_objects) == 2

    expense_groups = _group_expenses(expense_objects, ['expense_id', 'fund_source', 'employee_email', 'spent_at'], 4)
    assert len(expense_groups) == 2

    expense_group_settings.split_expense_grouping = 'MULTIPLE_LINE_ITEM'
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['expense_id', 'fund_source', 'employee_email', 'spent_at'], 4)
    assert len(expense_groups) == 2


def test_split_expenses_diff_bank_transaction_id(db):
    """
    Test split expenses with different bank transaction id
    """
    # Grouping of expenses with different bank transaction id
    expenses = data['ccc_expenses_split_diff_bank_transaction_id']
    configuration = Configuration.objects.get(workspace_id=1)
    configuration.corporate_credit_card_expenses_object = 'CREDIT CARD PURCHASE'
    configuration.save()

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=1)
    expense_group_settings.ccc_export_date_type = 'last_spent_at'
    expense_group_settings.split_expense_grouping = 'SINGLE_LINE_ITEM'
    expense_group_settings.save()

    expense_objects = Expense.create_expense_objects(expenses, 1)
    assert len(expense_objects) == 4

    expense_groups = _group_expenses(expense_objects, ['expense_id', 'fund_source', 'employee_email', 'spent_at', 'bank_transaction_id'], 4)
    assert len(expense_groups) == 4

    expense_group_settings.split_expense_grouping = 'MULTIPLE_LINE_ITEM'
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['fund_source', 'employee_email', 'spent_at', 'bank_transaction_id'], 4)
    assert len(expense_groups) == 2


def test_create_expense_groups_by_report_id_fund_source_test_1(db):
    """
    Group By Report
    spent_at
    1 negative expense with total amount in -ve
    """
    workspace_id = 1
    payload = data['negative_expenses']

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.save()
    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['employee_email','claim_number','fund_source','spent_at'], 1)
    assert expense_groups[0]['total'] == 1
    assert expense_groups[1]['total'] == 1

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)
    expense_groups = ExpenseGroup.objects.filter(description__contains={'claim_number': 'C/2021/12/R/23'}).count()
    assert expense_groups == 1


def test_create_expense_groups_by_report_id_fund_source_test_2(db):
    """
    Group by report
    spent_at
    2 positive expenses
    """
    workspace_id = 1
    payload = data['positive_expenses']

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.save()
    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['employee_email','claim_number','fund_source','spent_at'], 1)
    assert expense_groups[0]['total'] == 2

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)
    expense_groups = ExpenseGroup.objects.filter(description__contains={'claim_number': 'C/2021/12/R/23'}).count()
    assert expense_groups == 1


def test_create_expense_groups_by_report_id_fund_source_test_3(db):
    """
    GROUP BY REPORT
    spent_at
    1 negative 1 positive with total positive
    """
    workspace_id = 1
    payload = data['positive_expenses']
    payload[0]['amount'] = -50

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.save()
    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['employee_email','claim_number','fund_source','spent_at'], 1)
    assert expense_groups[0]['total'] == 2

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)
    expense_groups = ExpenseGroup.objects.filter(description__contains={'claim_number': 'C/2021/12/R/23'}).count()
    assert expense_groups == 1


def test_create_expense_groups_by_report_id_fund_source_test_4(db):
    """
    Group By Report
    spent_at
    1 negative expense with total amount in -ve
    """
    workspace_id = 1
    payload = data['positive_expenses']
    payload[0]['amount'] = -200

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.save()
    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['employee_email','claim_number','fund_source','spent_at'], 1)
    assert expense_groups[0]['total'] == 2

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)
    expense_groups = ExpenseGroup.objects.filter(description__contains={'claim_number': 'C/2021/12/R/23'})
    assert len(expense_groups) == 1
    assert len(expense_groups[0].expenses.values_list('id', flat=True)) == 1


def test_create_expense_groups_by_report_id_fund_source_test_5(db):
    """
    Group by expense
    2 positive expenses
    """
    workspace_id = 1
    payload = data['positive_expenses']
    payload[0]['amount'] = 50

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.save()
    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    expense_group_settings.reimbursable_expense_group_fields = ["employee_email", "expense_id", "fund_source", "spent_at"]
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['employee_email','expense_id','fund_source','spent_at'], 1)
    assert expense_groups[0]['total'] == 1

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)
    expense_groups = ExpenseGroup.objects.filter(description__contains={'expense_id': 'tx4ziVSAyIsy'}).count()
    assert expense_groups == 1
    expense_groups = ExpenseGroup.objects.filter(description__contains={'expense_id': 'tx4ziVSAyIst'}).count()
    assert expense_groups == 1


def test_create_expense_groups_by_report_id_fund_source_test_6(db):
    """
    Group by expense
    1 negative expenses
    """
    workspace_id = 1
    payload = data['positive_expenses']
    payload[0]['amount'] = -50

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.save()
    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    expense_group_settings.reimbursable_expense_group_fields = ["employee_email", "expense_id", "fund_source", "spent_at"]
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['employee_email','expense_id','fund_source','spent_at'], 1)
    assert expense_groups[0]['total'] == 1

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)
    expense_groups = ExpenseGroup.objects.filter(description__contains={'expense_id': 'tx4ziVSAyIsy'}).count()
    assert expense_groups == 1
    expense_groups = ExpenseGroup.objects.filter(description__contains={'expense_id': 'tx4ziVSAyIst'}).count()
    assert expense_groups == 0


def test_create_expense_groups_by_report_id_fund_source_test_7(db):
    """
    Group by expense
    1 negative expenses
    """
    workspace_id = 1
    payload = data['positive_expenses']
    payload[0]['amount'] = -50

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'BILL'
    configuration.save()
    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    expense_group_settings.reimbursable_expense_group_fields = ["employee_email", "expense_id", "fund_source", "spent_at"]
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['employee_email','expense_id','fund_source','spent_at'], 1)
    assert expense_groups[0]['total'] == 1

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)
    expense_groups = ExpenseGroup.objects.filter(description__contains={'expense_id': 'tx4ziVSAyIsy'}).count()
    assert expense_groups == 1
    expense_groups = ExpenseGroup.objects.filter(description__contains={'expense_id': 'tx4ziVSAyIst'}).count()
    assert expense_groups == 1


def test_create_expense_groups_by_report_id_fund_source_test_8(db):
    """
    Group by expense
    1 negative expenses
    """
    workspace_id = 1
    payload = data['positive_expenses']
    payload[0]['amount'] = -50

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()
    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    expense_group_settings.reimbursable_expense_group_fields = ["employee_email", "expense_id", "fund_source", "spent_at"]
    expense_group_settings.save()

    expense_groups = _group_expenses(expense_objects, ['employee_email','expense_id','fund_source','spent_at'], 1)
    assert expense_groups[0]['total'] == 1

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)
    expense_groups = ExpenseGroup.objects.filter(description__contains={'expense_id': 'tx4ziVSAyIsy'}).count()
    assert expense_groups == 1
    expense_groups = ExpenseGroup.objects.filter(description__contains={'expense_id': 'tx4ziVSAyIst'}).count()
    assert expense_groups == 1


def test_create_expense_groups_ccc_negative_expense_report(db):
    """
    Test CCC negative expenses are NOT filtered when exported as EXPENSE_REPORT.
    Sage Intacct supports negative line items for non-reimbursable expense reports.
    Group by expense - both positive and negative CCC expenses should be exported.
    """
    workspace_id = 1
    payload = data['ccc_expenses_for_negative_test']

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.ccc_export_date_type = 'spent_at'
    expense_group_settings.corporate_credit_card_expense_group_fields = ["employee_email", "expense_id", "fund_source", "spent_at"]
    expense_group_settings.save()

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)

    # Both expenses should be exported - negative CCC expenses should NOT be skipped
    negative_expense_group = ExpenseGroup.objects.filter(description__contains={'expense_id': 'txCCCNeg001'}).count()
    positive_expense_group = ExpenseGroup.objects.filter(description__contains={'expense_id': 'txCCCPos001'}).count()

    assert negative_expense_group == 1, "Negative CCC expense should be exported as EXPENSE_REPORT"
    assert positive_expense_group == 1, "Positive CCC expense should be exported as EXPENSE_REPORT"


def test_create_expense_groups_ccc_negative_expense_report_grouped_by_report(db):
    """
    Test CCC negative expenses grouped by report are NOT filtered when exported as EXPENSE_REPORT.
    Even when total is negative, CCC expenses should be exported with both positive and negative line items.
    """
    workspace_id = 1
    payload = data['ccc_expenses_for_grouped_negative_test']

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.ccc_export_date_type = 'spent_at'
    # Group by report (claim_number) instead of expense_id
    expense_group_settings.corporate_credit_card_expense_group_fields = ["employee_email", "claim_number", "fund_source", "spent_at"]
    expense_group_settings.save()

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)

    # Expense group with negative total should be created for CCC expenses
    expense_group = ExpenseGroup.objects.filter(
        fund_source='CCC',
        description__contains={'claim_number': 'C/2021/12/R/GRP'}
    ).first()
    assert expense_group is not None, "CCC expense group should be created even with negative total"

    # Both expenses should be in the same group
    expenses_in_group = list(expense_group.expenses.all())
    assert len(expenses_in_group) == 2, "Both expenses should be in the same expense group"

    # Verify the negative expense is included
    negative_expense = expense_group.expenses.filter(amount__lt=0).first()
    assert negative_expense is not None, "Negative CCC expense should be included in the expense group"
    assert negative_expense.amount == -200, "Negative expense amount should be -200"


def test_create_expense_groups_reimbursable_negative_expense_report_grouped_by_report(db):
    """
    Test reimbursable expenses grouped by report - negative expenses should be filtered when total is positive.
    2 reimbursable expenses grouped by report with 1 negative expense (-100 + 200 = 100 positive total).
    """
    workspace_id = 1
    payload = data['reimbursable_expenses_for_grouped_negative_test']

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    # Group by report (claim_number)
    expense_group_settings.reimbursable_expense_group_fields = ["employee_email", "claim_number", "fund_source", "spent_at"]
    expense_group_settings.save()

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)

    # Expense group should be created since total is positive (200 - 100 = 100)
    expense_group = ExpenseGroup.objects.filter(
        fund_source='PERSONAL',
        description__contains={'claim_number': 'C/2021/12/R/REIM'}
    ).first()
    assert expense_group is not None, "Reimbursable expense group should be created with positive total"

    # Both expenses should be in the same group since total is positive
    expenses_in_group = list(expense_group.expenses.all())
    assert len(expenses_in_group) == 2, "Both expenses should be in the same expense group when total is positive"


def test_create_expense_groups_reimbursable_both_negative_expense_report_grouped_by_expense(db):
    """
    Test reimbursable expenses with both negative amounts grouped by expense.
    Both negative reimbursable expenses should be skipped when exported as EXPENSE_REPORT.
    """
    workspace_id = 1
    payload = data['reimbursable_expenses_both_negative_test']

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    expense_objects = Expense.create_expense_objects(payload, workspace_id)

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    # Group by expense (expense_id)
    expense_group_settings.reimbursable_expense_group_fields = ["employee_email", "expense_id", "fund_source", "spent_at"]
    expense_group_settings.save()

    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)

    # Both negative reimbursable expenses should be skipped
    negative_expense_group_1 = ExpenseGroup.objects.filter(description__contains={'expense_id': 'txReimNeg001'}).count()
    negative_expense_group_2 = ExpenseGroup.objects.filter(description__contains={'expense_id': 'txReimNeg002'}).count()

    assert negative_expense_group_1 == 0, "Negative reimbursable expense should be skipped"
    assert negative_expense_group_2 == 0, "Negative reimbursable expense should be skipped"


def test_format_date():
    """
    Test format date
    """
    date_string = _format_date('2022-05-13T09:32:06.643941Z')

    assert date_string == parser.parse('2022-05-13T09:32:06.643941Z')


def test_get_last_synced_at(db):
    """
    Test get last synced at
    """
    reimbursement = Reimbursement.get_last_synced_at(1)

    assert reimbursement.workspace_id == 1
    assert reimbursement.settlement_id == 'setzZCuAPxIsB'
    assert reimbursement.state == 'PENDING'
