from fyle_accounting_library.fyle_platform.enums import ExpenseStateEnum
from fyle_accounting_mappings.models import MappingSetting

from apps.fyle.models import ExpenseGroup, ExpenseGroupSettings
from apps.tasks.models import Error, TaskLog
from apps.workspaces.apis.export_settings.triggers import ExportSettingsTrigger
from apps.workspaces.models import Configuration, FeatureConfig
from workers.helpers import WorkerActionEnum


def test_post_save_configuration_trigger(mocker, db):
    """
    Test post_save_configuration trigger
    """
    workspace_id = 1
    configuration, _ = Configuration.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'reimbursable_expenses_object': None,
            'corporate_credit_card_expenses_object': 'JOURNAL ENTRY'
        }
    )

    expense_grp_ccc = ExpenseGroup.objects.filter(
        workspace_id=workspace_id,
        exported_at__isnull=True
    ).exclude(fund_source__in=['PERSONAL']).values_list('id', flat=True)

    export_trigger = ExportSettingsTrigger(configuration=configuration, workspace_id=workspace_id, old_configurations=None)
    export_trigger.post_save_configurations(False)

    after_delete_count = TaskLog.objects.filter(
        workspace_id=workspace_id,
        status__in=['FAILED', 'FATAL']
    ).count()

    after_errors_count = Error.objects.filter(
        workspace_id=workspace_id,
        expense_group_id__in=expense_grp_ccc
    ).exclude(type__contains='_MAPPING').count()

    assert after_errors_count == 0
    assert after_delete_count >= 2


def test_post_save_configuration_trigger_2(mocker, db):
    """
    Test post_save_configuration trigger
    """
    workspace_id = 1
    configuration, _ = Configuration.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'reimbursable_expenses_object': 'JOURNAL ENTRY',
            'corporate_credit_card_expenses_object': None
        }
    )

    expense_grp_personal = ExpenseGroup.objects.filter(
        workspace_id=workspace_id,
        exported_at__isnull=True
    ).exclude(fund_source__in=['CCC']).values_list('id', flat=True)

    export_trigger = ExportSettingsTrigger(configuration=configuration, workspace_id=workspace_id, old_configurations=None)
    export_trigger.post_save_configurations(False)

    after_delete_count = TaskLog.objects.filter(
        workspace_id=workspace_id,
        status__in=['FAILED', 'FATAL']
    ).count()

    after_errors_count = Error.objects.filter(
        workspace_id=workspace_id,
        expense_group_id__in=expense_grp_personal
    ).exclude(type__contains='_MAPPING').count()

    assert after_errors_count == 0
    assert after_delete_count >= 1


def test_run_pre_save_expense_group_setting_triggers_no_existing_settings(db, mocker):
    """
    Test when there are no existing expense group settings
    """
    workspace_id = 1
    Configuration.objects.filter(workspace_id=workspace_id).delete()
    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)

    configuration_payload = Configuration(reimbursable_expenses_object='JOURNAL ENTRY', corporate_credit_card_expenses_object='JOURNAL ENTRY')

    mock_publish = mocker.patch('apps.workspaces.apis.export_settings.triggers.publish_to_rabbitmq')

    export_trigger = ExportSettingsTrigger(configuration=configuration_payload, workspace_id=workspace_id, old_configurations={})
    export_trigger.post_save_expense_group_settings(expense_group_settings)
    # Save should not trigger any async tasks since there's no existing settings
    mock_publish.assert_not_called()


def test_run_pre_save_expense_group_setting_triggers_reimbursable_state_change(db, mocker):
    """
    Test when reimbursable expense state changes from PAID to PAYMENT_PROCESSING
    """
    workspace_id = 1

    # Get the existing settings and set it to PAID (old state)
    old_expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    old_expense_group_settings.expense_state = ExpenseStateEnum.PAID
    old_expense_group_settings.save()

    # Create new instance with changed state
    new_expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    new_expense_group_settings.expense_state = ExpenseStateEnum.PAYMENT_PROCESSING

    configuration_payload = Configuration(reimbursable_expenses_object='JOURNAL ENTRY', corporate_credit_card_expenses_object='JOURNAL ENTRY')

    mock_publish = mocker.patch('apps.workspaces.apis.export_settings.triggers.publish_to_rabbitmq')

    export_trigger = ExportSettingsTrigger(
        configuration=configuration_payload,
        workspace_id=workspace_id,
        old_configurations={'expense_group_settings': old_expense_group_settings}
    )
    export_trigger.post_save_expense_group_settings(new_expense_group_settings)

    assert mock_publish.call_count == 1


