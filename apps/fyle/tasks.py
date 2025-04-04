import logging
import traceback
from datetime import datetime, timezone
from typing import List

from django.db import transaction
from django_q.tasks import async_task
from django.db.models import Q
from fyle_integrations_platform_connector import PlatformConnector
from fyle_integrations_platform_connector.apis.expenses import Expenses as FyleExpenses
from fyle.platform.exceptions import (
    NoPrivilegeError,
    RetryException,
    InternalServerError,
    InvalidTokenError
)

from apps.tasks.models import Error, TaskLog
from apps.workspaces.actions import export_to_intacct
from apps.workspaces.models import (
    LastExportDetail,
    Workspace,
    FyleCredential,
    Configuration
)
from apps.fyle.models import (
    Expense,
    ExpenseFilter,
    ExpenseGroup,
    ExpenseGroupSettings
)
from apps.fyle.helpers import (
    get_fund_source,
    get_source_account_type,
    handle_import_exception,
    construct_expense_filter_query
)
from apps.fyle.actions import (
    mark_expenses_as_skipped,
    create_generator_and_post_in_batches
)

logger = logging.getLogger(__name__)
logger.level = logging.INFO


SOURCE_ACCOUNT_MAP = {
    'PERSONAL': 'PERSONAL_CASH_ACCOUNT',
    'CCC': 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'
}


def get_task_log_and_fund_source(workspace_id: int) -> tuple[TaskLog, list[str]]:
    """
    Get task log and fund source
    :param workspace_id: Workspace id
    :return: Task log and fund source
    """
    task_log, _ = TaskLog.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    fund_source = []
    if configuration.reimbursable_expenses_object:
        fund_source.append('PERSONAL')
    if configuration.corporate_credit_card_expenses_object:
        fund_source.append('CCC')

    return task_log, fund_source


def schedule_expense_group_creation(workspace_id: int) -> None:
    """
    Schedule Expense group creation
    :param workspace_id: Workspace id
    :return: None
    """
    task_log, fund_source = get_task_log_and_fund_source(workspace_id)

    async_task('apps.fyle.tasks.create_expense_groups', workspace_id, fund_source, task_log)


def create_expense_groups(workspace_id: int, fund_source: list[str], task_log: TaskLog) -> None:
    """
    Create expense groups
    :param task_log: Task log object
    :param workspace_id: workspace id
    :param fund_source: expense fund source
    """
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    try:
        with transaction.atomic():
            workspace = Workspace.objects.get(pk=workspace_id)

            last_synced_at = workspace.last_synced_at
            ccc_last_synced_at = workspace.ccc_last_synced_at
            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

            expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)

            platform = PlatformConnector(fyle_credentials)
            source_account_type = []

            for source in fund_source:
                source_account_type.append(SOURCE_ACCOUNT_MAP[source])

            filter_credit_expenses = False

            expenses = []
            reimbursable_expense_count = 0

            if 'PERSONAL' in fund_source:
                expenses.extend(platform.expenses.get(
                    source_account_type=['PERSONAL_CASH_ACCOUNT'],
                    state=expense_group_settings.expense_state,
                    settled_at=last_synced_at if expense_group_settings.expense_state == 'PAYMENT_PROCESSING' else None,
                    filter_credit_expenses=filter_credit_expenses,
                    last_paid_at=last_synced_at if expense_group_settings.expense_state == 'PAID' else None
                ))

            if workspace.last_synced_at or expenses:
                workspace.last_synced_at = datetime.now()
                reimbursable_expense_count += len(expenses)

            if 'CCC' in fund_source:
                expenses.extend(platform.expenses.get(
                    source_account_type=['PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'],
                    state=expense_group_settings.ccc_expense_state,
                    settled_at=ccc_last_synced_at if expense_group_settings.ccc_expense_state == 'PAYMENT_PROCESSING' else None,
                    approved_at=ccc_last_synced_at if expense_group_settings.ccc_expense_state == 'APPROVED' else None,
                    filter_credit_expenses=filter_credit_expenses,
                    last_paid_at=ccc_last_synced_at if expense_group_settings.ccc_expense_state == 'PAID' else None
                ))

            if workspace.ccc_last_synced_at or len(expenses) != reimbursable_expense_count:
                workspace.ccc_last_synced_at = datetime.now()

            workspace.save()

            expense_objects = Expense.create_expense_objects(expenses, workspace_id)

            expense_filters = ExpenseFilter.objects.filter(workspace_id=workspace_id).order_by('rank')
            filtered_expenses = expense_objects
            if expense_filters:
                expenses_object_ids = [expense_object.id for expense_object in expense_objects]
                final_query = construct_expense_filter_query(expense_filters)
                Expense.objects.filter(
                    final_query,
                    id__in=expenses_object_ids,
                    expensegroup__isnull=True,
                    org_id=workspace.fyle_org_id
                ).update(is_skipped=True, updated_at=datetime.now(timezone.utc))

                filtered_expenses = Expense.objects.filter(
                    is_skipped=False,
                    id__in=expenses_object_ids,
                    expensegroup__isnull=True,
                    org_id=workspace.fyle_org_id)

            ExpenseGroup.create_expense_groups_by_report_id_fund_source(
                filtered_expenses,
                configuration,
                workspace_id
            )

            task_log.status = 'COMPLETE'
            task_log.save()

    except NoPrivilegeError:
        logger.info('Invalid Fyle Credentials / Admin is disabled')
        task_log.detail = {
            'message': 'Invalid Fyle Credentials / Admin is disabled'
        }
        task_log.status = 'FAILED'
        task_log.save()

    except FyleCredential.DoesNotExist:
        logger.info('Fyle credentials not found %s', workspace_id)
        task_log.detail = {
            'message': 'Fyle credentials do not exist in workspace'
        }
        task_log.status = 'FAILED'
        task_log.save()

    except RetryException:
        logger.info('Fyle Retry Exception occured in workspace_id: %s', workspace_id)
        task_log.detail = {
            'message': 'Fyle Retry Exception occured'
        }
        task_log.status = 'FATAL'
        task_log.save()

    except InvalidTokenError:
        logger.info('Invalid Token for Fyle')
        task_log.detail = {
            'message': 'Invalid Token for Fyle'
        }
        task_log.status = 'FAILED'
        task_log.save()

    except InternalServerError:
        logger.info('Fyle Internal Server Error occured in workspace_id: %s', workspace_id)
        task_log.detail = {
            'message': 'Fyle Internal Server Error occured'
        }
        task_log.status = 'FAILED'
        task_log.save()

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save()
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)


