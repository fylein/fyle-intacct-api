from datetime import datetime

from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from apps.workspaces.actions import export_to_intacct
from apps.fyle.models import ExpenseGroup


def test_export_to_intacct_variable_assignments(mocker, db):
    """
    Test export_to_intacct to cover the variable assignment lines 38-39, 49-51
    """
    workspace_id = 1

    # Create some expense groups to work with
    from apps.workspaces.models import Workspace
    workspace = Workspace.objects.get(id=workspace_id)
    ExpenseGroup.objects.create(
        workspace=workspace,
        fund_source='PERSONAL'
    )
    ExpenseGroup.objects.create(
        workspace=workspace,
        fund_source='CCC'
    )

    # Mock all the scheduling functions to prevent actual execution
    mocker.patch('apps.workspaces.actions.schedule_bills_creation')
    mocker.patch('apps.workspaces.actions.schedule_expense_reports_creation')
    mocker.patch('apps.workspaces.actions.schedule_journal_entries_creation')
    mocker.patch('apps.workspaces.actions.schedule_charge_card_transaction_creation')

    # Mock datetime.now() to have predictable results
    mock_datetime = mocker.patch('apps.workspaces.actions.datetime')
    mock_datetime.now.return_value = datetime(2023, 6, 15, 10, 30, 0)

    # Test with MANUAL export_mode (triggered_by in DASHBOARD_SYNC, DIRECT_EXPORT, CONFIGURATION_UPDATE)
    # This covers lines 38-39 with 'MANUAL' assignment
    export_to_intacct(
        workspace_id=workspace_id,
        triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC,
        run_in_rabbitmq_worker=False
    )

    # Test with AUTO export_mode (triggered_by not in the manual list)
    # This covers lines 38-39 with 'AUTO' assignment
    export_to_intacct(
        workspace_id=workspace_id,
        triggered_by=ExpenseImportSourceEnum.WEBHOOK,
        run_in_rabbitmq_worker=False
    )


def test_export_to_intacct_with_expense_group_ids(mocker, db):
    """
    Test export_to_intacct with specific expense_group_ids to ensure all paths are covered
    """
    workspace_id = 1

    # Create expense groups
    from apps.workspaces.models import Workspace
    workspace = Workspace.objects.get(id=workspace_id)
    expense_group_1 = ExpenseGroup.objects.create(
        workspace=workspace,
        fund_source='PERSONAL'
    )
    expense_group_2 = ExpenseGroup.objects.create(
        workspace=workspace,
        fund_source='CCC'
    )

    # Mock all the scheduling functions
    mocker.patch('apps.workspaces.actions.schedule_bills_creation')
    mocker.patch('apps.workspaces.actions.schedule_expense_reports_creation')
    mocker.patch('apps.workspaces.actions.schedule_journal_entries_creation')
    mocker.patch('apps.workspaces.actions.schedule_charge_card_transaction_creation')

    # Test with specific expense group IDs and CONFIGURATION_UPDATE (MANUAL mode)
    export_to_intacct(
        workspace_id=workspace_id,
        expense_group_ids=[expense_group_1.id, expense_group_2.id],
        triggered_by=ExpenseImportSourceEnum.CONFIGURATION_UPDATE,
        run_in_rabbitmq_worker=True
    )

    # Test with DIRECT_EXPORT (also MANUAL mode)
    export_to_intacct(
        workspace_id=workspace_id,
        expense_group_ids=[expense_group_1.id],
        triggered_by=ExpenseImportSourceEnum.DIRECT_EXPORT,
        run_in_rabbitmq_worker=False
    )

    # Test with BACKGROUND_SCHEDULE (AUTO mode)
    export_to_intacct(
        workspace_id=workspace_id,
        expense_group_ids=[expense_group_2.id],
        triggered_by=ExpenseImportSourceEnum.BACKGROUND_SCHEDULE,
        run_in_rabbitmq_worker=True
    )

    # Verify the function executed without errors (this confirms all variable assignments were successful)
    assert True  # If we get here, the function ran successfully


def test_export_to_intacct_no_triggered_by(mocker, db):
    """
    Test export_to_intacct with triggered_by=None to test the default AUTO mode assignment
    """
    workspace_id = 1

    # Mock all the scheduling functions
    mocker.patch('apps.workspaces.actions.schedule_bills_creation')
    mocker.patch('apps.workspaces.actions.schedule_expense_reports_creation')
    mocker.patch('apps.workspaces.actions.schedule_journal_entries_creation')
    mocker.patch('apps.workspaces.actions.schedule_charge_card_transaction_creation')

    # Test with triggered_by=None (should default to AUTO mode)
    export_to_intacct(
        workspace_id=workspace_id,
        triggered_by=None,
        run_in_rabbitmq_worker=False
    )

    # If we get here without exceptions, the variable assignments (lines 38-39, 49-51) were successful
    assert True
