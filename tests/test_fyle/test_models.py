from apps.fyle.models import get_default_expense_state, get_default_expense_group_fields, ExpenseGroupSettings, Expense, Reimbursement, \
    ExpenseGroup, _group_expenses, _format_date, get_default_ccc_expense_state
from apps.workspaces.models import Configuration
from .fixtures import data
from dateutil import parser
from apps.tasks.models import TaskLog
from apps.fyle.tasks import create_expense_groups
from apps.sage_intacct.models import get_transaction_date
from datetime import datetime


def test_default_fields():
    expense_group_field = get_default_expense_group_fields()
    expense_state = get_default_expense_state()
    ccc_expense_state = get_default_ccc_expense_state()

    assert expense_group_field == ['employee_email', 'report_id', 'claim_number', 'fund_source']
    assert expense_state == 'PAYMENT_PROCESSING'
    assert ccc_expense_state == 'PAID'


def test_create_expense_objects(db):
    workspace_id = 1
    payload = data['expenses']

    Expense.create_expense_objects(payload, workspace_id)
    expense = Expense.objects.last()

    assert expense.expense_id == 'tx4ziVSAyIsv'


def test_create_eliminated_expense_objects(db):
    workspace_id = 1
    payload = data['eliminated_expenses']

    Expense.create_expense_objects(payload, workspace_id)
    expense = Expense.objects.filter(expense_id='tx6wOnBVaumk')

    assert len(expense) == 1


def test_expense_group_settings(create_temp_workspace, db):
    workspace_id = 98
    payload = data['expense_group_settings_payload']

    ExpenseGroupSettings.update_expense_group_settings(
        payload, workspace_id
    )

    settings = ExpenseGroupSettings.objects.last()

    assert settings.expense_state == 'PAYMENT_PROCESSING'
    assert settings.ccc_export_date_type == 'spent_at'
    assert settings.ccc_expense_state == 'PAID'


def test_create_reimbursement(db):
    workspace_id = 1
    reimbursements = data['reimbursements']

    Reimbursement.create_or_update_reimbursement_objects(reimbursements=reimbursements, workspace_id=workspace_id)

    pending_reimbursement = Reimbursement.objects.get(reimbursement_id='reimgCW1Og0BcM')

    pending_reimbursement.state = 'PENDING'
    pending_reimbursement.settlement_id= 'setgCxsr2vTmZ'

    reimbursements[0]['is_paid'] = True

    Reimbursement.create_or_update_reimbursement_objects(reimbursements=reimbursements, workspace_id=workspace_id)

    paid_reimbursement = Reimbursement.objects.get(reimbursement_id='reimgCW1Og0BcM')
    paid_reimbursement.state == 'PAID'


def test_create_expense_groups_by_report_id_fund_source(db):
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

    expense_groups = _group_expenses(expense_objects, ['expense_id', 'fund_source', 'employee_email', 'spent_at', 'bank_transaction_id'], 4)
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
    expense_group_settings.reimbursable_expense_group_fields = ["employee_email", "expense_id", "fund_source", "spent_at" ]
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
    expense_group_settings.reimbursable_expense_group_fields = ["employee_email", "expense_id", "fund_source", "spent_at" ]
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
    expense_group_settings.reimbursable_expense_group_fields = ["employee_email", "expense_id", "fund_source", "spent_at" ]
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
    expense_group_settings.reimbursable_expense_group_fields = ["employee_email", "expense_id", "fund_source", "spent_at" ]
    expense_group_settings.save()

    
    expense_groups = _group_expenses(expense_objects, ['employee_email','expense_id','fund_source','spent_at'], 1)
    assert expense_groups[0]['total'] == 1
    
    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, workspace_id)
    expense_groups = ExpenseGroup.objects.filter(description__contains={'expense_id': 'tx4ziVSAyIsy'}).count()
    assert expense_groups == 1
    expense_groups = ExpenseGroup.objects.filter(description__contains={'expense_id': 'tx4ziVSAyIst'}).count()
    assert expense_groups == 1


def test_format_date():
    date_string = _format_date('2022-05-13T09:32:06.643941Z')

    assert date_string == parser.parse('2022-05-13T09:32:06.643941Z')


def test_get_last_synced_at(db):

    reimbursement = Reimbursement.get_last_synced_at(1)

    assert reimbursement.workspace_id == 1
    assert reimbursement.settlement_id == 'setzZCuAPxIsB'
    assert reimbursement.state == 'PENDING'

def test_support_post_date_integrations(mocker, db, api_client, test_connection):
    workspace_id = 1
    
    #Import assert
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses']
    )

    task_log, _ = TaskLog.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.reimbursable_export_date_type = 'last_spent_at'
    expense_group_settings.ccc_export_date_type = 'posted_at'
    expense_group_settings.save()

    create_expense_groups(workspace_id, ['PERSONAL', 'CCC'], task_log)

    task_log = TaskLog.objects.get(id=task_log.id)

    assert task_log.status == 'COMPLETE'
	
	#Export assert
    expense_group = ExpenseGroup.objects.get(id=1)

    posted_at = {'posted_at': '2021-12-24'}
    expense_group.description.update(posted_at)

    transaction_date = get_transaction_date(expense_group).split('T')[0]
    assert transaction_date <= datetime.now().strftime('%Y-%m-%d')

    access_token = test_connection.access_token
    url = '/api/workspaces/{}/sage_intacct/exports/trigger/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.post(
        url,
        data={
            'expense_group_ids': [1],
            'export_type': 'BILL'
        })
    assert response.status_code == 200