def group_expenses_and_save(expenses: list[dict], task_log: TaskLog, workspace: Workspace) -> None:
    """
    Group expenses and save
    :param expenses: Expenses
    :param task_log: Task log object
    :param workspace: Workspace object
    :return: None
    """
    expense_objects = Expense.create_expense_objects(expenses, workspace.id)
    expense_filters = ExpenseFilter.objects.filter(workspace_id=workspace.id).order_by('rank')
    configuration = Configuration.objects.get(workspace_id=workspace.id)
    filtered_expenses = expense_objects

    if expense_filters:
        expenses_object_ids = [expense_object.id for expense_object in expense_objects]
        final_query = construct_expense_filter_query(expense_filters)

        skipped_expenses = mark_expenses_as_skipped(final_query, expenses_object_ids, workspace)
        if skipped_expenses:
            try:
                post_accounting_export_summary(workspace.fyle_org_id, workspace.id, [expense.id for expense in skipped_expenses])
            except Exception:
                logger.exception('Error posting accounting export summary for workspace_id: %s', workspace.id)

        filtered_expenses = Expense.objects.filter(
            is_skipped=False,
            id__in=expenses_object_ids,
            expensegroup__isnull=True,
            org_id=workspace.fyle_org_id
        )
    filtered_expenses = [expense for expense in filtered_expenses if not expense.is_skipped]
    ExpenseGroup.create_expense_groups_by_report_id_fund_source(
        filtered_expenses, configuration, workspace.id
    )

    task_log.status = 'COMPLETE'
    task_log.save()


def post_accounting_export_summary(org_id: str, workspace_id: int, expense_ids: List = None, fund_source: str = None, is_failed: bool = False) -> None:
    """
    Post accounting export summary to Fyle
    :param org_id: org id
    :param workspace_id: workspace id
    :param fund_source: fund source
    :return: None
    """
    # Iterate through all expenses which are not synced and post accounting export summary to Fyle in batches
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)
    filters = {
        'org_id': org_id,
        'accounting_export_summary__synced': False
    }

    if expense_ids:
        filters['id__in'] = expense_ids

    if fund_source:
        filters['fund_source'] = fund_source

    if is_failed:
        filters['accounting_export_summary__state'] = 'ERROR'

    expenses_count = Expense.objects.filter(**filters).count()

    accounting_export_summary_batches = []
    page_size = 200
    for offset in range(0, expenses_count, page_size):
        limit = offset + page_size
        paginated_expenses = Expense.objects.filter(**filters).order_by('id')[offset:limit]

        payload = []

        for expense in paginated_expenses:
            accounting_export_summary = expense.accounting_export_summary
            accounting_export_summary.pop('synced')
            payload.append(expense.accounting_export_summary)

        accounting_export_summary_batches.append(payload)

    logger.info(
        'Posting accounting export summary to Fyle workspace_id: %s, payload: %s',
        workspace_id,
        accounting_export_summary_batches
    )
    create_generator_and_post_in_batches(accounting_export_summary_batches, platform, workspace_id)