def test_run_pre_save_expense_group_setting_triggers_ccc_state_change(db, mocker):
    """
    Test when corporate credit card expense state changes from PAID to APPROVED
    """
    workspace_id = 1

    # Get the existing settings and set it to PAID (old state)
    old_expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    old_expense_group_settings.ccc_expense_state = ExpenseStateEnum.PAID
    old_expense_group_settings.save()

    # Create new instance with changed state
    new_expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    new_expense_group_settings.ccc_expense_state = ExpenseStateEnum.APPROVED

    configuration_payload = Configuration(reimbursable_expenses_object='JOURNAL ENTRY', corporate_credit_card_expenses_object='JOURNAL ENTRY')

    mock_publish = mocker.patch('apps.workspaces.apis.export_settings.triggers.publish_to_rabbitmq')

    export_trigger = ExportSettingsTrigger(
        configuration=configuration_payload,
        workspace_id=workspace_id,
        old_configurations={'expense_group_settings': old_expense_group_settings}
    )
    export_trigger.post_save_expense_group_settings(new_expense_group_settings)

    assert mock_publish.call_count == 1


def test_run_pre_save_expense_group_setting_triggers_no_configuration(db, mocker):
    """
    Test when workspace general settings don't exist
    """
    workspace_id = 1

    Configuration.objects.filter(workspace_id=workspace_id).delete()
    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)

    configuration_payload = Configuration(reimbursable_expenses_object='JOURNAL ENTRY', corporate_credit_card_expenses_object='JOURNAL ENTRY')

    mock_publish = mocker.patch('apps.workspaces.apis.export_settings.triggers.publish_to_rabbitmq')

    export_trigger = ExportSettingsTrigger(configuration=configuration_payload, workspace_id=workspace_id, old_configurations={})
    export_trigger.post_save_expense_group_settings(expense_group_settings)

    # Verify no async tasks were called due to missing configuration
    mock_publish.assert_not_called()


def test_run_pre_save_expense_group_setting_triggers_no_state_change(db, mocker):
    """
    Test when expense states don't change
    """
    workspace_id = 1

    # Get settings with same state for old and new
    old_expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    old_expense_group_settings.expense_state = ExpenseStateEnum.PAID
    old_expense_group_settings.ccc_expense_state = ExpenseStateEnum.PAID
    old_expense_group_settings.save()

    # New instance with same states (no change)
    new_expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    new_expense_group_settings.expense_state = ExpenseStateEnum.PAID
    new_expense_group_settings.ccc_expense_state = ExpenseStateEnum.PAID

    configuration_payload = Configuration(reimbursable_expenses_object='JOURNAL ENTRY', corporate_credit_card_expenses_object='JOURNAL ENTRY')

    mock_publish = mocker.patch('apps.workspaces.apis.export_settings.triggers.publish_to_rabbitmq')

    export_trigger = ExportSettingsTrigger(
        configuration=configuration_payload,
        workspace_id=workspace_id,
        old_configurations={'expense_group_settings': old_expense_group_settings}
    )
    export_trigger.post_save_expense_group_settings(new_expense_group_settings)

    mock_publish.assert_not_called()


def test_post_save_configuration_triggers_billable_sync_on_export_type_change(db, mocker):
    """
    Test that billable sync is triggered when export type changes
    """
    workspace_id = 1

    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = True
    feature_config.save()

    MappingSetting.objects.update_or_create(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='PROJECT',
        defaults={'import_to_fyle': True, 'is_custom': False}
    )

    configuration, _ = Configuration.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'reimbursable_expenses_object': 'BILL',
            'corporate_credit_card_expenses_object': None
        }
    )

    old_configurations = {
        'reimbursable_expenses_object': 'EXPENSE_REPORT',
        'corporate_credit_card_expenses_object': None
    }

    mock_publish = mocker.patch('apps.workspaces.apis.export_settings.triggers.publish_to_rabbitmq')

    export_trigger = ExportSettingsTrigger(
        configuration=configuration,
        workspace_id=workspace_id,
        old_configurations=old_configurations
    )
    export_trigger.post_save_configurations(False)

    billable_sync_calls = [
        call for call in mock_publish.call_args_list
        if call.kwargs.get('payload', {}).get('action') == WorkerActionEnum.SYNC_PROJECT_BILLABLE_TO_FYLE.value
    ]

    assert len(billable_sync_calls) == 1
    payload = billable_sync_calls[0].kwargs['payload']
    assert payload['data']['workspace_id'] == workspace_id
    assert payload['data']['billable_field'] == 'default_bill_billable'


