from datetime import datetime

import pytest
from fyle.platform.exceptions import InvalidTokenError
from fyle_accounting_mappings.models import ExpenseAttribute

from apps.fyle.models import ExpenseGroup
from apps.tasks.models import TaskLog
from apps.workspaces.models import (
    Configuration,
    FeatureConfig,
    FyleCredential,
    LastExportDetail,
    SageIntacctCredential,
    Workspace,
    WorkspaceSchedule,
)
from apps.workspaces.tasks import (
    async_update_fyle_credentials,
    create_admin_subscriptions,
    patch_integration_settings,
    patch_integration_settings_for_unmapped_cards,
    post_to_integration_settings,
    run_sync_schedule,
    schedule_sync,
    sync_org_settings,
    trigger_email_notification,
    update_workspace_name,
)
from tests.test_workspaces.fixtures import data


def test_schedule_sync_enabled_with_regular_scheduling(mocker, db):
    """
    Test schedule_sync with schedule_enabled=True and is_real_time_export_enabled=False
    """
    workspace_id = 1

    # Mock datetime.now() to have predictable results
    mock_now = mocker.patch('apps.workspaces.tasks.datetime')
    mock_now.now.return_value = datetime(2023, 6, 15, 10, 30, 0)

    # Mock schedule_email_notification
    mock_email_notification = mocker.patch('apps.workspaces.tasks.schedule_email_notification')

    result = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=True,
        hours=24,
        email_added=['new_user@fyle.in'],
        emails_selected=['user1@fyle.in', 'user2@fyle.in'],
        is_real_time_export_enabled=False
    )

    # Verify WorkspaceSchedule was created/updated correctly
    assert result.workspace_id == workspace_id
    assert result.enabled == True
    assert result.is_real_time_export_enabled == False
    assert result.interval_hours == 24
    assert result.emails_selected == ['user1@fyle.in', 'user2@fyle.in']
    assert result.start_datetime == datetime(2023, 6, 15, 10, 30, 0)
    assert ['new_user@fyle.in'] in result.additional_email_options

    # Verify Schedule was created
    assert result.schedule is not None
    assert result.schedule.func == 'apps.workspaces.tasks.run_sync_schedule'
    assert result.schedule.args == '1'
    assert result.schedule.minutes == 24 * 60

    # Verify email notification was scheduled
    mock_email_notification.assert_called_once_with(
        workspace_id=workspace_id,
        schedule_enabled=True,
        hours=24
    )


def test_schedule_sync_enabled_with_real_time_export(mocker, db):
    """
    Test schedule_sync with schedule_enabled=True and is_real_time_export_enabled=True
    """
    workspace_id = 1

    # Create an existing WorkspaceSchedule with a Schedule
    from django_q.models import Schedule
    existing_schedule = Schedule.objects.create(
        func='apps.workspaces.tasks.run_sync_schedule',
        args='1',
        schedule_type=Schedule.MINUTES,
        minutes=60
    )

    WorkspaceSchedule.objects.create(
        workspace_id=workspace_id,
        enabled=False,
        schedule=existing_schedule
    )

    # Mock datetime.now()
    mock_now = mocker.patch('apps.workspaces.tasks.datetime')
    mock_now.now.return_value = datetime(2023, 6, 15, 10, 30, 0)

    # Mock schedule_email_notification
    mock_email_notification = mocker.patch('apps.workspaces.tasks.schedule_email_notification')

    result = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=True,
        hours=12,
        email_added=['realtime_user@fyle.in'],
        emails_selected=['admin@fyle.in'],
        is_real_time_export_enabled=True
    )

    # Verify WorkspaceSchedule was updated correctly
    assert result.workspace_id == workspace_id
    assert result.enabled == True
    assert result.is_real_time_export_enabled == True
    assert result.interval_hours == 12
    assert result.emails_selected == ['admin@fyle.in']
    assert result.start_datetime == datetime(2023, 6, 15, 10, 30, 0)
    assert ['realtime_user@fyle.in'] in result.additional_email_options

    # Verify the existing schedule was deleted and no new schedule created
    assert result.schedule is None
    assert not Schedule.objects.filter(id=existing_schedule.id).exists()

    # Verify email notification was scheduled
    mock_email_notification.assert_called_once_with(
        workspace_id=workspace_id,
        schedule_enabled=True,
        hours=12
    )