def import_and_export_expenses(report_id: str, org_id: str) -> None:
    """
    Import and export expenses
    :param report_id: report id
    :param org_id: org id
    :return: None
    """
    workspace = Workspace.objects.get(fyle_org_id=org_id)
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace.id)

    try:
        with transaction.atomic():
            task_log, _ = TaskLog.objects.update_or_create(workspace_id=workspace.id, type='FETCHING_EXPENSES', defaults={'status': 'IN_PROGRESS'})

            fund_source = get_fund_source(workspace.id)
            source_account_type = get_source_account_type(fund_source)

            platform = PlatformConnector(fyle_credentials)
            expenses = platform.expenses.get(
                source_account_type,
                filter_credit_expenses=False,
                report_id=report_id
            )

            group_expenses_and_save(expenses, task_log, workspace)

        # Export only selected expense groups
        expense_ids = Expense.objects.filter(report_id=report_id, org_id=org_id).values_list('id', flat=True)
        expense_groups = ExpenseGroup.objects.filter(expenses__id__in=[expense_ids], workspace_id=workspace.id).distinct('id').values('id')
        expense_group_ids = [expense_group['id'] for expense_group in expense_groups]

        if len(expense_group_ids):
            export_to_intacct(workspace.id, None, expense_group_ids)

    except Configuration.DoesNotExist:
        logger.info('Configuration does not exist for workspace_id: %s', workspace.id)

    except Exception:
        handle_import_exception(task_log)


def update_non_exported_expenses(data: dict) -> None:
    """
    To update expenses not in COMPLETE, IN_PROGRESS state
    :param data: data
    :return: None
    """
    expense_state = None
    org_id = data['org_id']
    expense_id = data['id']
    workspace = Workspace.objects.get(fyle_org_id=org_id)
    expense = Expense.objects.filter(workspace_id=workspace.id, expense_id=expense_id).first()

    if expense:
        if 'state' in expense.accounting_export_summary:
            expense_state = expense.accounting_export_summary['state']
        else:
            expense_state = 'NOT_EXPORTED'

        if expense_state and expense_state not in ['COMPLETE', 'IN_PROGRESS']:
            expense_obj = []
            expense_obj.append(data)
            expense_objects = FyleExpenses().construct_expense_object(expense_obj, expense.workspace_id)
            Expense.create_expense_objects(
                expense_objects, expense.workspace_id, skip_update=True
            )


def re_run_skip_export_rule(workspace: Workspace) -> None:
    """
    Skip expenses before export
    :param workspace_id: Workspace id
    :return: None
    """
    expense_filters = ExpenseFilter.objects.filter(workspace_id=workspace.id).order_by('rank')
    if expense_filters:
        filtered_expense_query = construct_expense_filter_query(expense_filters)
        # Get all expenses matching the filter query, excluding those in COMPLETE state
        expenses = Expense.objects.filter(
            filtered_expense_query,
            workspace_id=workspace.id,
            is_skipped=False
        ).exclude(
            ~Q(accounting_export_summary={}),
            accounting_export_summary__state='COMPLETE'
        )
        expense_ids = list(expenses.values_list('id', flat=True))
        skipped_expenses = mark_expenses_as_skipped(
            filtered_expense_query,
            expense_ids,
            workspace
        )
        if skipped_expenses:
            post_accounting_export_summary(workspace.fyle_org_id, workspace.id, [expense.id for expense in skipped_expenses])
            expense_groups = ExpenseGroup.objects.filter(exported_at__isnull=True, workspace_id=workspace.id)
            deleted_failed_expense_groups_count = 0
            for expense_group in expense_groups:
                task_log = TaskLog.objects.filter(
                    workspace_id=workspace.id,
                    expense_group_id=expense_group.id
                ).first()
                if task_log:
                    if task_log.status != 'COMPLETE':
                        deleted_failed_expense_groups_count += 1
                    logger.info('Deleting task log for expense group %s before export', expense_group.id)
                    task_log.delete()

                error = Error.objects.filter(
                    workspace_id=workspace.id,
                    expense_group_id=expense_group.id
                ).first()
                if error:
                    logger.info('Deleting QBO error for expense group %s before export', expense_group.id)
                    error.delete()

                expense_group.expenses.remove(*skipped_expenses)
                if not expense_group.expenses.exists():
                    logger.info('Deleting empty expense group %s before export', expense_group.id)
                    expense_group.delete()

            last_export_detail = LastExportDetail.objects.filter(workspace_id=workspace.id, failed_expense_groups_count__gt=0).first()
            if last_export_detail and deleted_failed_expense_groups_count > 0:
                last_export_detail.failed_expense_groups_count = max(
                    0,
                    last_export_detail.failed_expense_groups_count - deleted_failed_expense_groups_count
                )
                last_export_detail.total_expense_groups_count = max(
                    0,
                    last_export_detail.total_expense_groups_count - deleted_failed_expense_groups_count
                )
                last_export_detail.save()
