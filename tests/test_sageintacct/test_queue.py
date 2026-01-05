import pytest
from unittest import mock
from apps.sage_intacct.queue import (
    trigger_sync_payments,
    schedule_journal_entries_creation,
    schedule_expense_reports_creation,
    schedule_bills_creation,
    schedule_charge_card_transaction_creation,
)
from apps.tasks.models import TaskLog
from apps.fyle.models import ExpenseGroup
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from workers.helpers import WorkerActionEnum


@pytest.mark.django_db
@mock.patch('apps.sage_intacct.queue.publish_to_rabbitmq')
@mock.patch('apps.workspaces.models.Configuration.objects.get')
@mock.patch('apps.mappings.models.GeneralMapping.objects.filter')
def test_trigger_sync_payments(
    mock_general_mapping_filter,
    mock_configuration_get,
    mock_publish_to_rabbitmq
):
    """
    Test trigger_sync_payments function
    """
    workspace_id = 1
    # Mock configuration and general_mappings
    mock_config = mock.Mock()
    mock_config.sync_fyle_to_sage_intacct_payments = True
    mock_config.sync_sage_intacct_to_fyle_payments = True
    mock_config.reimbursable_expenses_object = 'BILL'
    mock_configuration_get.return_value = mock_config

    mock_general_mapping = mock.Mock()
    mock_general_mapping.payment_account_id = 123
    mock_general_mapping_filter.return_value.first.return_value = mock_general_mapping

    # Call function
    trigger_sync_payments(workspace_id)

    # Should publish CREATE_AP_PAYMENT and CHECK_SAGE_INTACCT_OBJECT_STATUS_AND_PROCESS_FYLE_REIMBURSEMENTS
    assert mock_publish_to_rabbitmq.call_count == 2
    payloads = [call[1]['payload'] if 'payload' in call[1] else None for call in mock_publish_to_rabbitmq.call_args_list]
    actions = [p['action'] for p in payloads if p]
    assert WorkerActionEnum.CREATE_AP_PAYMENT.value in actions
    assert WorkerActionEnum.CHECK_SAGE_INTACCT_OBJECT_STATUS_AND_PROCESS_FYLE_REIMBURSEMENTS.value in actions

    # Test with reimbursable_expenses_object = 'EXPENSE_REPORT'
    mock_config.reimbursable_expenses_object = 'EXPENSE_REPORT'
    trigger_sync_payments(workspace_id)
    payloads = [call[1]['payload'] if 'payload' in call[1] else None for call in mock_publish_to_rabbitmq.call_args_list]
    actions = [p['action'] for p in payloads if p]
    assert WorkerActionEnum.CREATE_SAGE_INTACCT_REIMBURSEMENT.value in actions


@pytest.mark.django_db
def test_schedule_journal_entries_creation_skips_exported_to_intacct(mocker):
    """
    Test that schedule_journal_entries_creation skips expense groups with EXPORTED_TO_INTACCT status
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id, fund_source='PERSONAL').first()

    # Get existing task log for expense group and update its status
    task_log = TaskLog.objects.filter(expense_group=expense_group).first()
    if task_log:
        task_log.status = 'EXPORTED_TO_INTACCT'
        task_log.type = 'CREATING_JOURNAL_ENTRIES'
        task_log.save()
    else:
        task_log = TaskLog.objects.create(
            workspace_id=workspace_id,
            expense_group=expense_group,
            type='CREATING_JOURNAL_ENTRIES',
            status='EXPORTED_TO_INTACCT'
        )

    # Try to schedule creation - should skip since status is EXPORTED_TO_INTACCT
    schedule_journal_entries_creation(
        workspace_id,
        [expense_group.id],
        False,
        1,
        triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC,
        run_in_rabbitmq_worker=False
    )

    # Task log status should remain EXPORTED_TO_INTACCT (not changed to ENQUEUED)
    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'


@pytest.mark.django_db
def test_schedule_expense_reports_creation_skips_exported_to_intacct(mocker):
    """
    Test that schedule_expense_reports_creation skips expense groups with EXPORTED_TO_INTACCT status
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id, fund_source='PERSONAL').first()

    # Get existing task log for expense group and update its status
    task_log = TaskLog.objects.filter(expense_group=expense_group).first()
    if task_log:
        task_log.status = 'EXPORTED_TO_INTACCT'
        task_log.type = 'CREATING_EXPENSE_REPORTS'
        task_log.save()
    else:
        task_log = TaskLog.objects.create(
            workspace_id=workspace_id,
            expense_group=expense_group,
            type='CREATING_EXPENSE_REPORTS',
            status='EXPORTED_TO_INTACCT'
        )

    # Try to schedule creation - should skip since status is EXPORTED_TO_INTACCT
    schedule_expense_reports_creation(
        workspace_id,
        [expense_group.id],
        False,
        1,
        triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC,
        run_in_rabbitmq_worker=False
    )

    # Task log status should remain EXPORTED_TO_INTACCT (not changed to ENQUEUED)
    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'


@pytest.mark.django_db
def test_schedule_bills_creation_skips_exported_to_intacct(mocker):
    """
    Test that schedule_bills_creation skips expense groups with EXPORTED_TO_INTACCT status
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id, fund_source='PERSONAL').first()

    # Get existing task log for expense group and update its status
    task_log = TaskLog.objects.filter(expense_group=expense_group).first()
    if task_log:
        task_log.status = 'EXPORTED_TO_INTACCT'
        task_log.type = 'CREATING_BILLS'
        task_log.save()
    else:
        task_log = TaskLog.objects.create(
            workspace_id=workspace_id,
            expense_group=expense_group,
            type='CREATING_BILLS',
            status='EXPORTED_TO_INTACCT'
        )

    # Try to schedule creation - should skip since status is EXPORTED_TO_INTACCT
    schedule_bills_creation(
        workspace_id,
        [expense_group.id],
        False,
        1,
        triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC,
        run_in_rabbitmq_worker=False
    )

    # Task log status should remain EXPORTED_TO_INTACCT (not changed to ENQUEUED)
    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'


@pytest.mark.django_db
def test_schedule_charge_card_transaction_creation_skips_exported_to_intacct(mocker):
    """
    Test that schedule_charge_card_transaction_creation skips expense groups with EXPORTED_TO_INTACCT status
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id, fund_source='CCC').first()

    # Get existing task log for expense group and update its status
    task_log = TaskLog.objects.filter(expense_group=expense_group).first()
    if task_log:
        task_log.status = 'EXPORTED_TO_INTACCT'
        task_log.type = 'CREATING_CHARGE_CARD_TRANSACTIONS'
        task_log.save()
    else:
        task_log = TaskLog.objects.create(
            workspace_id=workspace_id,
            expense_group=expense_group,
            type='CREATING_CHARGE_CARD_TRANSACTIONS',
            status='EXPORTED_TO_INTACCT'
        )

    # Try to schedule creation - should skip since status is EXPORTED_TO_INTACCT
    schedule_charge_card_transaction_creation(
        workspace_id,
        [expense_group.id],
        False,
        1,
        triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC,
        run_in_rabbitmq_worker=False
    )

    # Task log status should remain EXPORTED_TO_INTACCT (not changed to ENQUEUED)
    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'
