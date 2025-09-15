import logging
from datetime import datetime, timedelta

from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from apps.fyle.models import ExpenseGroup
from apps.workspaces.models import (
    Configuration,
    LastExportDetail,
    WorkspaceSchedule
)
from apps.sage_intacct.queue import (
    schedule_bills_creation,
    schedule_expense_reports_creation,
    schedule_journal_entries_creation,
    schedule_charge_card_transaction_creation
)

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def export_to_intacct(
    workspace_id: int,
    expense_group_ids: list = [],
    triggered_by: ExpenseImportSourceEnum = None,
    run_in_rabbitmq_worker: bool = False
) -> None:
    """
    Export expenses to Intacct
    :param workspace_id: Workspace ID
    :param expense_group_ids: Expense group IDs
    :param triggered_by: Triggered by
    :param run_in_rabbitmq_worker: Run in rabbitmq worker
    :return: None
    """
    is_expenses_exported = False
    last_exported_at = datetime.now()
    export_mode = 'MANUAL' if triggered_by in (
        ExpenseImportSourceEnum.DASHBOARD_SYNC,
        ExpenseImportSourceEnum.DIRECT_EXPORT,
        ExpenseImportSourceEnum.CONFIGURATION_UPDATE
    ) else 'AUTO'
    expense_group_filters = {
        'exported_at__isnull': True,
        'workspace_id': workspace_id
    }

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    last_export_detail = LastExportDetail.objects.get(workspace_id=workspace_id)
    workspace_schedule = WorkspaceSchedule.objects.filter(workspace_id=workspace_id, interval_hours__gt=0, enabled=True).first()

    if expense_group_ids:
        expense_group_filters['id__in'] = expense_group_ids

    if configuration.reimbursable_expenses_object:
        expense_group_ids = ExpenseGroup.objects.filter(
            fund_source='PERSONAL', **expense_group_filters
        ).values_list('id', flat=True)

        if len(expense_group_ids):
            is_expenses_exported = True

        if configuration.reimbursable_expenses_object == 'EXPENSE_REPORT':
            schedule_expense_reports_creation(
                workspace_id=workspace_id,
                expense_group_ids=expense_group_ids,
                is_auto_export=export_mode == 'AUTO',
                interval_hours=workspace_schedule.interval_hours if workspace_schedule else 0,
                triggered_by=triggered_by,
                run_in_rabbitmq_worker=run_in_rabbitmq_worker
            )

        elif configuration.reimbursable_expenses_object == 'BILL':
            schedule_bills_creation(
                workspace_id=workspace_id,
                expense_group_ids=expense_group_ids,
                is_auto_export=export_mode == 'AUTO',
                interval_hours=workspace_schedule.interval_hours if workspace_schedule else 0,
                triggered_by=triggered_by,
                run_in_rabbitmq_worker=run_in_rabbitmq_worker
            )

        elif configuration.reimbursable_expenses_object == 'JOURNAL_ENTRY':
            schedule_journal_entries_creation(
                workspace_id=workspace_id,
                expense_group_ids=expense_group_ids,
                is_auto_export=export_mode == 'AUTO',
                interval_hours=workspace_schedule.interval_hours if workspace_schedule else 0,
                triggered_by=triggered_by,
                run_in_rabbitmq_worker=run_in_rabbitmq_worker
            )

    if configuration.corporate_credit_card_expenses_object:
        expense_group_ids = ExpenseGroup.objects.filter(
            fund_source='CCC', **expense_group_filters
        ).values_list('id', flat=True)

        if len(expense_group_ids):
            is_expenses_exported = True

        if configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
            schedule_charge_card_transaction_creation(
                workspace_id=workspace_id,
                expense_group_ids=expense_group_ids,
                is_auto_export=export_mode == 'AUTO',
                interval_hours=workspace_schedule.interval_hours if workspace_schedule else 0,
                triggered_by=triggered_by,
                run_in_rabbitmq_worker=run_in_rabbitmq_worker
            )

        elif configuration.corporate_credit_card_expenses_object == 'BILL':
            schedule_bills_creation(
                workspace_id=workspace_id,
                expense_group_ids=expense_group_ids,
                is_auto_export=export_mode == 'AUTO',
                interval_hours=workspace_schedule.interval_hours if workspace_schedule else 0,
                triggered_by=triggered_by,
                run_in_rabbitmq_worker=run_in_rabbitmq_worker
            )

        elif configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            schedule_expense_reports_creation(
                workspace_id=workspace_id,
                expense_group_ids=expense_group_ids,
                is_auto_export=export_mode == 'AUTO',
                interval_hours=workspace_schedule.interval_hours if workspace_schedule else 0,
                triggered_by=triggered_by,
                run_in_rabbitmq_worker=run_in_rabbitmq_worker
            )

        elif configuration.corporate_credit_card_expenses_object == 'JOURNAL_ENTRY':
            schedule_journal_entries_creation(
                workspace_id=workspace_id,
                expense_group_ids=expense_group_ids,
                is_auto_export=export_mode == 'AUTO',
                interval_hours=workspace_schedule.interval_hours if workspace_schedule else 0,
                triggered_by=triggered_by,
                run_in_rabbitmq_worker=run_in_rabbitmq_worker
            )

    if is_expenses_exported:
        last_export_detail.last_exported_at = last_exported_at
        last_export_detail.export_mode = export_mode or 'MANUAL'

        if workspace_schedule:
            last_export_detail.next_export_at = last_exported_at + timedelta(hours=workspace_schedule.interval_hours)

        last_export_detail.save(update_fields=['last_exported_at', 'export_mode', 'next_export_at'])