def test_schedule_sync_disabled_with_existing_schedule(mocker, db):
    """
    Test schedule_sync with schedule_enabled=False and existing schedule
    """
    workspace_id = 1

    # Create an existing WorkspaceSchedule with a Schedule
    from django_q.models import Schedule
    existing_schedule = Schedule.objects.create(
        func='apps.workspaces.tasks.run_sync_schedule',
        args='1',
        schedule_type=Schedule.MINUTES,
        minutes=120
    )

    WorkspaceSchedule.objects.create(
        workspace_id=workspace_id,
        enabled=True,
        schedule=existing_schedule,
        additional_email_options=[{'email': 'old@fyle.in', 'name': 'Old User'}]
    )

    # Mock schedule_email_notification
    mock_email_notification = mocker.patch('apps.workspaces.tasks.schedule_email_notification')

    result = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=False,
        hours=6,
        email_added=None,
        emails_selected=['user@fyle.in'],
        is_real_time_export_enabled=False
    )

    # Verify WorkspaceSchedule was updated correctly
    assert result.workspace_id == workspace_id
    assert result.enabled == False
    assert result.is_real_time_export_enabled == False

    # Verify the existing schedule was deleted
    assert result.schedule is None
    assert not Schedule.objects.filter(id=existing_schedule.id).exists()

    # Verify email notification was scheduled (even when disabled)
    mock_email_notification.assert_called_once_with(
        workspace_id=workspace_id,
        schedule_enabled=False,
        hours=6
    )


def test_schedule_sync_disabled_without_existing_schedule(mocker, db):
    """
    Test schedule_sync with schedule_enabled=False and no existing schedule
    """
    workspace_id = 1

    # Mock schedule_email_notification
    mock_email_notification = mocker.patch('apps.workspaces.tasks.schedule_email_notification')

    result = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=False,
        hours=0,
        email_added=None,
        emails_selected=[],
        is_real_time_export_enabled=False
    )

    # Verify WorkspaceSchedule was created correctly
    assert result.workspace_id == workspace_id
    assert result.enabled == False
    assert result.is_real_time_export_enabled == False
    assert result.schedule is None

    # Verify email notification was scheduled
    mock_email_notification.assert_called_once_with(
        workspace_id=workspace_id,
        schedule_enabled=False,
        hours=0
    )


def test_schedule_sync_email_added_functionality(mocker, db):
    """
    Test schedule_sync email_added list functionality
    """
    workspace_id = 1

    # Create an existing WorkspaceSchedule with some email options
    WorkspaceSchedule.objects.create(
        workspace_id=workspace_id,
        enabled=False,
        additional_email_options=[
            {'email': 'existing1@fyle.in', 'name': 'Existing User 1'},
            {'email': 'existing2@fyle.in', 'name': 'Existing User 2'}
        ]
    )

    # Mock schedule_email_notification and datetime
    mocker.patch('apps.workspaces.tasks.schedule_email_notification')
    mock_now = mocker.patch('apps.workspaces.tasks.datetime')
    mock_now.now.return_value = datetime(2023, 6, 15, 14, 0, 0)

    result = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=True,
        hours=8,
        email_added=['new1@fyle.in', 'new2@fyle.in'],
        emails_selected=['admin1@fyle.in', 'admin2@fyle.in'],
        is_real_time_export_enabled=False
    )

    # Verify email_added was appended to additional_email_options
    expected_email_options = [
        {'email': 'existing1@fyle.in', 'name': 'Existing User 1'},
        {'email': 'existing2@fyle.in', 'name': 'Existing User 2'},
        ['new1@fyle.in', 'new2@fyle.in']
    ]
    assert result.additional_email_options == expected_email_options

    # Test with empty email_added - it should NOT be appended since code checks "if email_added:"
    result2 = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=True,
        hours=8,
        email_added=[],
        emails_selected=['admin@fyle.in'],
        is_real_time_export_enabled=False
    )

    # Verify empty email_added was NOT appended since empty lists are falsy
    expected_email_options_2 = [
        {'email': 'existing1@fyle.in', 'name': 'Existing User 1'},
        {'email': 'existing2@fyle.in', 'name': 'Existing User 2'},
        ['new1@fyle.in', 'new2@fyle.in']
    ]
    assert result2.additional_email_options == expected_email_options_2


