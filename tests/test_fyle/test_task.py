import hashlib
import json
from datetime import datetime, timezone
from unittest import mock

from django.urls import reverse
from django_q.models import Schedule
from fyle.platform.exceptions import InternalServerError, InvalidTokenError
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from fyle_accounting_mappings.models import ExpenseAttribute
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.fyle.models import Expense, ExpenseFilter, ExpenseGroup, ExpenseGroupSettings
from apps.fyle.tasks import (
    _delete_expense_groups_for_report,
    _handle_expense_ejected_from_report,
    cleanup_scheduled_task,
    construct_filter_for_affected_expense_groups,
    create_expense_groups,
    delete_expense_group_and_related_data,
    get_task_log_and_fund_source,
    handle_category_changes_for_expense,
    handle_expense_fund_source_change,
    handle_expense_report_change,
    handle_fund_source_changes_for_expense_ids,
    import_and_export_expenses,
    process_expense_group_for_fund_source_update,
    recreate_expense_groups,
    schedule_task_for_expense_group_fund_source_change,
    skip_expenses_and_post_accounting_export_summary,
    update_non_exported_expenses,
)
from apps.tasks.models import Error, TaskLog
from apps.workspaces.models import Configuration, FyleCredential, Workspace
from tests.helper import dict_compare_keys
from tests.test_fyle.fixtures import data


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


def test_create_expense_group_skipped_flow(mocker, api_client, test_connection, db):
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


def test_update_non_exported_expenses(db, mocker, api_client):
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


def test_import_and_export_expenses_with_export_call(mocker, db, test_connection):
    """
    Test import_and_export_expenses that hits the export_to_intacct call (line 303)
    """
    workspace_id = 1
    workspace = Workspace.objects.get(id=workspace_id)

    # Mock the expenses API call to return expenses
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses_webhook']
    )

    # Mock the export_to_intacct call to track if it's called
    mock_export_to_intacct = mocker.patch(
        'apps.fyle.tasks.export_to_intacct'
    )

    # Create expense groups to ensure len(expense_group_ids) > 0
    ExpenseGroup.objects.create(
        workspace=workspace,
        fund_source='PERSONAL',
        description={
            'report_id': 'rp1s1L3QtMpF',
            'claim_number': 'C/2021/12/R/1',
            'settlement_id': 'setqMAs7J5eOH',
            'employee_email': 'user1@fylefortesting.in'
        }
    )

    # Call with is_state_change_event=False to bypass the real-time export check
    import_and_export_expenses(
        report_id='rp1s1L3QtMpF',
        org_id=workspace.fyle_org_id,
        is_state_change_event=False,
        imported_from=ExpenseImportSourceEnum.DASHBOARD_SYNC
    )

    # Verify that export_to_intacct was called (this covers line 303)
    assert mock_export_to_intacct.call_count == 1

    # Verify the call arguments
    _, kwargs = mock_export_to_intacct.call_args
    assert kwargs['workspace_id'] == workspace.id
    assert kwargs['triggered_by'] == ExpenseImportSourceEnum.DASHBOARD_SYNC
    assert kwargs['run_in_rabbitmq_worker'] == True
    assert len(kwargs['expense_group_ids']) > 0


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
    expense = expense_group.expenses.first()
    changed_expense_ids = [expense.id]
    report_id = expense.report_id  # Use the actual report_id from the expense

    mock_process_expense_group = mocker.patch(
        'apps.fyle.tasks.process_expense_group_for_fund_source_update',
        return_value=None
    )

    handle_fund_source_changes_for_expense_ids(
        workspace_id=workspace_id,
        changed_expense_ids=changed_expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids={'PERSONAL': changed_expense_ids, 'CCC': []},
        task_name='test_task'
    )

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

    process_expense_group_for_fund_source_update(
        expense_group=expense_group,
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id,
        report_id='rp1s1L3QtMpF',
        affected_fund_source_expense_ids={'PERSONAL': changed_expense_ids}
    )
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

    process_expense_group_for_fund_source_update(
        expense_group=expense_group,
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id,
        report_id='rp1s1L3QtMpF',
        affected_fund_source_expense_ids={'PERSONAL': changed_expense_ids}
    )
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
        'apps.fyle.tasks.delete_expense_group_and_related_data',
        return_value=None
    )

    process_expense_group_for_fund_source_update(
        expense_group=expense_group,
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id,
        report_id='rp1s1L3QtMpF',
        affected_fund_source_expense_ids={'PERSONAL': changed_expense_ids}
    )
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
        'apps.fyle.tasks.delete_expense_group_and_related_data',
        return_value=None
    )

    process_expense_group_for_fund_source_update(
        expense_group=expense_group,
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id,
        report_id='rp1s1L3QtMpF',
        affected_fund_source_expense_ids={'PERSONAL': changed_expense_ids}
    )

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

    delete_expense_group_and_related_data(expense_group=expense_group, workspace_id=workspace_id)

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

    delete_expense_group_and_related_data(expense_group=expense_group, workspace_id=workspace_id)

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
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id,
        report_id='rp1s1L3QtMpF',
        affected_fund_source_expense_ids={'PERSONAL': changed_expense_ids}
    )

    assert Schedule.objects.filter(
        func='apps.fyle.tasks.handle_fund_source_changes_for_expense_ids',
        name__startswith='fund_source_change_retry_'
    ).exists() is True


