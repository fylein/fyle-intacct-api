import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, timezone
from typing import List

from django.db.models import Q
from django_q.models import Schedule
from django_q.tasks import Chain

from apps.tasks.models import TaskLog
from apps.fyle.models import ExpenseGroup
from apps.workspaces.models import Configuration
from apps.mappings.models import GeneralMapping

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def __create_chain_and_run(workspace_id: int, chain_tasks: List[dict], is_auto_export: bool) -> None:
    """
    Create chain and run
    :param workspace_id: Workspace ID
    :param chain_tasks: List of chain tasks
    :param is_auto_export: Is auto export
    :return: None
    """
    chain = Chain()
    chain.append('apps.fyle.helpers.sync_dimensions', workspace_id, True)

    for task in chain_tasks:
        chain.append(task['target'], task['expense_group'], task['task_log_id'], task['last_export'], is_auto_export)

    chain.run()


def schedule_journal_entries_creation(
    workspace_id: int,
    expense_group_ids: list[str],
    is_auto_export: bool,
    interval_hours: int
) -> None:
    """
    Schedule journal entries creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    q_filter = Q(tasklog__id__isnull=True) | ~Q(tasklog__status__in=['IN_PROGRESS', 'COMPLETE'])
    if is_auto_export:
        q_filter = q_filter | Q(tasklog__is_retired=False)

    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            q_filter,
            workspace_id=workspace_id, id__in=expense_group_ids, journalentry__id__isnull=True,
            exported_at__isnull=True
        ).all()

        chain_tasks = []

        for index, expense_group in enumerate(expense_groups):
            skip_export = validate_failing_export(is_auto_export, interval_hours, expense_group)

            if skip_export:
                logger.info('Skipping export for expense group %s', expense_group.id)
                continue

            task_log, _ = TaskLog.objects.get_or_create(
                workspace_id=expense_group.workspace_id,
                expense_group=expense_group,
                defaults={
                    'status': 'ENQUEUED',
                    'type': 'CREATING_JOURNAL_ENTRIES'
                }
            )
            if task_log.status not in ['IN_PROGRESS', 'ENQUEUED']:
                task_log.status = 'ENQUEUED'
                task_log.save()

            last_export = False
            if expense_groups.count() == index + 1:
                last_export = True

            chain_tasks.append({
                'target': 'apps.sage_intacct.tasks.create_journal_entry',
                'expense_group': expense_group,
                'task_log_id': task_log.id,
                'last_export': last_export
            })

        if len(chain_tasks) > 0:
            __create_chain_and_run(workspace_id, chain_tasks, is_auto_export)


def validate_failing_export(is_auto_export: bool, interval_hours: int, expense_group: ExpenseGroup) -> bool:
    """
    Validate failing export
    :param is_auto_export: Is auto export
    :param interval_hours: Interval hours
    :param expense_group: Expense Group
    :return: bool
    """
    if is_auto_export and interval_hours:
        task_log = TaskLog.objects.filter(expense_group=expense_group, workspace_id=expense_group.workspace.id).first()
        now = datetime.now(tz=timezone.utc)

        if task_log:
            # if the task log is created before 2 months
            if task_log.created_at <= now - relativedelta(months=2):
                task_log.is_retired = True
                task_log.save()
                return True

            # if the task log is created in the last 2 months
            if now - relativedelta(months=2) < task_log.created_at <= now - relativedelta(months=1):
                if now - task_log.updated_at.replace(tzinfo=timezone.utc) <= timedelta(weeks=1):
                    return True

            # if the task log is created is the last month
            if task_log.created_at > now - relativedelta(months=1):
                if now - task_log.updated_at.replace(tzinfo=timezone.utc) <= timedelta(hours=24):
                    return True

    return False


def schedule_expense_reports_creation(workspace_id: int, expense_group_ids: list[str], is_auto_export: bool, interval_hours: int) -> None:
    """
    Schedule expense reports creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    q_filter = Q(tasklog__id__isnull=True) | ~Q(tasklog__status__in=['IN_PROGRESS', 'COMPLETE'])
    if is_auto_export:
        q_filter = q_filter | Q(tasklog__is_retired=False)

    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            q_filter,
            workspace_id=workspace_id, id__in=expense_group_ids, expensereport__id__isnull=True,
            exported_at__isnull=True
        ).all()

        chain_tasks = []

        for index, expense_group in enumerate(expense_groups):
            skip_export = validate_failing_export(is_auto_export, interval_hours, expense_group)

            if skip_export:
                logger.info('Skipping export for expense group %s', expense_group.id)
                continue

            task_log, _ = TaskLog.objects.get_or_create(
                workspace_id=expense_group.workspace_id,
                expense_group=expense_group,
                defaults={
                    'status': 'ENQUEUED',
                    'type': 'CREATING_EXPENSE_REPORTS'
                }
            )
            if task_log.status not in ['IN_PROGRESS', 'ENQUEUED']:
                task_log.status = 'ENQUEUED'
                task_log.save()

            last_export = False
            if expense_groups.count() == index + 1:
                last_export = True

            chain_tasks.append({
                'target': 'apps.sage_intacct.tasks.create_expense_report',
                'expense_group': expense_group,
                'task_log_id': task_log.id,
                'last_export': last_export
            })

        if len(chain_tasks) > 0:
            __create_chain_and_run(workspace_id, chain_tasks, is_auto_export)


