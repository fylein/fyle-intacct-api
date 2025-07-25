import logging
from datetime import datetime, timedelta, timezone
from random import randint

from django.db.models import Q
from django_q.models import OrmQ, Schedule
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from apps.fyle.actions import post_accounting_export_summary, update_failed_expenses
from apps.fyle.models import ExpenseGroup
from apps.tasks.models import TaskLog
from apps.workspaces.actions import export_to_intacct
from apps.workspaces.models import LastExportDetail, Workspace

logger = logging.getLogger(__name__)
logger.level = logging.INFO

target_func = ['apps.sage_intacct.tasks.create_bill', 'apps.sage_intacct.tasks.create_expense_report', 'apps.sage_intacct.tasks.create_charge_card_transaction', 'apps.sage_intacct.tasks.create_journal_entry']


def re_export_stuck_exports() -> None:
    """
    Re-exports stuck exports by identifying failed export attempts
    and retrying them.
    """
    prod_workspace_ids = Workspace.objects.filter(
        ~Q(name__icontains='fyle for') & ~Q(name__iendswith='test')
    ).values_list('id', flat=True)
    task_logs = TaskLog.objects.filter(
        status__in=['ENQUEUED', 'IN_PROGRESS'],
        updated_at__lt=datetime.now() - timedelta(minutes=60),
        updated_at__gt=datetime.now() - timedelta(days=7),
        expense_group_id__isnull=False,
        workspace_id__in=prod_workspace_ids
    )
    if task_logs.count() > 0:
        logger.info('Re-exporting stuck task_logs')
        logger.info('%s stuck task_logs found', task_logs.count())
        workspace_ids = list(task_logs.values_list('workspace_id', flat=True).distinct())
        expense_group_ids = list(task_logs.values_list('expense_group_id', flat=True))
        ormqs = OrmQ.objects.all()
        for orm in ormqs:
            if 'chain' in orm.task and orm.task['chain']:
                for chain in orm.task['chain']:
                    if len(chain) > 1 and chain[0] in target_func and isinstance(chain[1][0], int):
                        if chain[1][0] in expense_group_ids:
                            logger.info('Skipping Re Export For Expense group %s', chain[1][0])
                            expense_group_ids.remove(chain[1][0])

        logger.info('Re-exporting Expense Group IDs: %s', expense_group_ids)
        expense_groups = ExpenseGroup.objects.filter(id__in=expense_group_ids)
        expenses = []
        for expense_group in expense_groups:
            expenses.extend(expense_group.expenses.all())
        workspace_ids_list = list(workspace_ids)
        task_logs.update(status='FAILED', updated_at=datetime.now())
        for workspace_id in workspace_ids_list:
            errored_expenses = [expense for expense in expenses if expense.workspace_id == workspace_id]
            update_failed_expenses(errored_expenses, True)
            post_accounting_export_summary(workspace_id=workspace_id,  expense_ids=[expense.id for expense in errored_expenses], is_failed=True)
        schedules = Schedule.objects.filter(
            args__in=[str(workspace_id) for workspace_id in workspace_ids_list],
            func='apps.workspaces.tasks.run_sync_schedule'
        )
        for workspace_id in workspace_ids_list:
            logger.info('Checking if 1hour sync schedule for workspace %s', workspace_id)
            schedule = schedules.filter(args=str(workspace_id)).first()
            # If schedule exist and it's within 1 hour, need not trigger it immediately
            if not (schedule and schedule.next_run < datetime.now(tz=schedule.next_run.tzinfo) + timedelta(minutes=60)):
                export_expense_group_ids = list(expense_groups.filter(workspace_id=workspace_id).values_list('id', flat=True))
                if export_expense_group_ids and len(export_expense_group_ids) < 200:
                    logger.info('Re-triggering export for expense group %s since no 1 hour schedule for workspace  %s', export_expense_group_ids, workspace_id)
                    export_to_intacct(workspace_id=workspace_id, expense_group_ids=export_expense_group_ids, triggered_by=ExpenseImportSourceEnum.INTERNAL)
                else:
                    logger.info('Skipping export for workspace %s since it has more than 200 expense groups', workspace_id)


def pause_and_resume_export_schedules() -> None:
    """
    Pauses and resumes export schedules based on the current time.
    If the export failure count > 50 and the run_sync_schedule is present move it to +30 days,
    if the error count is < 50 and run_sync_schedule has moved to >25 days, move it to now + interval hours
    """
    current_time = datetime.now(timezone.utc)
    workspaces_with_gt_50_failed_exports = list(LastExportDetail.objects.filter(
        failed_expense_groups_count__gt=50,
        updated_at__gte=current_time - timedelta(hours=12),
    ).values_list('workspace_id', flat=True))

    workspaces_with_lt_50_failed_exports = list(LastExportDetail.objects.filter(
        failed_expense_groups_count__lt=50,
        updated_at__gte=current_time - timedelta(hours=12),
    ).values_list('workspace_id', flat=True))

    schedules_to_pause = []
    paused_workspace_ids = []

    schedules = Schedule.objects.filter(
        args__in=(str(workspace_id) for workspace_id in workspaces_with_gt_50_failed_exports),
        func='apps.workspaces.tasks.run_sync_schedule',
        next_run__lt=current_time + timedelta(days=25)
    ).all()

    if schedules:
        for schedule in schedules:
            schedule.next_run = current_time + timedelta(days=30) + timedelta(hours=randint(0, 5)) + timedelta(minutes=randint(0, 60))  # just for scattering schedules
            schedules_to_pause.append(schedule)
            paused_workspace_ids.append(schedule.args)

        Schedule.objects.bulk_update(
            schedules_to_pause,
            ['next_run']
        )
        logger.info('Paused export schedules for workspaces with > 50 failed exports: %s', paused_workspace_ids)

    schedules_to_resume = []
    resumed_workspace_ids = []

    schedules = Schedule.objects.filter(
        args__in=(str(workspace_id) for workspace_id in workspaces_with_lt_50_failed_exports),
        func='apps.workspaces.tasks.run_sync_schedule',
        next_run__gt=current_time + timedelta(days=25)
    ).all()

    if schedules:
        for schedule in schedules:
            schedule.next_run = current_time + timedelta(hours=randint(0, 5)) + timedelta(minutes=randint(0, 60))  # just for scattering schedules
            schedules_to_resume.append(schedule)
            resumed_workspace_ids.append(schedule.args)

        Schedule.objects.bulk_update(
            schedules_to_resume,
            ['next_run']
        )
        logger.info('Resumed export schedules for workspaces with < 50 failed exports: %s', resumed_workspace_ids)