def test_schedule_task_existing_schedule(mocker, db):
    """
    Test schedule task when schedule already exists
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    changed_expense_ids = [expense_group.expenses.first().id]

    # Generate the same task name that the function will generate
    hashed_name = hashlib.md5(str(changed_expense_ids).encode('utf-8')).hexdigest()[0:6]
    task_name = f'fund_source_change_retry_{hashed_name}_{workspace_id}'
    existing_schedule = Schedule.objects.create(
        func='apps.fyle.tasks.handle_fund_source_changes_for_expense_ids',
        name=task_name,
        args='[]'
    )

    mock_schedule = mocker.patch(
        'apps.fyle.tasks.schedule',
        return_value=None
    )

    expense = expense_group.expenses.first()
    report_id = expense.report_id
    schedule_task_for_expense_group_fund_source_change(
        changed_expense_ids=changed_expense_ids,
        workspace_id=workspace_id,
        report_id=report_id,
        affected_fund_source_expense_ids={'PERSONAL': changed_expense_ids}
    )

    assert mock_schedule.call_count == 0
    existing_schedule.delete()


def test_cleanup_scheduled_task_exists(mocker, db):
    """
    Test cleanup scheduled task when task exists
    """
    workspace_id = 1
    task_name = 'test_task_name'

    schedule_obj = Schedule.objects.create(
        func='apps.fyle.tasks.handle_fund_source_changes_for_expense_ids',
        name=task_name,
        args='[]'
    )

    cleanup_scheduled_task(task_name=task_name, workspace_id=workspace_id)

    assert not Schedule.objects.filter(id=schedule_obj.id).exists()


def test_import_and_export_expenses_fund_source_change_exception_handling(mocker, db):
    """
    Test import and export expenses fund source change exception handling - covers lines 290-293
    """
    workspace = Workspace.objects.get(id=1)
    report_id = 'rp1s1L3QtMpF'
    org_id = workspace.fyle_org_id

    # Mock the handle_expense_fund_source_change to raise exception
    mocker.patch(
        'apps.fyle.tasks.handle_expense_fund_source_change',
        side_effect=Exception("Test exception")
    )

    # Mock other required dependencies
    mocker.patch(
        'apps.fyle.tasks.get_fund_source',
        return_value='PERSONAL'
    )
    mocker.patch(
        'apps.fyle.tasks.get_source_account_type',
        return_value=['PERSONAL_CASH_ACCOUNT']
    )

    # Should not raise exception, just log it and continue
    import_and_export_expenses(
        report_id=report_id,
        org_id=org_id,
        is_state_change_event=True,
        report_state='APPROVED'
    )


def test_update_non_exported_expenses_fund_source_change_logging(mocker, db):
    """
    Test fund source change logging in update_non_exported_expenses - covers lines 371-372
    """
    # Use existing expense from fixtures - check if any exist first
    expense = Expense.objects.filter(workspace_id=1).first()
    if not expense:
        # Skip test if no expenses exist in fixtures
        return

    # Mock the expense data to have different fund source
    mock_expense_data = {
        'id': expense.expense_id,
        'source_account_type': 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'  # Different from current
    }

    mock_handle_fund_source_changes = mocker.patch(
        'apps.fyle.tasks.handle_fund_source_changes_for_expense_ids',
        return_value=None
    )

    update_non_exported_expenses(mock_expense_data)

    # Verify that the fund source change handler was called
    mock_handle_fund_source_changes.assert_called_once()


def test_construct_filter_for_affected_expense_groups_personal_expense_ccc_expense(mocker, db):
    """
    Test construct filter for affected expense groups - covers lines 490-493
    """
    workspace_id = 1
    report_id = 'test_report'
    changed_expense_ids = [1, 2, 3]
    affected_fund_source_expense_ids = {'PERSONAL': [1, 2], 'CCC': [3]}

    # Mock grouping types where both are 'expense'
    mocker.patch(
        'apps.fyle.tasks.get_grouping_types',
        return_value={'PERSONAL': 'expense', 'CCC': 'expense'}
    )

    filter_query = construct_filter_for_affected_expense_groups(
        workspace_id, report_id, changed_expense_ids, affected_fund_source_expense_ids
    )

    # Should create a Q object for expense IDs
    assert filter_query is not None


def test_construct_filter_for_affected_expense_groups_mixed_grouping_personal_report_ccc_expense(mocker, db):
    """
    Test construct filter with mixed grouping types - covers lines 498-499
    """
    workspace_id = 1
    report_id = 'test_report'
    changed_expense_ids = [1, 2, 3]
    affected_fund_source_expense_ids = {'PERSONAL': [1, 2], 'CCC': [3]}

    # Mock grouping types: PERSONAL = report, CCC = expense
    mocker.patch(
        'apps.fyle.tasks.get_grouping_types',
        return_value={'PERSONAL': 'report', 'CCC': 'expense'}
    )

    filter_query = construct_filter_for_affected_expense_groups(
        workspace_id, report_id, changed_expense_ids, affected_fund_source_expense_ids
    )

    assert filter_query is not None


def test_construct_filter_for_affected_expense_groups_mixed_grouping_personal_expense_ccc_report(mocker, db):
    """
    Test construct filter with mixed grouping types - covers lines 501-502
    """
    workspace_id = 1
    report_id = 'test_report'
    changed_expense_ids = [1, 2, 3]
    affected_fund_source_expense_ids = {'PERSONAL': [1, 2], 'CCC': [3]}

    # Mock grouping types: PERSONAL = expense, CCC = report
    mocker.patch(
        'apps.fyle.tasks.get_grouping_types',
        return_value={'PERSONAL': 'expense', 'CCC': 'report'}
    )

    filter_query = construct_filter_for_affected_expense_groups(
        workspace_id, report_id, changed_expense_ids, affected_fund_source_expense_ids
    )

    assert filter_query is not None


def test_construct_filter_for_affected_expense_groups_ccc_fund_source(mocker, db):
    """
    Test construct filter for CCC fund source - covers lines 505-509
    """
    workspace_id = 1
    report_id = 'test_report'
    changed_expense_ids = [1, 2, 3]
    affected_fund_source_expense_ids = {'PERSONAL': [], 'CCC': [1, 2, 3]}

    # Test CCC fund source with PERSONAL=report, CCC=expense
    mock_get_grouping_types = mocker.patch(
        'apps.fyle.tasks.get_grouping_types',
        return_value={'PERSONAL': 'report', 'CCC': 'expense'}
    )

    filter_query = construct_filter_for_affected_expense_groups(
        workspace_id, report_id, changed_expense_ids, affected_fund_source_expense_ids
    )

    assert filter_query is not None

    # Test CCC fund source with PERSONAL=expense, CCC=report
    mock_get_grouping_types.return_value = {'PERSONAL': 'expense', 'CCC': 'report'}

    filter_query = construct_filter_for_affected_expense_groups(
        workspace_id, report_id, changed_expense_ids, affected_fund_source_expense_ids
    )

    assert filter_query is not None


def test_handle_expense_fund_source_change_platform_call(mocker, db):
    """
    Test handle expense fund source change platform call - covers lines 522, 528-532, 540, 545-553, 555-558
    """
    workspace_id = 1
    report_id = 'test_report'

    # Use existing expense from fixtures - check if any exist first
    expense = Expense.objects.filter(workspace_id=workspace_id).first()
    if not expense:
        # Skip test if no expenses exist in fixtures
        return

    # Mock platform response with changed fund source
    mock_expenses = [
        {
            'id': expense.expense_id,
            'source_account_type': 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'  # Different from current
        }
    ]

    mock_platform = mocker.Mock()
    mock_platform.expenses.get.return_value = mock_expenses

    mocker.patch(
        'apps.fyle.models.Expense.create_expense_objects',
        return_value=None
    )

    mocker.patch(
        'apps.fyle.tasks.handle_fund_source_changes_for_expense_ids',
        return_value=None
    )

    handle_expense_fund_source_change(workspace_id, report_id, mock_platform)

    # Verify platform was called with correct parameters
    mock_platform.expenses.get.assert_called_once_with(
        source_account_type=['PERSONAL_CASH_ACCOUNT', 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'],
        report_id=report_id,
        filter_credit_expenses=False
    )


def test_handle_fund_source_changes_no_expense_groups_found(mocker, db):
    """
    Test handle fund source changes when no expense groups found - covers lines 585-586
    """
    workspace_id = 1
    changed_expense_ids = [999]  # Non-existent expense IDs
    report_id = 'test_report'
    affected_fund_source_expense_ids = {'PERSONAL': [999], 'CCC': []}

    # Mock get_grouping_types
    mocker.patch(
        'apps.fyle.tasks.get_grouping_types',
        return_value={'PERSONAL': 'expense', 'CCC': 'expense'}
    )

    # This should return early when no expense groups are found
    handle_fund_source_changes_for_expense_ids(
        workspace_id=workspace_id,
        changed_expense_ids=changed_expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )


def test_handle_fund_source_changes_all_groups_exported(mocker, db):
    """
    Test handle fund source changes when all groups are exported - covers lines 606-608
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    expense = expense_group.expenses.first()
    changed_expense_ids = [expense.id]
    report_id = expense.report_id
    affected_fund_source_expense_ids = {'PERSONAL': changed_expense_ids, 'CCC': []}

    # Mock get_grouping_types
    mocker.patch(
        'apps.fyle.tasks.get_grouping_types',
        return_value={'PERSONAL': 'expense', 'CCC': 'expense'}
    )

    # Mock process_expense_group_for_fund_source_update to return True (exported)
    mocker.patch(
        'apps.fyle.tasks.process_expense_group_for_fund_source_update',
        return_value=True
    )

    mock_recreate_expense_groups = mocker.patch(
        'apps.fyle.tasks.recreate_expense_groups',
        return_value=None
    )

    mock_cleanup_scheduled_task = mocker.patch(
        'apps.fyle.tasks.cleanup_scheduled_task',
        return_value=None
    )

    handle_fund_source_changes_for_expense_ids(
        workspace_id=workspace_id,
        changed_expense_ids=changed_expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids,
        task_name='test_task'
    )

    # Verify recreate and cleanup were called
    mock_recreate_expense_groups.assert_called_once()
    mock_cleanup_scheduled_task.assert_called_once_with(task_name='test_task', workspace_id=workspace_id)


