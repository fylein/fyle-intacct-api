import json
import pytest
from unittest import mock
from apps.fyle.models import Expense, ExpenseGroup, ExpenseGroupSettings, Reimbursement
from apps.workspaces.models import FyleCredential
from apps.fyle.tasks import schedule_expense_group_creation, create_expense_groups, sync_reimbursements
from apps.tasks.models import TaskLog
from tests.helper import dict_compare_keys
from .fixtures import data
from django.urls import reverse


def test_schedule_expense_group_creation(api_client, test_connection):
    workspace_id = 1

    expense_groups = ExpenseGroup.objects.filter(workspace_id=workspace_id).count()
    assert expense_groups == 3
    
    schedule_expense_group_creation(workspace_id=workspace_id)

    expense_groups = ExpenseGroup.objects.filter(workspace_id=workspace_id).count()
    assert expense_groups == 3


def test_create_expense_groups(mocker, db):
    workspace_id = 1
    
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
    expense_group_settings.ccc_export_date_type = 'last_spent_at'
    expense_group_settings.save()

    create_expense_groups(workspace_id, ['PERSONAL', 'CCC'], task_log)

    task_log = TaskLog.objects.get(id=task_log.id)

    assert task_log.status == 'COMPLETE'

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.delete()

    create_expense_groups(workspace_id, ['PERSONAL', 'CCC'], task_log)

    task_log = TaskLog.objects.get(id=task_log.id)
    assert task_log.status == 'FATAL'

    fyle_credential = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credential.delete()

    task_log, _ = TaskLog.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )
    create_expense_groups(workspace_id, ['PERSONAL', 'CCC'], task_log)

    task_log = TaskLog.objects.get(id=task_log.id)
    assert task_log.status == 'FAILED'


def test_sync_reimbursements(mocker, db):
    workspace_id = 1
    fyle_credential = FyleCredential.objects.get(workspace_id=workspace_id)
    
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Reimbursements.sync',
        return_value=None
    )

    sync_reimbursements(fyle_credential, workspace_id)

    reimbursements = Reimbursement.objects.filter().count()
    assert reimbursements == 258


@pytest.mark.django_db()
def test_create_expense_group_skipped_flow(mocker, api_client, test_connection):
    access_token = test_connection.access_token
    #adding the expense-filter
    url = reverse('expense-filters', 
        kwargs={
            'workspace_id': 1,
        }
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.post(url,data=data['expense_filter_0'])
    assert response.status_code == 201
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['expense_filter_0_response']) == [], 'expense group api return diffs in keys'

    task_log, _ = TaskLog.objects.update_or_create(
        workspace_id=1,
        type='FETCHING_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=1)
    expense_group_settings.import_card_credits = True
    expense_group_settings.save()


    with mock.patch('fyle_integrations_platform_connector.apis.Expenses.get') as mock_call:
        mock_call.side_effect = [
            data['expenses'],
            data['ccc_expenses']
        ]

        expense_group_count = len(ExpenseGroup.objects.filter(workspace_id=1))
        expenses_count = len(Expense.objects.filter(org_id='or79Cob97KSh'))

        create_expense_groups(1, ['PERSONAL', 'CCC'], task_log)
        expense_group = ExpenseGroup.objects.filter(workspace_id=1)
        expenses = Expense.objects.filter(org_id='or79Cob97KSh')

        assert len(expense_group) == expense_group_count+2
        assert len(expenses) == expenses_count+2

        for expense in expenses:
            if expense.employee_email == 'jhonsnow@fyle.in': 
                assert expense.is_skipped == True