def test_schedule_sync_no_email_added(mocker, db):
    """
    Test schedule_sync when email_added is None
    """
    workspace_id = 1

    # Mock schedule_email_notification and datetime
    mocker.patch('apps.workspaces.tasks.schedule_email_notification')
    mock_now = mocker.patch('apps.workspaces.tasks.datetime')
    mock_now.now.return_value = datetime(2023, 6, 15, 16, 45, 0)

    result = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=True,
        hours=6,
        email_added=None,
        emails_selected=['user@fyle.in'],
        is_real_time_export_enabled=False
    )

    # Verify additional_email_options remains as default list
    assert result.additional_email_options == []

    # Verify other fields are set correctly
    assert result.workspace_id == workspace_id
    assert result.enabled == True
    assert result.interval_hours == 6
    assert result.emails_selected == ['user@fyle.in']


def test_schedule_sync_update_existing_workspace_schedule(mocker, db):
    """
    Test schedule_sync updating an existing WorkspaceSchedule
    """
    workspace_id = 1

    # Create an existing WorkspaceSchedule
    existing_ws_schedule = WorkspaceSchedule.objects.create(
        workspace_id=workspace_id,
        enabled=True,
        is_real_time_export_enabled=True,
        interval_hours=12,
        emails_selected=['old@fyle.in'],
        additional_email_options=[{'old': 'data'}]
    )

    original_id = existing_ws_schedule.id

    # Mock schedule_email_notification and datetime
    mocker.patch('apps.workspaces.tasks.schedule_email_notification')
    mock_now = mocker.patch('apps.workspaces.tasks.datetime')
    mock_now.now.return_value = datetime(2023, 6, 15, 18, 0, 0)

    result = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=False,
        hours=24,
        email_added=['updated@fyle.in'],
        emails_selected=['new@fyle.in'],
        is_real_time_export_enabled=False
    )

    # Verify the same WorkspaceSchedule object was updated (not created new)
    assert result.id == original_id
    assert WorkspaceSchedule.objects.filter(workspace_id=workspace_id).count() == 1

    # Verify fields were updated correctly
    assert result.enabled == False
    assert result.is_real_time_export_enabled == False
    assert result.schedule is None  # Since schedule_enabled=False

    # Note: When schedule_enabled=False, the schedule fields like interval_hours
    # and emails_selected are not updated according to the current logic


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

    assert ws_schedule is not None
    assert ws_schedule.enabled == True
    assert ws_schedule.emails_selected == ['user5@fyleforgotham.in']

    if ws_schedule.additional_email_options is None:
        ws_schedule.additional_email_options = []
        ws_schedule.save()

    TaskLog.objects.filter(workspace_id=workspace_id, status='FAILED').delete()

    for i in range(3):
        TaskLog.objects.create(
            workspace_id=workspace_id,
            type='CREATING_BILLS',
            status='FAILED'
        )

    failed_task_logs = TaskLog.objects.filter(
        workspace_id=workspace_id,
        status='FAILED',
        type='CREATING_BILLS'
    )
    assert failed_task_logs.count() == 3

    mocker.patch('apps.workspaces.tasks.send_email',
                 return_value=None)
    mocker.patch('apps.workspaces.tasks.render_to_string',
                 return_value='<html>Test Email</html>')

    trigger_email_notification(workspace_id=workspace_id)

    updated_ws_schedule = WorkspaceSchedule.objects.filter(
        workspace_id=workspace_id, id=ws_schedule.id
    ).first()

    assert updated_ws_schedule.error_count == 3

    attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id, value='user5@fyleforgotham.in').first()
    attribute.delete()

    ws_schedule.enabled = True
    ws_schedule.additional_email_options = [{'email': 'user5@fyleforgotham.in', 'name': 'Ashwin'}]
    ws_schedule.save()

    trigger_email_notification(workspace_id=workspace_id)
    updated_ws_schedule = WorkspaceSchedule.objects.filter(
        workspace_id=workspace_id, id=ws_schedule.id
    ).first()

    assert updated_ws_schedule.error_count == 3

    SageIntacctCredential.objects.filter(workspace_id=workspace_id).delete()

    trigger_email_notification(workspace_id=workspace_id)


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