def test_recreate_expense_groups_no_expenses_found(mocker, db):
    """
    Test recreate expense groups when no expenses found - covers lines 708-709
    """
    workspace_id = 1
    expense_ids = [999]  # Non-existent expense IDs

    # This should return early when no expenses are found
    recreate_expense_groups(workspace_id=workspace_id, expense_ids=expense_ids)


def test_recreate_expense_groups_with_filters(mocker, db):
    """
    Test recreate expense groups with expense filters - covers lines 733-735, 737
    """
    workspace_id = 1

    # Use existing expense from fixtures - check if any exist first
    expense = Expense.objects.filter(workspace_id=workspace_id).first()
    if not expense:
        # Skip test if no expenses exist in fixtures
        return

    expense_ids = [expense.id]

    # Create an expense filter
    ExpenseFilter.objects.create(
        workspace_id=workspace_id,
        condition='employee_email',
        operator='in',
        values=['test@example.com'],
        rank=1
    )

    mock_construct_expense_filter_query = mocker.patch(
        'apps.fyle.tasks.construct_expense_filter_query',
        return_value=mocker.Mock()
    )

    mock_skip_expenses = mocker.patch(
        'apps.fyle.tasks.skip_expenses_and_post_accounting_export_summary',
        return_value=None
    )

    mocker.patch(
        'apps.fyle.models.ExpenseGroup.create_expense_groups_by_report_id_fund_source',
        return_value=[]
    )

    recreate_expense_groups(workspace_id=workspace_id, expense_ids=expense_ids)

    # Verify filter functions were called
    mock_construct_expense_filter_query.assert_called_once()
    mock_skip_expenses.assert_called_once()


