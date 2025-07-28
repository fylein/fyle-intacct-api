import json
from unittest import mock

from django.urls import reverse
from django_q.models import Schedule
from fyle.platform.exceptions import InternalServerError, InvalidTokenError
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.fyle.models import Expense, ExpenseGroup, ExpenseGroupSettings
from apps.fyle.tasks import (
    cleanup_scheduled_task,
    create_expense_groups,
    delete_and_recreate_expense_group,
    handle_fund_source_changes_for_expense_ids,
    import_and_export_expenses,
    process_expense_group,
    recreate_expense_groups,
    retry_fund_source_change_handling,
    schedule_expense_group_creation,
    schedule_task_for_expense_group_fund_source_change,
    skip_expenses_and_post_accounting_export_summary,
    update_non_exported_expenses,
)
from apps.tasks.models import Error, TaskLog
from apps.workspaces.models import Configuration, FyleCredential, Workspace
from tests.helper import dict_compare_keys
from tests.test_fyle.fixtures import data


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


def test_import_and_export_expenses_direct_export_case_1(mocker, db, test_connection):
    """
    Test import and export expenses
    Case 1: Reimbursable expenses are not configured
    """
    workspace_id = 1
    workspace = Workspace.objects.get(id=workspace_id)
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = None
    configuration.save()

    mock_call = mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses_webhook']
    )

    mock_skip_expenses_and_post_accounting_export_summary = mocker.patch(
        'apps.fyle.tasks.skip_expenses_and_post_accounting_export_summary',
        return_value=None
    )

    import_and_export_expenses(
        report_id='rp1s1L3QtMpF',
        org_id=workspace.fyle_org_id,
        is_state_change_event=False,
        imported_from=ExpenseImportSourceEnum.DIRECT_EXPORT
    )

    assert mock_call.call_count == 1
    assert mock_skip_expenses_and_post_accounting_export_summary.call_count == 1


def test_import_and_export_expenses_direct_export_case_2(mocker, db, test_connection):
    """
    Test import and export expenses
    Case 2: Corporate credit card expenses are not configured
    """
    workspace_id = 1
    workspace = Workspace.objects.get(id=workspace_id)
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.corporate_credit_card_expenses_object = None
    configuration.save()

    expense_data = data['expenses_webhook'].copy()
    expense_data[0]['org_id'] = workspace.fyle_org_id
    expense_data[0]['source_account_type'] = 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'

    mock_call = mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=expense_data
    )

    mock_skip_expenses_and_post_accounting_export_summary = mocker.patch(
        'apps.fyle.tasks.skip_expenses_and_post_accounting_export_summary',
        return_value=None
    )

    import_and_export_expenses(
        report_id='rp1s1L3QtMpF',
        org_id=workspace.fyle_org_id,
        is_state_change_event=False,
        imported_from=ExpenseImportSourceEnum.DIRECT_EXPORT
    )

    assert mock_call.call_count == 1
    assert mock_skip_expenses_and_post_accounting_export_summary.call_count == 1


def test_skip_expenses_and_post_accounting_export_summary(mocker, db):
    """
    Test skip expenses and post accounting export summary
    """
    workspace = Workspace.objects.get(id=1)

    expense = Expense.objects.filter(org_id='or79Cob97KSh').first()
    expense.workspace = workspace
    expense.org_id = workspace.fyle_org_id
    expense.accounting_export_summary = {}
    expense.is_skipped = False
    expense.fund_source = 'PERSONAL'
    expense.save()

    # Patch mark_expenses_as_skipped to return the expense in a list
    mock_mark_skipped = mocker.patch(
        'apps.fyle.tasks.mark_expenses_as_skipped',
        return_value=[expense]
    )
    # Patch post_accounting_export_summary to just record the call
    mock_post_summary = mocker.patch(
        'apps.fyle.tasks.post_accounting_export_summary',
        return_value=None
    )

    # Call the function under test
    skip_expenses_and_post_accounting_export_summary([expense.id], workspace)

    # Assert mark_expenses_as_skipped was called with Q(), [expense.id], workspace
    assert mock_mark_skipped.call_count == 1
    args, _ = mock_mark_skipped.call_args
    assert args[1] == [expense.id]
    assert args[2] == workspace

    # Assert post_accounting_export_summary was called with workspace_id and expense_ids
    assert mock_post_summary.call_count == 1
    _, post_kwargs = mock_post_summary.call_args
    assert post_kwargs['workspace_id'] == workspace.id
    assert post_kwargs['expense_ids'] == [expense.id]


