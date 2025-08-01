import pytest

from fyle_accounting_mappings.models import ExpenseAttribute

from apps.tasks.models import TaskLog
from apps.workspaces.models import (
    Workspace,
    Configuration,
    FyleCredential,
    WorkspaceSchedule,
    SageIntacctCredential
)
from apps.workspaces.tasks import (
    run_sync_schedule,
    schedule_sync,
    run_email_notification,
    async_update_fyle_credentials,
    post_to_integration_settings,
    async_create_admin_subcriptions,
    async_update_workspace_name
)
from .fixtures import data


def test_schedule_sync(db):
    """
    Test schedule sync
    """
    workspace_id = 1

    schedule_sync(
        hours=1,
        schedule_enabled=True,
        email_added=[
            'ashwin.t@fyle.in'
        ],
        emails_selected=[
            'ashwin.t@fyle.in'
        ],
        workspace_id=workspace_id,
        is_real_time_export_enabled=False
    )

    ws_schedule = WorkspaceSchedule.objects.filter(
        workspace_id=workspace_id
    ).first()

    assert ws_schedule.schedule.func == 'apps.workspaces.tasks.run_sync_schedule'

    schedule_sync(
        hours=1,
        schedule_enabled=False,
        email_added=None,
        emails_selected=[
            'ashwin.t@fyle.in'
        ],
        workspace_id=workspace_id,
        is_real_time_export_enabled=False
    )

    ws_schedule = WorkspaceSchedule.objects.filter(
        workspace_id=workspace_id
    ).first()

    assert ws_schedule.schedule == None


def test_run_sync_schedule(mocker, db):
    """
    Test run sync schedule with new failed expense group filtering logic
    """
    workspace_id = 1

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses']
    )

    mock_export = mocker.patch('apps.workspaces.tasks.export_to_intacct')

    run_sync_schedule(workspace_id)

    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    configuration.save()

    run_sync_schedule(workspace_id)

    configuration.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    run_sync_schedule(workspace_id)

    # Verify that export_to_intacct was called with only eligible expense groups
    # Based on test data, expense groups 1, 2, 3 have failed TaskLogs, so they should be excluded
    eligible_calls = [call for call in mock_export.call_args_list if call[1]['expense_group_ids']]
    if eligible_calls:
        exported_ids = eligible_calls[-1][1]['expense_group_ids']

        failed_expense_group_ids = set(TaskLog.objects.filter(
            workspace_id=workspace_id,
            status='FAILED',
            expense_group__isnull=False
        ).exclude(
            type__in=['FETCHING_EXPENSES', 'CREATING_BILL_PAYMENT']
        ).values_list('expense_group_id', flat=True))

        for group_id in exported_ids:
            assert group_id not in failed_expense_group_ids, f"Failed expense group {group_id} should not be exported"

    task_log = TaskLog.objects.filter(
        workspace_id=workspace_id,
        type='FETCHING_EXPENSES'
    ).first()

    assert task_log.status == 'COMPLETE'


def test_run_sync_schedule_je(mocker, db):
    """
    Test run sync schedule with journal entries and new filtering logic
    """
    workspace_id = 1

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses']
    )

    mock_export = mocker.patch('apps.workspaces.tasks.export_to_intacct')

    run_sync_schedule(workspace_id)

    configuration.reimbursable_expenses_object = 'JOURNAL_ENTRY'
    configuration.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    configuration.save()

    run_sync_schedule(workspace_id)

    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()

    run_sync_schedule(workspace_id)

    # Verify that export_to_intacct was called with only eligible expense groups
    eligible_calls = [call for call in mock_export.call_args_list if call[1]['expense_group_ids']]
    if eligible_calls:
        exported_ids = eligible_calls[-1][1]['expense_group_ids']

        failed_expense_group_ids = set(TaskLog.objects.filter(
            workspace_id=workspace_id,
            status='FAILED',
            expense_group__isnull=False
        ).exclude(
            type__in=['FETCHING_EXPENSES', 'CREATING_BILL_PAYMENT']
        ).values_list('expense_group_id', flat=True))

        for group_id in exported_ids:
            assert group_id not in failed_expense_group_ids, f"Failed expense group {group_id} should not be exported"

    task_log = TaskLog.objects.filter(
        workspace_id=workspace_id,
        type='FETCHING_EXPENSES'
    ).first()

    assert task_log.status == 'COMPLETE'


def test_email_notification(mocker,db):
    """
    Test email notification
    """
    workspace_id = 1

    schedule_sync(
        hours=1,
        schedule_enabled=True,
        email_added=None,
        emails_selected=[
            'user5@fyleforgotham.in'
        ],
        workspace_id=workspace_id,
        is_real_time_export_enabled=False
    )

    ws_schedule = WorkspaceSchedule.objects.filter(
        workspace_id=workspace_id
    ).first()

    mocker.patch('apps.workspaces.tasks.send_email',
                 return_value=None)

    run_email_notification(workspace_id=workspace_id)

    updated_ws_schedule = WorkspaceSchedule.objects.filter(
        workspace_id=workspace_id, id=ws_schedule.id
    ).first()

    assert updated_ws_schedule.error_count == 3

    attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id, value='user5@fyleforgotham.in').first()
    attribute.delete()

    ws_schedule.enabled = True
    ws_schedule.additional_email_options = [{'email': 'user5@fyleforgotham.in', 'name': 'Ashwin'}]
    ws_schedule.save()

    run_email_notification(workspace_id=workspace_id)
    updated_ws_schedule = WorkspaceSchedule.objects.filter(
        workspace_id=workspace_id, id=ws_schedule.id
    ).first()

    assert updated_ws_schedule.error_count == 3

    SageIntacctCredential.objects.filter(workspace_id=workspace_id).delete()

    run_email_notification(workspace_id=workspace_id)


def test_async_update_fyle_credentials(db):
    """
    Test async update fyle credentials
    """
    workspace_id = 1
    refresh_token = 'hehehuhu'

    async_update_fyle_credentials('or79Cob97KSh', refresh_token)

    fyle_credentials = FyleCredential.objects.filter(workspace_id=workspace_id).first()

    assert fyle_credentials.refresh_token == refresh_token


def test_async_create_admin_subcriptions(db, mocker):
    """
    Test async create admin subscriptions
    """
    mocker.patch(
        'fyle.platform.apis.v1.admin.Subscriptions.post',
        return_value={}
    )
    async_create_admin_subcriptions(1)


@pytest.mark.django_db(databases=['default'])
def test_post_to_integration_settings(mocker):
    """
    Test post to integration settings
    """
    mocker.patch(
        'apps.fyle.helpers.post_request',
        return_value=''
    )

    no_exception = True
    post_to_integration_settings(1, True)

    # If exception is raised, this test will fail
    assert no_exception


def test_async_update_workspace_name(db, mocker):
    """
    Test async update workspace name
    """
    mocker.patch(
        'apps.workspaces.tasks.get_fyle_admin',
        return_value={'data': {'org': {'name': 'Test Org'}}}
    )
    workspace = Workspace.objects.get(id=1)
    async_update_workspace_name(workspace, 'Bearer access_token')

    workspace = Workspace.objects.get(id=1)
    assert workspace.name == 'Test Org'