def test_cleanup_scheduled_task_no_task_found(mocker, db):
    """
    Test cleanup scheduled task when no task found - covers line 819
    """
    workspace_id = 1
    task_name = 'non_existent_task'

    # This should handle the case when no scheduled task is found
    cleanup_scheduled_task(task_name=task_name, workspace_id=workspace_id)


def test_get_task_log_and_fund_source(db):
    """
    Test get_task_log_and_fund_source function - covers lines 68-83
    """
    workspace_id = 1
    task_log, fund_source = get_task_log_and_fund_source(workspace_id)

    assert task_log is not None
    assert task_log.workspace_id == workspace_id
    assert task_log.type == 'FETCHING_EXPENSES'
    assert task_log.status == 'IN_PROGRESS'

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    expected_fund_source = []
    if configuration.reimbursable_expenses_object:
        expected_fund_source.append('PERSONAL')
    if configuration.corporate_credit_card_expenses_object:
        expected_fund_source.append('CCC')

    assert fund_source == expected_fund_source


def test_update_non_exported_expenses_fund_source_change_detection(mocker, db):
    """
    Test update_non_exported_expenses fund source change detection - covers lines 371-372
    """
    expense = Expense.objects.filter(workspace_id=1).first()
    if not expense:
        return

    expense.fund_source = 'PERSONAL'
    expense.save()

    mocker.patch('apps.fyle.tasks.get_fund_source', side_effect=['PERSONAL', 'CCC'])
    mock_handler = mocker.patch('apps.fyle.tasks.handle_fund_source_changes_for_expense_ids')

    expense_objects = [{
        'id': expense.expense_id,
        'fund_source': 'CCC'
    }]

    update_non_exported_expenses(expense_objects[0])
    mock_handler.assert_called_once()