def schedule_bills_creation(workspace_id: int, expense_group_ids: list[str], is_auto_export: bool, interval_hours: int) -> None:
    """
    Schedule bill creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    q_filter = Q(tasklog__id__isnull=True) | ~Q(tasklog__status__in=['IN_PROGRESS', 'COMPLETE'])
    if is_auto_export:
        q_filter = q_filter | Q(tasklog__is_retired=False)

    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            q_filter,
            workspace_id=workspace_id, id__in=expense_group_ids, bill__id__isnull=True, exported_at__isnull=True
        ).all()

        chain_tasks = []

        for index, expense_group in enumerate(expense_groups):
            skip_export = validate_failing_export(is_auto_export, interval_hours, expense_group)

            if skip_export:
                logger.info('Skipping export for expense group %s', expense_group.id)
                continue

            task_log, _ = TaskLog.objects.get_or_create(
                workspace_id=expense_group.workspace_id,
                expense_group=expense_group,
                defaults={
                    'status': 'ENQUEUED',
                    'type': 'CREATING_BILLS'
                }
            )
            if task_log.status not in ['IN_PROGRESS', 'ENQUEUED']:
                task_log.status = 'ENQUEUED'
                task_log.save()

            last_export = False
            if expense_groups.count() == index + 1:
                last_export = True

            chain_tasks.append({
                'target': 'apps.sage_intacct.tasks.create_bill',
                'expense_group': expense_group,
                'task_log_id': task_log.id,
                'last_export': last_export
            })

        if len(chain_tasks) > 0:
            __create_chain_and_run(workspace_id, chain_tasks, is_auto_export)


def schedule_charge_card_transaction_creation(workspace_id: int, expense_group_ids: list[str], is_auto_export: bool, interval_hours: int) -> None:
    """
    Schedule charge card transaction creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    q_filter = Q(tasklog__id__isnull=True) | ~Q(tasklog__status__in=['IN_PROGRESS', 'COMPLETE'])
    if is_auto_export:
        q_filter = q_filter | Q(tasklog__is_retired=False)

    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            q_filter,
            workspace_id=workspace_id, id__in=expense_group_ids, chargecardtransaction__id__isnull=True,
            exported_at__isnull=True
        ).all()

        chain_tasks = []

        for index, expense_group in enumerate(expense_groups):
            skip_export = validate_failing_export(is_auto_export, interval_hours, expense_group)
            if skip_export:
                logger.info('Skipping export for expense group %s', expense_group.id)
                continue

            task_log, _ = TaskLog.objects.get_or_create(
                workspace_id=expense_group.workspace_id,
                expense_group=expense_group,
                defaults={
                    'status': 'ENQUEUED',
                    'type': 'CREATING_CHARGE_CARD_TRANSACTIONS'
                }
            )
            if task_log.status not in ['IN_PROGRESS', 'ENQUEUED']:
                task_log.status = 'ENQUEUED'
                task_log.save()

            last_export = False
            if expense_groups.count() == index + 1:
                last_export = True

            chain_tasks.append({
                'target': 'apps.sage_intacct.tasks.create_charge_card_transaction',
                'expense_group': expense_group,
                'task_log_id': task_log.id,
                'last_export': last_export
            })

        if len(chain_tasks) > 0:
            __create_chain_and_run(workspace_id, chain_tasks, is_auto_export)