def test_run_sync_schedule_with_rabbitmq_export(mocker, db):
    """
    Test run_sync_schedule with export_via_rabbitmq enabled (covers lines 162-163, 173)
    """
    workspace_id = 1

    # Mock the expenses API call
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses']
    )

    # Mock the RabbitMQ publish function to track if it's called
    mock_publish_to_rabbitmq = mocker.patch('apps.workspaces.tasks.publish_to_rabbitmq')

    # Enable export_via_rabbitmq in FeatureConfig
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.export_via_rabbitmq = True
    feature_config.save()

    # Create some expense groups to export
    workspace = Workspace.objects.get(id=workspace_id)
    ExpenseGroup.objects.create(
        workspace=workspace,
        fund_source='PERSONAL',
        exported_at=None
    )
    ExpenseGroup.objects.create(
        workspace=workspace,
        fund_source='CCC',
        exported_at=None
    )

    # Call run_sync_schedule - this should trigger the RabbitMQ path
    run_sync_schedule(workspace_id)

    # Verify that publish_to_rabbitmq was called (covers line 173)
    mock_publish_to_rabbitmq.assert_called_once()

    # Verify the payload structure
    call_args = mock_publish_to_rabbitmq.call_args
    payload_arg = call_args[1]['payload']
    routing_key_arg = call_args[1]['routing_key']

    assert payload_arg['workspace_id'] == workspace_id
    assert payload_arg['action'] == 'EXPORT.P1.BACKGROUND_SCHEDULE_EXPORT'
    assert payload_arg['data']['workspace_id'] == workspace_id
    assert payload_arg['data']['triggered_by'] == 'BACKGROUND_SCHEDULE'
    assert payload_arg['data']['run_in_rabbitmq_worker'] == True
    assert routing_key_arg == 'EXPORT.P1.*'
    assert isinstance(payload_arg['data']['expense_group_ids'], list)

    # Reset the feature config
    feature_config.export_via_rabbitmq = False
    feature_config.save()


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


def test_create_admin_subscriptions_invalid_token(db, mocker):
    """
    Test create admin subscriptions with invalid token
    """
    mocker.patch(
        'fyle_integrations_platform_connector.PlatformConnector.__init__',
        side_effect=InvalidTokenError('Invalid Token')
    )
    create_admin_subscriptions(3)

    mocker.patch(
        'fyle_integrations_platform_connector.PlatformConnector.__init__',
        side_effect=Exception('General error')
    )
    create_admin_subscriptions(3)


def test_update_workspace_name_invalid_token(db, mocker):
    """
    Test update workspace name with invalid token
    """
    mocker.patch(
        'apps.workspaces.tasks.get_fyle_admin',
        side_effect=InvalidTokenError('Invalid Token')
    )
    update_workspace_name(1, 'Bearer access_token')

    mocker.patch(
        'apps.workspaces.tasks.get_fyle_admin',
        side_effect=Exception('General error')
    )
    update_workspace_name(1, 'Bearer access_token')


def test_sync_org_settings(db, mocker):
    """
    Test sync org settings
    """
    workspace_id = 1
    workspace = Workspace.objects.get(id=workspace_id)
    workspace.org_settings = {}
    workspace.save()

    mock_platform = mocker.patch('apps.workspaces.tasks.PlatformConnector')
    mock_platform.return_value.org_settings.get.return_value = {
        'regional_settings': {
            'locale': {
                'date_format': 'DD/MM/YYYY',
                'timezone': 'Asia/Kolkata'
            }
        }
    }

    sync_org_settings(workspace_id=workspace_id)

    workspace.refresh_from_db()
    assert workspace.org_settings == {
        'regional_settings': {
            'locale': {
                'date_format': 'DD/MM/YYYY',
                'timezone': 'Asia/Kolkata'
            }
        }
    }