def test_handle_expense_fund_source_change_simple(mocker, db):
    """
    Simple test for handle_expense_fund_source_change - covers lines 522-558
    """
    workspace_id = 1
    report_id = 'test_simple'

    mock_platform = mocker.MagicMock()
    mock_platform.expenses.get.return_value = [
        {
            'id': 'exp123',
            'source_account_type': 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'
        }
    ]

    mock_queryset = mocker.MagicMock()
    mock_queryset.values_list.return_value = [('exp123', 'PERSONAL', 1)]
    mocker.patch('apps.fyle.models.Expense.objects.filter', return_value=mock_queryset)

    mock_create = mocker.patch('apps.fyle.models.Expense.create_expense_objects')
    mock_handle = mocker.patch('apps.fyle.tasks.handle_fund_source_changes_for_expense_ids')

    handle_expense_fund_source_change(workspace_id, report_id, mock_platform)

    mock_create.assert_called_once()
    mock_handle.assert_called_once()


def test_recreate_expense_groups_with_filters_simple(mocker, db):
    """
    Simple test for recreate_expense_groups with filters - covers lines 733-737
    """
    workspace_id = 1
    configuration = Configuration.objects.filter(workspace_id=workspace_id).first()
    if not configuration:
        return

    expenses = list(Expense.objects.filter(workspace_id=workspace_id)[:1])
    if not expenses:
        return

    expense_filter = ExpenseFilter.objects.create(
        workspace_id=workspace_id,
        condition='employee_email',
        operator='in',
        values=['test@test.com'],
        rank=1
    )

    mock_construct = mocker.patch('apps.fyle.tasks.construct_expense_filter_query', return_value={'test': 'filter'})
    mock_skip = mocker.patch('apps.fyle.tasks.skip_expenses_and_post_accounting_export_summary')
    mocker.patch('apps.fyle.tasks.Expense.objects.filter', return_value=expenses)
    mocker.patch('apps.fyle.tasks.ExpenseGroup.create_expense_groups_by_report_id_fund_source')

    recreate_expense_groups(workspace_id=workspace_id, expense_ids=[expense.id for expense in expenses])

    mock_construct.assert_called_once()
    mock_skip.assert_called_once()

    expense_filter.delete()


def test_handle_expense_report_change_added_to_report(db, mocker):
    """
    Test handle_expense_report_change with ADDED_TO_REPORT action
    """
    workspace = Workspace.objects.get(id=1)

    expense_data = {
        'id': 'tx1234567890',
        'org_id': workspace.fyle_org_id,
        'report_id': 'rp1234567890'
    }

    mock_delete = mocker.patch('apps.fyle.tasks._delete_expense_groups_for_report')

    handle_expense_report_change(expense_data, 'ADDED_TO_REPORT')

    mock_delete.assert_called_once()
    args = mock_delete.call_args[0]
    assert args[0] == 'rp1234567890'
    assert args[1].id == workspace.id


def test_handle_expense_report_change_ejected_from_report(db, mocker, add_expense_report_data):
    """
    Test handle_expense_report_change with EJECTED_FROM_REPORT action
    """
    workspace = Workspace.objects.get(id=1)
    expense = add_expense_report_data['expenses'][0]

    expense_data = {
        'id': expense.expense_id,
        'org_id': workspace.fyle_org_id,
        'report_id': expense.report_id
    }

    mock_handle = mocker.patch('apps.fyle.tasks._handle_expense_ejected_from_report')

    handle_expense_report_change(expense_data, 'EJECTED_FROM_REPORT')

    mock_handle.assert_called_once()