def test_handle_fund_source_changes_for_expense_ids(mocker, db):
    """
    Test handle fund source changes for expense ids
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    mock_process_expense_group = mocker.patch(
        'apps.fyle.tasks.process_expense_group',
        return_value=None
    )

    handle_fund_source_changes_for_expense_ids(workspace_id=workspace_id, changed_expense_ids=changed_expense_ids)

    assert mock_process_expense_group.call_count == 1


def test_process_expense_group_enqueued_status(mocker, db):
    """
    Test process expense group when task log is ENQUEUED
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    TaskLog.objects.filter(expense_group_id=expense_group.id).delete()

    task_log = TaskLog.objects.create(
        workspace_id=workspace_id,
        type='CREATING_JOURNAL_ENTRY',
        expense_group_id=expense_group.id,
        status='ENQUEUED'
    )

    mock_schedule = mocker.patch(
        'apps.fyle.tasks.schedule_task_for_expense_group_fund_source_change',
        return_value=None
    )

    process_expense_group(expense_group=expense_group, changed_expense_ids=changed_expense_ids, workspace_id=workspace_id)
    task_log.delete()

    assert mock_schedule.call_count == 1


def test_process_expense_group_in_progress_status(mocker, db):
    """
    Test process expense group when task log is IN_PROGRESS
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    TaskLog.objects.filter(expense_group_id=expense_group.id).delete()

    task_log = TaskLog.objects.create(
        workspace_id=workspace_id,
        type='CREATING_JOURNAL_ENTRY',
        expense_group_id=expense_group.id,
        status='IN_PROGRESS'
    )

    mock_schedule = mocker.patch(
        'apps.fyle.tasks.schedule_task_for_expense_group_fund_source_change',
        return_value=None
    )

    process_expense_group(expense_group=expense_group, changed_expense_ids=changed_expense_ids, workspace_id=workspace_id)
    task_log.delete()

    assert mock_schedule.call_count == 1


def test_process_expense_group_complete_status(mocker, db):
    """
    Test process expense group when task log is COMPLETE
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    TaskLog.objects.filter(expense_group_id=expense_group.id).delete()

    task_log = TaskLog.objects.create(
        workspace_id=workspace_id,
        type='CREATING_JOURNAL_ENTRY',
        expense_group_id=expense_group.id,
        status='COMPLETE'
    )

    mock_delete_recreate = mocker.patch(
        'apps.fyle.tasks.delete_and_recreate_expense_group',
        return_value=None
    )

    process_expense_group(expense_group=expense_group, changed_expense_ids=changed_expense_ids, workspace_id=workspace_id)
    task_log.delete()

    assert mock_delete_recreate.call_count == 0


def test_process_expense_group_no_task_log(mocker, db):
    """
    Test process expense group when no task log exists
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    TaskLog.objects.filter(expense_group_id=expense_group.id).delete()

    mock_delete_recreate = mocker.patch(
        'apps.fyle.tasks.delete_and_recreate_expense_group',
        return_value=None
    )

    process_expense_group(expense_group=expense_group, changed_expense_ids=changed_expense_ids, workspace_id=workspace_id)

    assert mock_delete_recreate.call_count == 1


def test_delete_and_recreate_expense_group(mocker, db):
    """
    Test delete and recreate expense group
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()

    TaskLog.objects.filter(expense_group_id=expense_group.id).delete()

    task_log = TaskLog.objects.create(
        workspace_id=workspace_id,
        type='CREATING_JOURNAL_ENTRY',
        expense_group_id=expense_group.id,
        status='FAILED'
    )

    error = Error.objects.create(
        workspace_id=workspace_id,
        expense_group_id=expense_group.id,
        type='INTACCT_ERROR'
    )

    # Create error with mapping_error_expense_group_ids
    error_with_mapping = Error.objects.create(
        workspace_id=workspace_id,
        type='MAPPING',
        mapping_error_expense_group_ids=[expense_group.id, 999]
    )

    mocker.patch(
        'apps.fyle.tasks.recreate_expense_groups',
        return_value=None
    )

    delete_and_recreate_expense_group(expense_group=expense_group, workspace_id=workspace_id)

    assert not ExpenseGroup.objects.filter(id=expense_group.id).exists()
    assert not TaskLog.objects.filter(id=task_log.id).exists()
    assert not Error.objects.filter(id=error.id).exists()
    error_with_mapping.refresh_from_db()
    assert expense_group.id not in error_with_mapping.mapping_error_expense_group_ids
    assert 999 in error_with_mapping.mapping_error_expense_group_ids
    error_with_mapping.delete()


