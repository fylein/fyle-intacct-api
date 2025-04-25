import pytest

import json
from unittest import mock

from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError

from fyle.platform.exceptions import InvalidTokenError, InternalServerError

from tests.helper import dict_compare_keys

from apps.tasks.models import Error, TaskLog
from apps.workspaces.models import Configuration, FyleCredential, LastExportDetail, Workspace
from apps.fyle.models import Expense, ExpenseFilter, ExpenseGroup, ExpenseGroupSettings
from apps.fyle.tasks import (
    create_expense_groups,
    re_run_skip_export_rule,
    schedule_expense_group_creation,
    update_non_exported_expenses,
    import_and_export_expenses
)
from .fixtures import data


def test_schedule_expense_group_creation(api_client, test_connection):
    """
    Test schedule expense group creation
    """
    workspace_id = 1
    expense_groups = ExpenseGroup.objects.filter(workspace_id=workspace_id).count()
    assert expense_groups == 3

    schedule_expense_group_creation(workspace_id=workspace_id)

    expense_groups = ExpenseGroup.objects.filter(workspace_id=workspace_id).count()
    assert expense_groups == 3


def test_create_expense_groups(mocker, db):
    """
    Test create expense groups
    """
    workspace_id = 1

    mock_call = mocker.patch(
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

    create_expense_groups(workspace_id, ['PERSONAL', 'CCC'], task_log, ExpenseImportSourceEnum.DASHBOARD_SYNC)

    task_log = TaskLog.objects.get(id=task_log.id)

    assert task_log.status == 'COMPLETE'

    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    expense_group_settings.delete()

    create_expense_groups(workspace_id, ['PERSONAL', 'CCC'], task_log, ExpenseImportSourceEnum.DASHBOARD_SYNC)

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
    create_expense_groups(workspace_id, ['PERSONAL', 'CCC'], task_log, ExpenseImportSourceEnum.DASHBOARD_SYNC)

    task_log = TaskLog.objects.get(id=task_log.id)
    assert task_log.status == 'FAILED'

    mock_call.side_effect = InternalServerError('Error')
    create_expense_groups(workspace_id, ['PERSONAL', 'CCC'], task_log, ExpenseImportSourceEnum.DASHBOARD_SYNC)

    mock_call.side_effect = InvalidTokenError('Invalid Token')
    create_expense_groups(workspace_id, ['PERSONAL', 'CCC'], task_log, ExpenseImportSourceEnum.DASHBOARD_SYNC)

    assert mock_call.call_count == 2


@pytest.mark.django_db()
def test_create_expense_group_skipped_flow(mocker, api_client, test_connection):
    """
    Test create expense groups
    """
    access_token = test_connection.access_token
    # adding the expense-filter
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

    with mock.patch('fyle_integrations_platform_connector.apis.Expenses.get') as mock_call:
        mock_call.side_effect = [
            data['expenses'],
            data['ccc_expenses']
        ]

        expense_group_count = len(ExpenseGroup.objects.filter(workspace_id=1))
        expenses_count = len(Expense.objects.filter(org_id='or79Cob97KSh'))

        create_expense_groups(1, ['PERSONAL', 'CCC'], task_log, ExpenseImportSourceEnum.DASHBOARD_SYNC)
        expense_group = ExpenseGroup.objects.filter(workspace_id=1)
        expenses = Expense.objects.filter(org_id='or79Cob97KSh')

        assert len(expense_group) == expense_group_count
        assert len(expenses) == expenses_count

        for expense in expenses:
            if expense.employee_email == 'jhonsnow@fyle.in':
                assert expense.is_skipped == True


def test_update_non_exported_expenses(db, create_temp_workspace, mocker, api_client):
    """
    Test update non exported expenses
    """
    expense = data['raw_expense']
    expense['bank_transaction_id'] = 'btxnanish'
    default_raw_expense = data['default_raw_expense']
    org_id = expense['org_id']
    payload = {
        "resource": "EXPENSE",
        "action": 'UPDATED_AFTER_APPROVAL',
        "data": expense,
        "reason": 'expense update testing',
    }

    expense_created, _ = Expense.objects.update_or_create(
        org_id=org_id,
        expense_id='txhJLOSKs1iN',
        workspace_id=1,
        defaults=default_raw_expense
    )
    expense_created.accounting_export_summary = {}
    expense_created.save()

    workspace = Workspace.objects.filter(id=1).first()
    workspace.fyle_org_id = org_id
    workspace.save()

    assert expense_created.category == 'Old Category'

    update_non_exported_expenses(payload['data'])

    expense = Expense.objects.get(expense_id='txhJLOSKs1iN', org_id=org_id)
    assert expense.category == 'ABN Withholding'

    expense.accounting_export_summary = {"synced": True, "state": "COMPLETE"}
    expense.category = 'Old Category'
    expense.save()

    update_non_exported_expenses(payload['data'])
    expense = Expense.objects.get(expense_id='txhJLOSKs1iN', org_id=org_id)
    assert expense.category == 'Old Category'

    try:
        update_non_exported_expenses(payload['data'])
    except ValidationError as e:
        assert e.detail[0] == 'Workspace mismatch'

    url = reverse('exports', kwargs={'workspace_id': 1})
    response = api_client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_200_OK

    url = reverse('exports', kwargs={'workspace_id': 2})
    response = api_client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_re_run_skip_export_rule(db, create_temp_workspace, mocker, api_client, test_connection):
    """Test the re-running of skip export rules for expenses

    This test verifies that expenses are correctly skipped based on email filters,
    expense groups are properly cleaned up, and export details are updated.
    """
    # Create an expense filter that will match expenses with employee_email 'jhonsnow@fyle.in'
    ExpenseFilter.objects.create(
        workspace_id=1,
        condition='expense_number',
        operator='in',
        values=['expense_1'],
        rank=1,
        join_by=None,
    )

    # Retrieve test expenses data and modify them to ensure unique grouping
    expenses = list(data["expenses_spent_at"])
    expenses[0].update({
        'expense_number': 'expense_1',
        'employee_email': 'jhonsnow@fyle.in',
        'report_id': 'report_1',
        'claim_number': 'claim_1',
        'fund_source': 'PERSONAL'
    })
    expenses[1].update({
        'expense_number': 'expense_2',
        'employee_email': 'other.email@fyle.in',
        'report_id': 'report_2',
        'claim_number': 'claim_2',
        'fund_source': 'PERSONAL'
    })
    expenses[2].update({
        'expense_number': 'expense_3',
        'employee_email': 'anish@fyle.in',
        'report_id': 'report_3',
        'claim_number': 'claim_3',
        'fund_source': 'PERSONAL',
        'amount': 1000
    })
    # Assign org_id to all expenses
    for expense in expenses:
        expense['org_id'] = 'orHVw3ikkCxJ'

    # Create expense objects in the database
    expense_objects = Expense.create_expense_objects(expenses, 1)

    # Mark all expenses as failed exports by updating their accounting_export_summary
    for expense in Expense.objects.filter(workspace_id=1):
        expense.accounting_export_summary = {
            'state': 'FAILED',
            'synced': False
        }
        expense.save()

    configuration = Configuration.objects.get(workspace_id=1)

    # Create expense groups - this should create 3 separate groups, one for each expense
    ExpenseGroup.create_expense_groups_by_report_id_fund_source(expense_objects, configuration, 1)
    expense_groups = ExpenseGroup.objects.filter(workspace_id=1)
    expense_group_ids = expense_groups.values_list('id', flat=True)
    expense_group_skipped = ExpenseGroup.objects.filter(workspace_id=1, expenses__expense_id=expenses[0]['id']).first()

    # Create TaskLog to simulate in-progress export
    # get the first expense group id, and create a task log for it
    tasklog = TaskLog.objects.create(
        workspace_id=1,
        type='CREATING_BILL',
        status='FAILED',
        expense_group_id=expense_group_skipped.id
    )

    # Create error for the first expense group
    error = Error.objects.create(
        workspace_id=1,
        type='QBO_ERROR',
        error_title='Test error title',
        error_detail='Test error detail',
        expense_group=ExpenseGroup.objects.get(id=expense_group_skipped.id)
    )

    LastExportDetail.objects.update_or_create(
        workspace_id=1,
        defaults={
            'total_expense_groups_count': len(expense_groups),
            'failed_expense_groups_count': 1,
            'export_mode': 'MANUAL'
        }
    )

    workspace = Workspace.objects.get(id=1)

    assert tasklog.status == 'FAILED'
    assert error.type == 'QBO_ERROR'

    re_run_skip_export_rule(workspace)

    # Test 1: Verify expense skipping based on email filter
    skipped_expense = Expense.objects.get(expense_number='expense_1')
    non_skipped_expense = Expense.objects.get(expense_number='expense_2')
    assert skipped_expense.is_skipped == True
    assert non_skipped_expense.is_skipped == False

    # Test 2: Verify expense group modifications
    remaining_groups = ExpenseGroup.objects.filter(id__in=expense_group_ids)
    assert remaining_groups.count() == 2

    # Test 3: Verify cleanup of task logs
    task_log = TaskLog.objects.filter(workspace_id=1).first()
    assert task_log is None

    # Test 4: Verify cleanup of errors
    error = Error.objects.filter(workspace_id=1, expense_group_id__in=expense_group_ids).first()
    assert error is None

    # Test 5: Verify LastExportDetail updates
    last_export_detail = LastExportDetail.objects.filter(workspace_id=1).first()
    assert last_export_detail.failed_expense_groups_count == 0


def test_import_and_export_expenses(mocker, db, test_connection):
    """
    Test import and export expenses
    """
    mock_call = mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses_webhook']
    )

    import_and_export_expenses(
        report_id='rp1s1L3QtMpF',
        org_id='or79Cob97KSh',
        is_state_change_event=True,
        imported_from=ExpenseImportSourceEnum.DASHBOARD_SYNC
    )

    assert mock_call.call_count == 1