def test_delete_expense_groups_for_report_basic(db, mocker, add_expense_report_data):
    """
    Test _delete_expense_groups_for_report deletes non-exported expense groups
    """
    workspace = Workspace.objects.get(id=1)

    expense = add_expense_report_data['expenses'][0]
    report_id = expense.report_id

    mock_delete = mocker.patch('apps.fyle.tasks.delete_expense_group_and_related_data')

    _delete_expense_groups_for_report(report_id, workspace)

    assert mock_delete.called


def test_delete_expense_groups_for_report_no_expenses(db, mocker):
    """
    Test _delete_expense_groups_for_report with no expenses in database
    Case: Non-existent report_id
    """
    workspace = Workspace.objects.get(id=1)
    report_id = 'rpNonExistent123'

    _delete_expense_groups_for_report(report_id, workspace)


def test_delete_expense_groups_for_report_with_active_task_logs(db, mocker, add_expense_report_data):
    """
    Test _delete_expense_groups_for_report skips groups with active task logs
    """
    workspace = Workspace.objects.get(id=1)
    expense_group = add_expense_report_data['expense_group']

    TaskLog.objects.create(
        workspace_id=workspace.id,
        expense_group_id=expense_group.id,
        type='CREATING_BILL',
        status='IN_PROGRESS'
    )

    report_id = expense_group.expenses.first().report_id

    mock_delete = mocker.patch('apps.fyle.tasks.delete_expense_group_and_related_data')

    _delete_expense_groups_for_report(report_id, workspace)

    assert not mock_delete.called


def test_delete_expense_groups_for_report_preserves_exported(db, mocker, add_expense_report_data):
    """
    Test _delete_expense_groups_for_report preserves exported expense groups
    """
    workspace = Workspace.objects.get(id=1)

    expense_group = add_expense_report_data['expense_group']

    expense_group.exported_at = datetime.now(tz=timezone.utc)
    expense_group.save()

    report_id = expense_group.expenses.first().report_id

    mock_delete = mocker.patch('apps.fyle.tasks.delete_expense_group_and_related_data')

    _delete_expense_groups_for_report(report_id, workspace)

    assert not mock_delete.called


def test_handle_expense_ejected_from_report_removes_from_group(db, add_expense_report_data):
    """
    Test _handle_expense_ejected_from_report removes expense from group
    """
    workspace = Workspace.objects.get(id=1)

    expense_group = add_expense_report_data['expense_group']
    expenses = add_expense_report_data['expenses']

    expense_to_remove = expenses[0]

    expense_data = {
        'id': expense_to_remove.expense_id,
        'report_id': None
    }

    initial_expense_count = expense_group.expenses.count()

    _handle_expense_ejected_from_report(expense_to_remove, expense_data, workspace)

    expense_group.refresh_from_db()

    assert expense_group.expenses.count() == initial_expense_count - 1
    assert expense_to_remove not in expense_group.expenses.all()
    assert ExpenseGroup.objects.filter(id=expense_group.id).exists()


def test_handle_expense_ejected_from_report_deletes_empty_group(db, add_expense_report_data):
    """
    Test _handle_expense_ejected_from_report deletes group when last expense is removed
    """
    workspace = Workspace.objects.get(id=1)

    expense_group = add_expense_report_data['expense_group']
    expense = add_expense_report_data['expenses'][0]
    expense_group.expenses.set([expense])

    expense_data = {
        'id': expense.expense_id,
        'report_id': None
    }

    group_id = expense_group.id

    _handle_expense_ejected_from_report(expense, expense_data, workspace)

    assert not ExpenseGroup.objects.filter(id=group_id).exists()


def test_handle_expense_ejected_from_report_no_group_found(db, add_expense_report_data):
    """
    Test _handle_expense_ejected_from_report when expense has no group
    """
    workspace = Workspace.objects.get(id=1)
    expense = add_expense_report_data['expenses'][0]

    # Remove expense from its group to simulate orphaned expense
    expense_group = add_expense_report_data['expense_group']
    expense_group.expenses.remove(expense)

    expense_data = {
        'id': expense.expense_id,
        'report_id': None
    }

    _handle_expense_ejected_from_report(expense, expense_data, workspace)


