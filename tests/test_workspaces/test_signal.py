from apps.workspaces.models import Configuration


def test_run_post_configration_triggers(db):
    """
    Test to check if the post_save signal is triggered when a new configuration is created
    """
    workspace_id = 1
    general_settings = Configuration.objects.get(workspace_id=workspace_id)
    general_settings.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    general_settings.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    general_settings.save()

    general_settings = Configuration.objects.get(workspace_id=workspace_id)
    assert general_settings.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION'
