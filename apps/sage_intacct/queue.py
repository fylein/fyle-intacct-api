import logging
from datetime import datetime, timedelta
from typing import List

from django.db.models import Q
from django_q.models import Schedule
from django_q.tasks import Chain
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from fyle_accounting_library.rabbitmq.data_class import Task
from fyle_accounting_library.rabbitmq.helpers import TaskChainRunner

from apps.fyle.actions import post_accounting_export_summary_for_skipped_exports
from apps.fyle.helpers import check_interval_and_sync_dimension
from apps.fyle.models import ExpenseGroup
from apps.mappings.models import GeneralMapping
from apps.sage_intacct.actions import update_last_export_details
from apps.tasks.models import Error, TaskLog
from apps.workspaces.models import Configuration

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def __create_chain_and_run(workspace_id: int, chain_tasks: List[dict], run_in_rabbitmq_worker: bool) -> None:
    """
    Create chain and run
    :param workspace_id: Workspace ID
    :param chain_tasks: List of chain tasks
    :param is_auto_export: Is auto export
    :param run_in_rabbitmq_worker: Run in rabbitmq worker
    :return: None
    """
    if run_in_rabbitmq_worker:
        # This function checks intervals and triggers sync if needed, syncing dimension for all exports is overkill
        check_interval_and_sync_dimension(workspace_id)

        task_executor = TaskChainRunner()
        task_executor.run(chain_tasks, workspace_id)
    else:
        chunk_size = 30
        logger.info('Breaking chain of %s tasks into chunks of %s for workspace %s', len(chain_tasks), chunk_size, workspace_id)

        for i in range(0, len(chain_tasks), chunk_size):
            chunk = chain_tasks[i:i + chunk_size]
            chunk_number = (i // chunk_size) + 1
            total_chunks = (len(chain_tasks) + chunk_size - 1) // chunk_size

            logger.info('Processing chunk %s of %s with %s tasks for workspace %s', chunk_number, total_chunks, len(chunk), workspace_id)

            chain = Chain()
            # Only add sync_dimensions for the first chunk
            if i == 0:
                chain.append('apps.fyle.helpers.sync_dimensions', workspace_id, True)

            for j, task in enumerate(chunk):
                # Remove is_auto_export from the args
                args = list(task.args[:-1])

                # Add is_auto_export to the args for final task in chunk, each chunk is gonna have
                if j == len(chunk) - 1:
                    args.append(True)
                chain.append(task.target, *args)

            chain.run()


def handle_skipped_exports(expense_groups: List[ExpenseGroup], index: int, skip_export_count: int, expense_group: ExpenseGroup, triggered_by: ExpenseImportSourceEnum) -> int:
    """
    Handle common export scheduling logic for skip tracking, logging, posting skipped export summaries, and last export updates.
    """
    total_count = expense_groups.count()
    last_export = (index + 1) == total_count

    logger.info('Skipping export for expense group %s', expense_group.id)
    skip_export_count += 1
    if triggered_by == ExpenseImportSourceEnum.DIRECT_EXPORT:
        post_accounting_export_summary_for_skipped_exports(expense_group=expense_group, workspace_id=expense_group.workspace_id)
    if last_export and skip_export_count == total_count:
        update_last_export_details(expense_group.workspace_id)

    return skip_export_count


def schedule_journal_entries_creation(
    workspace_id: int,
    expense_group_ids: list[str],
    is_auto_export: bool,
    interval_hours: int,
    triggered_by: ExpenseImportSourceEnum,
    run_in_rabbitmq_worker: bool
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

        fund_source = expense_groups.first().fund_source

        chain_tasks.append(Task(
            target='apps.sage_intacct.tasks.check_cache_and_search_vendors',
            args=[workspace_id, fund_source]
        ))

        skip_export_count = 0
        for index, expense_group in enumerate(expense_groups):
            skip_export = validate_failing_export(is_auto_export, interval_hours, expense_group)
            if skip_export:
                skip_export_count = handle_skipped_exports(
                    expense_groups=expense_groups, index=index, skip_export_count=skip_export_count, expense_group=expense_group, triggered_by=triggered_by
                )
                continue

            task_log, _ = TaskLog.objects.get_or_create(
                workspace_id=expense_group.workspace_id,
                expense_group=expense_group,
                defaults={
                    'status': 'ENQUEUED',
                    'type': 'CREATING_JOURNAL_ENTRIES',
                    'triggered_by': triggered_by
                }
            )
            if task_log.status not in ['IN_PROGRESS', 'ENQUEUED']:
                task_log.status = 'ENQUEUED'
                if triggered_by and task_log.triggered_by != triggered_by:
                    task_log.triggered_by = triggered_by
                task_log.save()

            chain_tasks.append(Task(
                target='apps.sage_intacct.tasks.create_journal_entry',
                args=[expense_group.id, task_log.id, is_auto_export, (expense_groups.count() == index + 1)]
            ))

        if len(chain_tasks) > 0:
            __create_chain_and_run(workspace_id, chain_tasks, run_in_rabbitmq_worker)


def validate_failing_export(is_auto_export: bool, interval_hours: int, expense_group: ExpenseGroup) -> bool:
    """
    Validate failing export
    :param is_auto_export: Is auto export
    :param interval_hours: Interval hours
    :param expense_group: Expense Group
    :return: bool
    """
    mapping_error = Error.objects.filter(
        workspace_id=expense_group.workspace_id,
        mapping_error_expense_group_ids__contains=[expense_group.id],
        is_resolved=False
    ).first()
    if mapping_error:
        return True

    return False


def schedule_expense_reports_creation(workspace_id: int, expense_group_ids: list[str], is_auto_export: bool, interval_hours: int, triggered_by: ExpenseImportSourceEnum, run_in_rabbitmq_worker: bool) -> None:
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

        skip_export_count = 0
        for index, expense_group in enumerate(expense_groups):
            skip_export = validate_failing_export(is_auto_export, interval_hours, expense_group)
            if skip_export:
                skip_export_count = handle_skipped_exports(
                    expense_groups=expense_groups, index=index, skip_export_count=skip_export_count, expense_group=expense_group, triggered_by=triggered_by
                )
                continue

            task_log, _ = TaskLog.objects.get_or_create(
                workspace_id=expense_group.workspace_id,
                expense_group=expense_group,
                defaults={
                    'status': 'ENQUEUED',
                    'type': 'CREATING_EXPENSE_REPORTS',
                    'triggered_by': triggered_by
                }
            )
            if task_log.status not in ['IN_PROGRESS', 'ENQUEUED']:
                task_log.status = 'ENQUEUED'
                if triggered_by and task_log.triggered_by != triggered_by:
                    task_log.triggered_by = triggered_by
                task_log.save()

            chain_tasks.append(Task(
                target='apps.sage_intacct.tasks.create_expense_report',
                args=[expense_group.id, task_log.id, is_auto_export, (expense_groups.count() == index + 1)]
            ))

        if len(chain_tasks) > 0:
            __create_chain_and_run(workspace_id, chain_tasks, run_in_rabbitmq_worker)


def schedule_bills_creation(workspace_id: int, expense_group_ids: list[str], is_auto_export: bool, interval_hours: int, triggered_by: ExpenseImportSourceEnum, run_in_rabbitmq_worker: bool) -> None:
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

        fund_source = expense_groups.first().fund_source

        chain_tasks.append(Task(
            target='apps.sage_intacct.tasks.check_cache_and_search_vendors',
            args=[workspace_id, fund_source]
        ))

        skip_export_count = 0
        for index, expense_group in enumerate(expense_groups):
            skip_export = validate_failing_export(is_auto_export, interval_hours, expense_group)
            if skip_export:
                skip_export_count = handle_skipped_exports(
                    expense_groups=expense_groups, index=index, skip_export_count=skip_export_count, expense_group=expense_group, triggered_by=triggered_by
                )
                continue

            task_log, _ = TaskLog.objects.get_or_create(
                workspace_id=expense_group.workspace_id,
                expense_group=expense_group,
                defaults={
                    'status': 'ENQUEUED',
                    'type': 'CREATING_BILLS',
                    'triggered_by': triggered_by
                }
            )
            if task_log.status not in ['IN_PROGRESS', 'ENQUEUED']:
                task_log.status = 'ENQUEUED'
                if triggered_by and task_log.triggered_by != triggered_by:
                    task_log.triggered_by = triggered_by
                task_log.save()

            chain_tasks.append(Task(
                target='apps.sage_intacct.tasks.create_bill',
                args=[expense_group.id, task_log.id, is_auto_export, (expense_groups.count() == index + 1)]
            ))

        if len(chain_tasks) > 0:
            __create_chain_and_run(workspace_id, chain_tasks, run_in_rabbitmq_worker)


def schedule_charge_card_transaction_creation(workspace_id: int, expense_group_ids: list[str], is_auto_export: bool, interval_hours: int, triggered_by: ExpenseImportSourceEnum, run_in_rabbitmq_worker: bool) -> None:
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

        fund_source = expense_groups.first().fund_source

        chain_tasks.append(Task(
            target='apps.sage_intacct.tasks.check_cache_and_search_vendors',
            args=[workspace_id, fund_source]
        ))

        skip_export_count = 0
        for index, expense_group in enumerate(expense_groups):
            skip_export = validate_failing_export(is_auto_export, interval_hours, expense_group)
            if skip_export:
                skip_export_count = handle_skipped_exports(
                    expense_groups=expense_groups, index=index, skip_export_count=skip_export_count, expense_group=expense_group, triggered_by=triggered_by
                )
                continue

            task_log, _ = TaskLog.objects.get_or_create(
                workspace_id=expense_group.workspace_id,
                expense_group=expense_group,
                defaults={
                    'status': 'ENQUEUED',
                    'type': 'CREATING_CHARGE_CARD_TRANSACTIONS',
                    'triggered_by': triggered_by
                }
            )
            if task_log.status not in ['IN_PROGRESS', 'ENQUEUED']:
                task_log.status = 'ENQUEUED'
                if triggered_by and task_log.triggered_by != triggered_by:
                    task_log.triggered_by = triggered_by
                task_log.save()

            chain_tasks.append(Task(
                target='apps.sage_intacct.tasks.create_charge_card_transaction',
                args=[expense_group.id, task_log.id, is_auto_export, (expense_groups.count() == index + 1)]
            ))

        if len(chain_tasks) > 0:
            __create_chain_and_run(workspace_id, chain_tasks, run_in_rabbitmq_worker)


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