def test_handle_expense_ejected_from_report_with_active_task_log(db, add_expense_report_data):
    """
    Test _handle_expense_ejected_from_report skips removal when task log is active
    """
    workspace = Workspace.objects.get(id=1)

    expense_group = add_expense_report_data['expense_group']
    expense = add_expense_report_data['expenses'][0]
    initial_count = expense_group.expenses.count()

    TaskLog.objects.create(
        workspace_id=workspace.id,
        expense_group_id=expense_group.id,
        type='CREATING_BILL',
        status='ENQUEUED'
    )

    expense_data = {
        'id': expense.expense_id,
        'report_id': None
    }

    _handle_expense_ejected_from_report(expense, expense_data, workspace)

    expense_group.refresh_from_db()

    assert expense_group.expenses.count() == initial_count
    assert expense in expense_group.expenses.all()


def test_handle_expense_report_change_ejected_expense_not_found(db, mocker):
    """
    Test handle_expense_report_change when expense doesn't exist in workspace (EJECTED_FROM_REPORT)
    """
    workspace = Workspace.objects.get(id=1)

    expense_data = {
        'id': 'txNonExistent999',
        'org_id': workspace.fyle_org_id,
        'report_id': None
    }

    handle_expense_report_change(expense_data, 'EJECTED_FROM_REPORT')


def test_handle_expense_report_change_ejected_from_exported_group(db, add_expense_report_data):
    """
    Test handle_expense_report_change skips when expense is part of exported group (EJECTED_FROM_REPORT)
    """
    workspace = Workspace.objects.get(id=1)
    expense_group = add_expense_report_data['expense_group']
    expense = add_expense_report_data['expenses'][0]

    expense_group.exported_at = datetime.now(tz=timezone.utc)
    expense_group.save()

    expense_data = {
        'id': expense.expense_id,
        'org_id': workspace.fyle_org_id,
        'report_id': None
    }

    handle_expense_report_change(expense_data, 'EJECTED_FROM_REPORT')

    expense_group.refresh_from_db()
    assert expense in expense_group.expenses.all()


def test_handle_category_changes_for_expense(db, add_category_test_expense, add_category_test_expense_group, add_category_mapping_error, add_category_expense_attribute, add_destination_attributes_for_category):
    """
    Test handle_category_changes_for_expense
    """
    workspace = Workspace.objects.get(id=1)
    expense = add_category_test_expense
    expense_group = add_category_test_expense_group
    error = add_category_mapping_error
    configuration = Configuration.objects.get(workspace_id=workspace.id)

    error.mapping_error_expense_group_ids = [expense_group.id, 999]
    error.save()

    handle_category_changes_for_expense(expense=expense, new_category='New Category')

    error.refresh_from_db()
    assert expense_group.id not in error.mapping_error_expense_group_ids
    assert 999 in error.mapping_error_expense_group_ids

    error.mapping_error_expense_group_ids = [expense_group.id]
    error.save()

    handle_category_changes_for_expense(expense=expense, new_category='Another Category')

    assert not Error.objects.filter(id=error.id, workspace_id=workspace.id, type='CATEGORY_MAPPING').exists()

    expense_group.delete()

    expense_group_2 = ExpenseGroup.objects.create(
        workspace_id=workspace.id,
        fund_source='PERSONAL',
        description={'employee_email': expense.employee_email},
        employee_name=expense.employee_name
    )
    expense_group_2.expenses.add(expense)

    unmapped_category_attr = ExpenseAttribute.objects.create(
        workspace_id=workspace.id,
        attribute_type='CATEGORY',
        value='Unmapped Category Personal',
        display_name='Category',
        source_id='catUnmapped1'
    )

    original_config = configuration.reimbursable_expenses_object
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    handle_category_changes_for_expense(expense=expense, new_category='Unmapped Category Personal')

    new_error = Error.objects.filter(
        workspace_id=workspace.id,
        type='CATEGORY_MAPPING',
        expense_attribute=unmapped_category_attr
    ).first()

    assert new_error is not None
    assert expense_group_2.id in new_error.mapping_error_expense_group_ids

    configuration.reimbursable_expenses_object = original_config
    configuration.save()

    expense_group_2.delete()

    expense_group_3 = ExpenseGroup.objects.create(
        workspace_id=workspace.id,
        fund_source='CCC',
        description={'employee_email': expense.employee_email},
        employee_name=expense.employee_name
    )
    expense_group_3.expenses.add(expense)

    unmapped_category_attr_ccc = ExpenseAttribute.objects.create(
        workspace_id=workspace.id,
        attribute_type='CATEGORY',
        value='Unmapped Category CCC',
        display_name='Category',
        source_id='catUnmapped2'
    )

    original_ccc_config = configuration.corporate_credit_card_expenses_object
    configuration.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    handle_category_changes_for_expense(expense=expense, new_category='Unmapped Category CCC')

    ccc_error = Error.objects.filter(
        workspace_id=workspace.id,
        type='CATEGORY_MAPPING',
        expense_attribute=unmapped_category_attr_ccc
    ).first()

    assert ccc_error is not None
    assert expense_group_3.id in ccc_error.mapping_error_expense_group_ids

    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()
    expense_group_3.delete()

    expense_group_4 = ExpenseGroup.objects.create(
        workspace_id=workspace.id,
        fund_source='CCC',
        description={'employee_email': expense.employee_email},
        employee_name=expense.employee_name
    )
    expense_group_4.expenses.add(expense)

    unmapped_category_attr_ccc_je = ExpenseAttribute.objects.create(
        workspace_id=workspace.id,
        attribute_type='CATEGORY',
        value='Unmapped Category CCC JE',
        display_name='Category',
        source_id='catUnmapped3'
    )

    handle_category_changes_for_expense(expense=expense, new_category='Unmapped Category CCC JE')

    ccc_je_error = Error.objects.filter(
        workspace_id=workspace.id,
        type='CATEGORY_MAPPING',
        expense_attribute=unmapped_category_attr_ccc_je
    ).first()

    assert ccc_je_error is not None
    assert expense_group_4.id in ccc_je_error.mapping_error_expense_group_ids

    configuration.corporate_credit_card_expenses_object = original_ccc_config
    configuration.save()