def schedule_ap_payment_creation(configuration: Configuration, workspace_id: int) -> None:
    """
    Schedule AP payment creation
    :param configuration: Configuration
    :param workspace_id: workspace id
    :return: None
    """
    general_mappings: GeneralMapping = GeneralMapping.objects.filter(workspace_id=workspace_id).first()

    if general_mappings:
        if configuration.sync_fyle_to_sage_intacct_payments and general_mappings.payment_account_id and configuration.reimbursable_expenses_object == 'BILL':
            start_datetime = datetime.now()
            schedule, _ = Schedule.objects.update_or_create(
                func='apps.sage_intacct.tasks.create_ap_payment',
                args='{}'.format(workspace_id),
                defaults={
                    'schedule_type': Schedule.MINUTES,
                    'minutes': 24 * 60,
                    'next_run': start_datetime
                }
            )
            return

        schedule: Schedule = Schedule.objects.filter(
            func='apps.sage_intacct.tasks.create_ap_payment',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()


def schedule_sage_intacct_reimbursement_creation(configuration: Configuration, workspace_id: int) -> None:
    """
    Schedule Sage Intacct reimbursement creation
    :param configuration: Configuration
    :param workspace_id: workspace id
    :return: None
    """
    general_mappings: GeneralMapping = GeneralMapping.objects.filter(workspace_id=workspace_id).first()

    if general_mappings:
        if configuration.sync_fyle_to_sage_intacct_payments and general_mappings.payment_account_id and configuration.reimbursable_expenses_object == 'EXPENSE_REPORT':
            start_datetime = datetime.now()
            schedule, _ = Schedule.objects.update_or_create(
                func='apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
                args='{}'.format(workspace_id),
                defaults={
                    'schedule_type': Schedule.MINUTES,
                    'minutes': 24 * 60,
                    'next_run': start_datetime
                }
            )
            return

        schedule: Schedule = Schedule.objects.filter(
            func='apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()


def schedule_sage_intacct_objects_status_sync(sync_sage_intacct_to_fyle_payments: bool, workspace_id: int) -> None:
    """
    Schedule Sage Intacct objects status sync
    :param sync_sage_intacct_to_fyle_payments: Sync Sage Intacct to Fyle payments
    :param workspace_id: workspace id
    :return
    """
    if sync_sage_intacct_to_fyle_payments:
        start_datetime = datetime.now()
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.sage_intacct.tasks.check_sage_intacct_object_status',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.sage_intacct.tasks.check_sage_intacct_object_status',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()


def schedule_fyle_reimbursements_sync(sync_sage_intacct_to_fyle_payments: bool, workspace_id: int) -> None:
    """
    Schedule Fyle reimbursements sync
    :param sync_sage_intacct_to_fyle_payments: Sync Sage Intacct to Fyle payments
    :param workspace_id: workspace id
    :return None
    """
    if sync_sage_intacct_to_fyle_payments:
        start_datetime = datetime.now() + timedelta(hours=12)
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.sage_intacct.tasks.process_fyle_reimbursements',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.sage_intacct.tasks.process_fyle_reimbursements',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()
