import logging
import traceback
from typing import List
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q
from django_q.models import Schedule
from django_q.tasks import Chain


from fyle_intacct_api.exceptions import BulkError
from apps.fyle.models import ExpenseGroup, Reimbursement, Expense
from apps.tasks.models import TaskLog, Error
from apps.workspaces.models import FyleCredential
from apps.mappings.models import GeneralMapping

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def __create_chain_and_run(fyle_credentials: FyleCredential, in_progress_expenses: List[Expense],
        workspace_id: int, chain_tasks: List[dict], fund_source: str) -> None:
    """
    Create chain and run
    :param fyle_credentials: Fyle credentials
    :param in_progress_expenses: List of in progress expenses
    :param workspace_id: workspace id
    :param chain_tasks: List of chain tasks
    :param fund_source: Fund source
    :return: None
    """
    chain = Chain()

    chain.append('apps.sage_intacct.tasks.update_expense_and_post_summary', in_progress_expenses, workspace_id, fund_source)
    chain.append('apps.fyle.helpers.sync_dimensions', fyle_credentials, True)

    for task in chain_tasks:
        chain.append(task['target'], task['expense_group'], task['task_log_id'], task['last_export'])

    chain.append('apps.fyle.tasks.post_accounting_export_summary', fyle_credentials.workspace.fyle_org_id, workspace_id, fund_source, True)
    chain.run()


def schedule_journal_entries_creation(workspace_id: int, expense_group_ids: List[str], is_auto_export: bool, fund_source: str, interval_hours: int):
    """
    Schedule journal entries creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            Q(tasklog__id__isnull=True) | ~Q(tasklog__status__in=['IN_PROGRESS', 'COMPLETE']),
            workspace_id=workspace_id, id__in=expense_group_ids, journalentry__id__isnull=True,
            exported_at__isnull=True
        ).all()

        errors = Error.objects.filter(workspace_id=workspace_id, is_resolved=False, expense_group_id__in=expense_group_ids).all()

        chain_tasks = []
        in_progress_expenses = []

        for index, expense_group in enumerate(expense_groups):
            error = errors.filter(workspace_id=workspace_id, expense_group=expense_group, is_resolved=False).first()
            skip_export = validate_failing_export(is_auto_export, interval_hours, error)
            if skip_export:
                logger.info('Skipping expense group %s as it has %s errors', expense_group.id, error.repetition_count)
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
            if not (is_auto_export and expense_group.expenses.first().previous_export_state == 'ERROR'):
                in_progress_expenses.extend(expense_group.expenses.all())

        if len(chain_tasks) > 0:
            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
            __create_chain_and_run(fyle_credentials, in_progress_expenses, workspace_id, chain_tasks, fund_source)


def validate_failing_export(is_auto_export: bool, interval_hours: int, error: Error):
    """
    Validate failing export
    :param is_auto_export: Is auto export
    :param interval_hours: Interval hours
    :param error: Error
    """
    # If auto export is enabled and interval hours is set and error repetition count is greater than 100, export only once a day
    if is_auto_export and interval_hours and error and error.repetition_count > 100:
        error.repetition_count += 1
        error.save()

        limit = round(24 / interval_hours)

        if error.repetition_count % limit != 0:
            return True

    return False


def schedule_expense_reports_creation(workspace_id: int, expense_group_ids: List[str], is_auto_export: bool, fund_source: str, interval_hours: int):
    """
    Schedule expense reports creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            Q(tasklog__id__isnull=True) | ~Q(tasklog__status__in=['IN_PROGRESS', 'COMPLETE']),
            workspace_id=workspace_id, id__in=expense_group_ids, expensereport__id__isnull=True,
            exported_at__isnull=True
        ).all()

        errors = Error.objects.filter(workspace_id=workspace_id, is_resolved=False, expense_group_id__in=expense_group_ids).all()

        chain_tasks = []
        in_progress_expenses = []

        for index, expense_group in enumerate(expense_groups):
            error = errors.filter(workspace_id=workspace_id, expense_group=expense_group, is_resolved=False).first()
            skip_export = validate_failing_export(is_auto_export, interval_hours, error)
            if skip_export:
                logger.info('Skipping expense group %s as it has %s errors', expense_group.id, error.repetition_count)
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
            if not (is_auto_export and expense_group.expenses.first().previous_export_state == 'ERROR'):
                in_progress_expenses.extend(expense_group.expenses.all())

        if len(chain_tasks) > 0:
            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
            __create_chain_and_run(fyle_credentials, in_progress_expenses, workspace_id, chain_tasks, fund_source)


def schedule_bills_creation(workspace_id: int, expense_group_ids: List[str], is_auto_export: bool, fund_source: str, interval_hours: int):
    """
    Schedule bill creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            Q(tasklog__id__isnull=True) | ~Q(tasklog__status__in=['IN_PROGRESS', 'COMPLETE']),
            workspace_id=workspace_id, id__in=expense_group_ids, bill__id__isnull=True, exported_at__isnull=True
        ).all()

        errors = Error.objects.filter(workspace_id=workspace_id, is_resolved=False, expense_group_id__in=expense_group_ids).all()

        chain_tasks = []
        in_progress_expenses = []

        for index, expense_group in enumerate(expense_groups):
            error = errors.filter(workspace_id=workspace_id, expense_group=expense_group, is_resolved=False).first()
            skip_export = validate_failing_export(is_auto_export, interval_hours, error)
            if skip_export:
                logger.info('Skipping expense group %s as it has %s errors', expense_group.id, error.repetition_count)
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
            if not (is_auto_export and expense_group.expenses.first().previous_export_state == 'ERROR'):
                in_progress_expenses.extend(expense_group.expenses.all())

        if len(chain_tasks) > 0:
            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
            __create_chain_and_run(fyle_credentials, in_progress_expenses, workspace_id, chain_tasks, fund_source)


def schedule_charge_card_transaction_creation(workspace_id: int, expense_group_ids: List[str], is_auto_export: bool, fund_source: str, interval_hours: int):
    """
    Schedule charge card transaction creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            Q(tasklog__id__isnull=True) | ~Q(tasklog__status__in=['IN_PROGRESS', 'COMPLETE']),
            workspace_id=workspace_id, id__in=expense_group_ids, chargecardtransaction__id__isnull=True,
            exported_at__isnull=True
        ).all()

        errors = Error.objects.filter(workspace_id=workspace_id, is_resolved=False, expense_group_id__in=expense_group_ids).all()

        chain_tasks = []
        in_progress_expenses = []

        for index, expense_group in enumerate(expense_groups):
            error = errors.filter(workspace_id=workspace_id, expense_group=expense_group, is_resolved=False).first()
            skip_export = validate_failing_export(is_auto_export, interval_hours, error)
            if skip_export:
                logger.info('Skipping expense group %s as it has %s errors', expense_group.id, error.repetition_count)
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
            if not (is_auto_export and expense_group.expenses.first().previous_export_state == 'ERROR'):
                in_progress_expenses.extend(expense_group.expenses.all())

        if len(chain_tasks) > 0:
            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
            __create_chain_and_run(fyle_credentials, in_progress_expenses, workspace_id, chain_tasks, fund_source)


def schedule_ap_payment_creation(configuration, workspace_id):
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


def schedule_sage_intacct_reimbursement_creation(configuration, workspace_id):
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


def schedule_sage_intacct_objects_status_sync(sync_sage_intacct_to_fyle_payments, workspace_id):
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


def schedule_fyle_reimbursements_sync(sync_sage_intacct_to_fyle_payments, workspace_id):
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