def test_update_non_exported_expenses_category_change(mocker, db):
    """
    Test update_non_exported_expenses_category_change
    """
    expense_data = data['raw_expense'].copy()
    expense_data['category']['name'] = 'New Category'
    expense_data['category']['sub_category'] = 'New Sub Category'
    org_id = expense_data['org_id']

    default_raw_expense = data['default_raw_expense'].copy()
    default_raw_expense['category'] = 'Old Category'
    default_raw_expense['sub_category'] = 'Old Sub Category'

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

    mock_fyle_expenses = mocker.patch('apps.fyle.tasks.FyleExpenses')
    constructed_expense = expense_data.copy()
    constructed_expense['category'] = expense_data['category']['name']
    constructed_expense['sub_category'] = expense_data['category']['sub_category']
    constructed_expense['source_account_type'] = 'PERSONAL_CASH_ACCOUNT'
    mock_fyle_expenses.return_value.construct_expense_object.return_value = [constructed_expense]

    mocker.patch('apps.fyle.tasks.Expense.create_expense_objects', return_value=None)

    mock_handle_category_changes = mocker.patch(
        'apps.fyle.tasks.handle_category_changes_for_expense',
        return_value=None
    )

    update_non_exported_expenses(expense_data)

    assert mock_handle_category_changes.call_count == 1
    _, kwargs = mock_handle_category_changes.call_args
    assert kwargs['expense'] == expense_created
    assert kwargs['new_category'] == 'New Category / New Sub Category'

    expense_created.category = 'Same Category'
    expense_created.sub_category = 'Same Category'
    expense_created.save()

    expense_data_2 = data['raw_expense'].copy()
    expense_data_2['category']['name'] = 'Changed'
    expense_data_2['category']['sub_category'] = 'Changed'

    constructed_expense_2 = expense_data_2.copy()
    constructed_expense_2['category'] = 'Changed'
    constructed_expense_2['sub_category'] = 'Changed'
    constructed_expense_2['source_account_type'] = 'PERSONAL_CASH_ACCOUNT'
    mock_fyle_expenses.return_value.construct_expense_object.return_value = [constructed_expense_2]

    update_non_exported_expenses(expense_data_2)

    assert mock_handle_category_changes.call_count == 2
    _, kwargs = mock_handle_category_changes.call_args
    assert kwargs['new_category'] == 'Changed'

    expense_created.category = 'Old Cat'
    expense_created.sub_category = None
    expense_created.save()

    expense_data_3 = data['raw_expense'].copy()
    expense_data_3['category']['name'] = 'New Cat'
    expense_data_3['category']['sub_category'] = None

    constructed_expense_3 = expense_data_3.copy()
    constructed_expense_3['category'] = 'New Cat'
    constructed_expense_3['sub_category'] = None
    constructed_expense_3['source_account_type'] = 'PERSONAL_CASH_ACCOUNT'
    mock_fyle_expenses.return_value.construct_expense_object.return_value = [constructed_expense_3]

    update_non_exported_expenses(expense_data_3)

    assert mock_handle_category_changes.call_count == 3
    _, kwargs = mock_handle_category_changes.call_args
    assert kwargs['new_category'] == 'New Cat'
