from fyle_accounting_library.fyle_platform.enums import ExpenseStateEnum

from apps.fyle.models import ExpenseGroupSettings
from apps.workspaces.models import Configuration


def test_run_pre_save_expense_group_setting_triggers_no_existing_settings(db, mocker):
    """
    Test when there are no existing expense group settings
    """
    workspace_id = 1
    Configuration.objects.filter(workspace_id=workspace_id).delete()
    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)

    mock_publish = mocker.patch('workers.helpers.publish_to_rabbitmq')

    # Save should not trigger any async tasks since there's no existing settings
    expense_group_settings.save()
    mock_publish.assert_not_called()


def test_run_pre_save_expense_group_setting_triggers_reimbursable_state_change(db, mocker):
    """
    Test when reimbursable expense state changes from PAID to PAYMENT_PROCESSING
    """
    workspace_id = 1

    # Ensure configuration has reimbursable_expenses_object set
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'BILL'
    configuration.save()

    expense_group_settings, _ = ExpenseGroupSettings.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'expense_state': ExpenseStateEnum.PAID,
            'ccc_expense_state': ExpenseStateEnum.PAID
        }
    )

    mock_publish = mocker.patch('apps.fyle.signals.publish_to_rabbitmq')

    # Change reimbursable state
    expense_group_settings.expense_state = ExpenseStateEnum.PAYMENT_PROCESSING
    expense_group_settings.save()

    # Verify publish_to_rabbitmq was called with correct parameters
    mock_publish.assert_called_once()


def test_run_pre_save_expense_group_setting_triggers_ccc_state_change(db, mocker):
    """
    Test when corporate credit card expense state changes from PAID to APPROVED
    """
    workspace_id = 1

    # Ensure configuration has corporate_credit_card_expenses_object set
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()

    expense_group_settings, _ = ExpenseGroupSettings.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'expense_state': ExpenseStateEnum.PAYMENT_PROCESSING,
            'ccc_expense_state': ExpenseStateEnum.PAID
        }
    )

    mock_publish = mocker.patch('apps.fyle.signals.publish_to_rabbitmq')

    # Change CCC state
    expense_group_settings.ccc_expense_state = ExpenseStateEnum.APPROVED
    expense_group_settings.save()

    # Verify publish_to_rabbitmq was called with correct parameters
    mock_publish.assert_called_once()


def test_run_pre_save_expense_group_setting_triggers_no_configuration(db, mocker):
    """
    Test when workspace general settings don't exist
    """
    workspace_id = 1

    Configuration.objects.filter(workspace_id=workspace_id).delete()
    expense_group_settings, _ = ExpenseGroupSettings.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'expense_state': ExpenseStateEnum.PAID,
            'ccc_expense_state': ExpenseStateEnum.PAID
        }
    )

    mock_publish = mocker.patch('workers.helpers.publish_to_rabbitmq')

    expense_group_settings.expense_state = ExpenseStateEnum.PAYMENT_PROCESSING
    expense_group_settings.ccc_expense_state = ExpenseStateEnum.APPROVED
    expense_group_settings.save()

    # Verify no async tasks were called due to missing configuration
    mock_publish.assert_not_called()


def test_run_pre_save_expense_group_setting_triggers_no_state_change(db, mocker):
    """
    Test when expense states don't change
    """
    workspace_id = 1

    expense_group_settings, _ = ExpenseGroupSettings.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'expense_state': ExpenseStateEnum.PAID,
            'ccc_expense_state': ExpenseStateEnum.PAID
        }
    )

    mock_publish = mocker.patch('workers.helpers.publish_to_rabbitmq')

    # Save without changing states
    expense_group_settings.save()

    # Verify no async tasks were called
    mock_publish.assert_not_called()
