import pytest
from fyle_accounting_mappings.models import ExpenseAttribute

from apps.tasks.models import TaskLog
from apps.fyle.models import ExpenseGroup
from apps.workspaces.models import (
    Configuration,
    FyleCredential,
    LastExportDetail,
    SageIntacctCredential,
    Workspace,
    WorkspaceSchedule,
)
from apps.workspaces.tasks import (
    create_admin_subscriptions,
    async_update_fyle_credentials,
    update_workspace_name,
    patch_integration_settings,
    patch_integration_settings_for_unmapped_cards,
    post_to_integration_settings,
    run_email_notification,
    run_sync_schedule,
    schedule_sync,
)
from tests.test_workspaces.fixtures import data


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

    eligible_calls = [call for call in mock_export.call_args_list if call[1]['expense_group_ids']]
    if eligible_calls:
        exported_ids = set(eligible_calls[-1][1]['expense_group_ids'])

        all_unexported_groups = set(ExpenseGroup.objects.filter(
            workspace_id=workspace_id,
            exported_at__isnull=True
        ).values_list('id', flat=True))

        excluded_groups = all_unexported_groups - exported_ids

        for group_id in excluded_groups:
            task_logs = TaskLog.objects.filter(
                workspace_id=workspace_id,
                expense_group_id=group_id
            ).exclude(
                type__in=['FETCHING_EXPENSES', 'CREATING_BILL_PAYMENT']
            )

            failed_logs = task_logs.filter(status='FAILED')
            assert failed_logs.exists(), f"Excluded expense group {group_id} should have FAILED task logs"

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

    eligible_calls = [call for call in mock_export.call_args_list if call[1]['expense_group_ids']]
    if eligible_calls:
        exported_ids = set(eligible_calls[-1][1]['expense_group_ids'])

        all_unexported_groups = set(ExpenseGroup.objects.filter(
            workspace_id=workspace_id,
            exported_at__isnull=True
        ).values_list('id', flat=True))

        excluded_groups = all_unexported_groups - exported_ids

        for group_id in excluded_groups:
            task_logs = TaskLog.objects.filter(
                workspace_id=workspace_id,
                expense_group_id=group_id
            ).exclude(
                type__in=['FETCHING_EXPENSES', 'CREATING_BILL_PAYMENT']
            )

            failed_logs = task_logs.filter(status='FAILED')
            assert failed_logs.exists(), f"Excluded expense group {group_id} should have FAILED task logs"

    task_log = TaskLog.objects.filter(
        workspace_id=workspace_id,
        type='FETCHING_EXPENSES'
    ).first()

    assert task_log.status == 'COMPLETE'


def test_run_sync_schedule_includes_expense_groups_without_task_logs(mocker, db):
    """
    Test that expense groups without task logs are included in the export
    This verifies our new behavior of including expense groups with no task logs
    """
    workspace_id = 1

    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses']
    )

    mock_export = mocker.patch('apps.workspaces.tasks.export_to_intacct')

    test_expense_group_1 = ExpenseGroup.objects.create(
        workspace_id=workspace_id,
        fund_source='PERSONAL',
        exported_at=None
    )

    test_expense_group_2 = ExpenseGroup.objects.create(
        workspace_id=workspace_id,
        fund_source='CCC',
        exported_at=None
    )

    run_sync_schedule(workspace_id)

    eligible_calls = [call for call in mock_export.call_args_list if call[1]['expense_group_ids']]
    if eligible_calls:
        exported_ids = set(eligible_calls[-1][1]['expense_group_ids'])

        groups_without_task_logs = ExpenseGroup.objects.filter(
            workspace_id=workspace_id,
            exported_at__isnull=True,
            tasklog__isnull=True
        ).values_list('id', flat=True)

        for group_id in groups_without_task_logs:
            assert group_id in exported_ids, f"Expense group {group_id} without task logs should be included in export"

        assert test_expense_group_1.id in exported_ids, f"Test expense group {test_expense_group_1.id} should be included in export"
        assert test_expense_group_2.id in exported_ids, f"Test expense group {test_expense_group_2.id} should be included in export"

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


def test_create_admin_subscriptions(db, mocker):
    """
    Test async create admin subscriptions
    """
    mocker.patch(
        'fyle.platform.apis.v1.admin.Subscriptions.post',
        return_value={}
    )
    create_admin_subscriptions(1)


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
    update_workspace_name(workspace.id, 'Bearer access_token')

    workspace = Workspace.objects.get(id=1)
    assert workspace.name == 'Test Org'


def test_patch_integration_settings_with_unmapped_card_count(db, add_fyle_credentials, mocker):
    """
    Test patch_integration_settings with unmapped_card_count
    """
    workspace_id = 2

    # Setup workspace with COMPLETE onboarding state
    workspace = Workspace.objects.get(id=workspace_id)
    workspace.onboarding_state = 'COMPLETE'
    workspace.save()

    # Setup FyleCredential with refresh token
    fyle_credential = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credential.refresh_token = 'test_refresh_token'
    fyle_credential.save()

    patch_request_mock = mocker.patch('apps.workspaces.tasks.patch_request')
    result = patch_integration_settings(workspace_id=workspace_id, unmapped_card_count=5)

    patch_request_mock.assert_called_once_with(
        mocker.ANY,  # URL
        {
            'tpa_name': 'Fyle Sage Intacct Integration',
            'unmapped_card_count': 5
        },
        'test_refresh_token'
    )

    assert result is True

    patch_request_mock.reset_mock()
    patch_request_mock.side_effect = Exception('Test exception')

    result = patch_integration_settings(workspace_id=workspace_id, unmapped_card_count=3)

    assert result is False


def test_patch_integration_settings_for_unmapped_cards(db, mocker):
    """
    Test patch_integration_settings_for_unmapped_cards
    """
    workspace_id = 1

    last_export_detail, _ = LastExportDetail.objects.get_or_create(
        workspace_id=workspace_id,
        defaults={'unmapped_card_count': 0}
    )
    patch_integration_settings_mock = mocker.patch(
        'apps.workspaces.tasks.patch_integration_settings',
        return_value=True
    )

    new_unmapped_count = 10
    patch_integration_settings_for_unmapped_cards(
        workspace_id=workspace_id,
        unmapped_card_count=new_unmapped_count
    )

    patch_integration_settings_mock.assert_called_once_with(
        workspace_id=workspace_id,
        unmapped_card_count=new_unmapped_count
    )

    last_export_detail.refresh_from_db()
    assert last_export_detail.unmapped_card_count == new_unmapped_count
    patch_integration_settings_mock.reset_mock()

    patch_integration_settings_for_unmapped_cards(
        workspace_id=workspace_id,
        unmapped_card_count=new_unmapped_count
    )
    patch_integration_settings_mock.assert_not_called()
    patch_integration_settings_mock.reset_mock()
    patch_integration_settings_mock.return_value = False
    last_export_detail.unmapped_card_count = 5
    last_export_detail.save()

    patch_integration_settings_for_unmapped_cards(
        workspace_id=workspace_id,
        unmapped_card_count=15
    )

    patch_integration_settings_mock.assert_called_once()
    last_export_detail.refresh_from_db()
    assert last_export_detail.unmapped_card_count == 5
