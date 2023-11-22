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