def test_delete_and_recreate_expense_group_empty_mapping_error(mocker, db):
    """
    Test delete and recreate expense group with empty mapping error
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()

    error_with_mapping = Error.objects.create(
        workspace_id=workspace_id,
        type='MAPPING',
        mapping_error_expense_group_ids=[expense_group.id]
    )

    mocker.patch(
        'apps.fyle.tasks.recreate_expense_groups',
        return_value=None
    )

    delete_and_recreate_expense_group(expense_group=expense_group, workspace_id=workspace_id)

    assert not Error.objects.filter(id=error_with_mapping.id).exists()


def test_recreate_expense_groups(mocker, db):
    """
    Test recreate expense groups
    """
    workspace_id = 1

    Expense.objects.all().update(workspace_id=workspace_id)

    existing_expenses = list(Expense.objects.filter(workspace_id=workspace_id))

    expense_ids = [existing_expenses[0].id]

    mock_create_groups = mocker.patch(
        'apps.fyle.models.ExpenseGroup.create_expense_groups_by_report_id_fund_source',
        return_value=[expense_ids[0]]
    )

    # Mock mark_expenses_as_skipped to return some expenses
    mock_expense = mocker.MagicMock()
    mock_expense.id = expense_ids[0]
    mocker.patch(
        'apps.fyle.tasks.mark_expenses_as_skipped',
        return_value=[mock_expense]
    )

    mock_post_summary = mocker.patch(
        'apps.fyle.tasks.post_accounting_export_summary',
        return_value=None
    )

    recreate_expense_groups(workspace_id=workspace_id, expense_ids=expense_ids)

    assert mock_create_groups.call_count == 1
    assert mock_post_summary.call_count == 1


def test_recreate_expense_groups_with_configuration_filters(mocker, db):
    """
    Test recreate expense groups with configuration and filters
    """
    workspace_id = 1
    configuration = Configuration.objects.get(workspace_id=workspace_id)

    Expense.objects.all().update(workspace_id=workspace_id)

    existing_expenses = list(Expense.objects.filter(workspace_id=workspace_id))

    expense_ids = [existing_expenses[0].id] if len(existing_expenses) == 1 else [existing_expenses[0].id, existing_expenses[1].id]

    mock_create_groups = mocker.patch(
        'apps.fyle.models.ExpenseGroup.create_expense_groups_by_report_id_fund_source',
        return_value=[]
    )

    mocker.patch(
        'apps.fyle.tasks.skip_expenses_and_post_accounting_export_summary',
        return_value=None
    )

    configuration.reimbursable_expenses_object = None
    configuration.save()

    recreate_expense_groups(workspace_id=workspace_id, expense_ids=expense_ids)

    configuration.reimbursable_expenses_object = 'BILL'
    configuration.corporate_credit_card_expenses_object = None
    configuration.save()

    recreate_expense_groups(workspace_id=workspace_id, expense_ids=expense_ids)

    assert mock_create_groups.call_count >= 1


def test_schedule_task_for_expense_group_fund_source_change(mocker, db):
    """
    Test schedule task for expense group fund source change
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    schedule_task_for_expense_group_fund_source_change(
        expense_group_id=expense_group.id,
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id
    )

    assert Schedule.objects.filter(
        func='apps.fyle.tasks.retry_fund_source_change_handling',
        name=f'fund_source_change_retry_{expense_group.id}_{workspace_id}'
    ).exists() is True


