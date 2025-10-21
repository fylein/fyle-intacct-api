from fyle_accounting_library.fyle_platform.enums import ExpenseStateEnum

from apps.fyle.models import ExpenseGroup, ExpenseGroupSettings
from apps.tasks.models import Error, TaskLog
from apps.workspaces.apis.export_settings.triggers import ExportSettingsTrigger
from apps.workspaces.models import Configuration


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

    # Verify no async tasks were called since states didn't change
    mock_publish.assert_not_called()