def test_post_save_configuration_no_billable_sync_when_export_type_unchanged(db, mocker):
    """
    Test that billable sync is NOT triggered when export type doesn't change
    """
    workspace_id = 1

    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = True
    feature_config.save()

    MappingSetting.objects.update_or_create(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='PROJECT',
        defaults={'import_to_fyle': True, 'is_custom': False}
    )

    configuration, _ = Configuration.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'reimbursable_expenses_object': 'BILL',
            'corporate_credit_card_expenses_object': None
        }
    )

    old_configurations = {
        'reimbursable_expenses_object': 'BILL',
        'corporate_credit_card_expenses_object': None
    }

    mock_publish = mocker.patch('apps.workspaces.apis.export_settings.triggers.publish_to_rabbitmq')

    export_trigger = ExportSettingsTrigger(
        configuration=configuration,
        workspace_id=workspace_id,
        old_configurations=old_configurations
    )
    export_trigger.post_save_configurations(False)

    billable_sync_calls = [
        call for call in mock_publish.call_args_list
        if call.kwargs.get('payload', {}).get('action') == WorkerActionEnum.SYNC_PROJECT_BILLABLE_TO_FYLE.value
    ]

    assert len(billable_sync_calls) == 0


def test_post_save_configuration_no_billable_sync_when_feature_disabled(db, mocker):
    """
    Test that billable sync is NOT triggered when feature is disabled
    """
    workspace_id = 1

    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = False
    feature_config.save()

    configuration, _ = Configuration.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'reimbursable_expenses_object': 'BILL',
            'corporate_credit_card_expenses_object': None
        }
    )

    old_configurations = {
        'reimbursable_expenses_object': 'EXPENSE_REPORT',
        'corporate_credit_card_expenses_object': None
    }

    mock_publish = mocker.patch('apps.workspaces.apis.export_settings.triggers.publish_to_rabbitmq')

    export_trigger = ExportSettingsTrigger(
        configuration=configuration,
        workspace_id=workspace_id,
        old_configurations=old_configurations
    )
    export_trigger.post_save_configurations(False)

    billable_sync_calls = [
        call for call in mock_publish.call_args_list
        if call.kwargs.get('payload', {}).get('action') == WorkerActionEnum.SYNC_PROJECT_BILLABLE_TO_FYLE.value
    ]

    assert len(billable_sync_calls) == 0


def test_post_save_configuration_no_billable_sync_without_project_mapping(db, mocker):
    """
    Test that billable sync is NOT triggered when PROJECT mapping setting doesn't exist
    """
    workspace_id = 1

    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = True
    feature_config.save()

    MappingSetting.objects.filter(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='PROJECT'
    ).delete()

    configuration, _ = Configuration.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'reimbursable_expenses_object': 'BILL',
            'corporate_credit_card_expenses_object': None
        }
    )

    old_configurations = {
        'reimbursable_expenses_object': 'EXPENSE_REPORT',
        'corporate_credit_card_expenses_object': None
    }

    mock_publish = mocker.patch('apps.workspaces.apis.export_settings.triggers.publish_to_rabbitmq')

    export_trigger = ExportSettingsTrigger(
        configuration=configuration,
        workspace_id=workspace_id,
        old_configurations=old_configurations
    )
    export_trigger.post_save_configurations(False)

    billable_sync_calls = [
        call for call in mock_publish.call_args_list
        if call.kwargs.get('payload', {}).get('action') == WorkerActionEnum.SYNC_PROJECT_BILLABLE_TO_FYLE.value
    ]

    assert len(billable_sync_calls) == 0


def test_post_save_configuration_triggers_billable_sync_ccc_change(db, mocker):
    """
    Test that billable sync is triggered when CCC export type changes
    """
    workspace_id = 1

    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = True
    feature_config.save()

    MappingSetting.objects.update_or_create(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='PROJECT',
        defaults={'import_to_fyle': True, 'is_custom': False}
    )

    configuration, _ = Configuration.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'reimbursable_expenses_object': None,
            'corporate_credit_card_expenses_object': 'EXPENSE_REPORT'
        }
    )

    old_configurations = {
        'reimbursable_expenses_object': None,
        'corporate_credit_card_expenses_object': 'JOURNAL_ENTRY'
    }

    mock_publish = mocker.patch('apps.workspaces.apis.export_settings.triggers.publish_to_rabbitmq')

    export_trigger = ExportSettingsTrigger(
        configuration=configuration,
        workspace_id=workspace_id,
        old_configurations=old_configurations
    )
    export_trigger.post_save_configurations(False)

    billable_sync_calls = [
        call for call in mock_publish.call_args_list
        if call.kwargs.get('payload', {}).get('action') == WorkerActionEnum.SYNC_PROJECT_BILLABLE_TO_FYLE.value
    ]

    assert len(billable_sync_calls) == 1
    payload = billable_sync_calls[0].kwargs['payload']
    assert payload['data']['workspace_id'] == workspace_id
    assert payload['data']['billable_field'] == 'default_expense_report_billable'