def test_schedule_task_existing_schedule(mocker, db):
    """
    Test schedule task when schedule already exists
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    task_name = f'fund_source_change_retry_{expense_group.id}_{workspace_id}'
    existing_schedule = Schedule.objects.create(
        func='apps.fyle.tasks.retry_fund_source_change_handling',
        name=task_name,
        args='[]'
    )

    mock_schedule = mocker.patch(
        'apps.fyle.tasks.schedule',
        return_value=None
    )

    schedule_task_for_expense_group_fund_source_change(
        expense_group_id=expense_group.id,
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id
    )

    assert mock_schedule.call_count == 0
    existing_schedule.delete()


def test_retry_fund_source_change_handling_nonexistent_group(mocker, db):
    """
    Test retry fund source change handling when expense group doesn't exist
    """
    workspace_id = 1
    nonexistent_group_id = 99999
    changed_expense_ids = [1, 2]

    mock_process = mocker.patch(
        'apps.fyle.tasks.process_expense_group',
        return_value=None
    )

    mock_cleanup = mocker.patch(
        'apps.fyle.tasks.cleanup_scheduled_task',
        return_value=None
    )

    retry_fund_source_change_handling(
        expense_group_id=nonexistent_group_id,
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id
    )

    assert mock_process.call_count == 0
    assert mock_cleanup.call_count == 0


def test_retry_fund_source_change_handling_enqueued_status(mocker, db):
    """
    Test retry fund source change handling when task log is ENQUEUED
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    TaskLog.objects.filter(expense_group_id=expense_group.id).delete()

    task_log = TaskLog.objects.create(
        workspace_id=workspace_id,
        type='CREATING_JOURNAL_ENTRY',
        expense_group_id=expense_group.id,
        status='ENQUEUED'
    )

    mock_process = mocker.patch(
        'apps.fyle.tasks.process_expense_group',
        return_value=None
    )

    retry_fund_source_change_handling(
        expense_group_id=expense_group.id,
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id
    )

    assert mock_process.call_count == 0
    task_log.delete()


def test_retry_fund_source_change_handling_complete_status(mocker, db):
    """
    Test retry fund source change handling when task log is COMPLETE
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    TaskLog.objects.filter(expense_group_id=expense_group.id).delete()

    task_log = TaskLog.objects.create(
        workspace_id=workspace_id,
        type='CREATING_JOURNAL_ENTRY',
        expense_group_id=expense_group.id,
        status='COMPLETE'
    )

    mock_cleanup = mocker.patch(
        'apps.fyle.tasks.cleanup_scheduled_task',
        return_value=None
    )

    mock_process = mocker.patch(
        'apps.fyle.tasks.process_expense_group',
        return_value=None
    )

    retry_fund_source_change_handling(
        expense_group_id=expense_group.id,
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id
    )

    assert mock_cleanup.call_count == 1
    assert mock_process.call_count == 0
    task_log.delete()


def test_retry_fund_source_change_handling_failed_status(mocker, db):
    """
    Test retry fund source change handling when task log is FAILED
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    TaskLog.objects.filter(expense_group_id=expense_group.id).delete()

    task_log = TaskLog.objects.create(
        workspace_id=workspace_id,
        type='CREATING_JOURNAL_ENTRY',
        expense_group_id=expense_group.id,
        status='FAILED'
    )

    mock_cleanup = mocker.patch(
        'apps.fyle.tasks.cleanup_scheduled_task',
        return_value=None
    )

    mock_process = mocker.patch(
        'apps.fyle.tasks.process_expense_group',
        return_value=None
    )

    retry_fund_source_change_handling(
        expense_group_id=expense_group.id,
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id
    )

    assert mock_cleanup.call_count == 1
    assert mock_process.call_count == 1
    task_log.delete()


def test_cleanup_scheduled_task_exists(mocker, db):
    """
    Test cleanup scheduled task when task exists
    """
    workspace_id = 1
    task_name = 'test_task_name'

    schedule_obj = Schedule.objects.create(
        func='apps.fyle.tasks.retry_fund_source_change_handling',
        name=task_name,
        args='[]'
    )

    cleanup_scheduled_task(task_name=task_name, workspace_id=workspace_id)

    assert not Schedule.objects.filter(id=schedule_obj.id).exists()
