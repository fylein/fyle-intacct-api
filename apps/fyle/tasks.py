import logging
from typing import List
import traceback
from datetime import datetime

from django.db import transaction
from django_q.tasks import async_task

from fyle_integrations_platform_connector import PlatformConnector
from sageintacctsdk.exceptions import NoPrivilegeError

from apps.workspaces.models import FyleCredential, Workspace, Configuration
from apps.tasks.models import TaskLog

from .models import Expense, ExpenseFilter, ExpenseGroup, ExpenseGroupSettings

from .helpers import construct_expense_filter_query

logger = logging.getLogger(__name__)
logger.level = logging.INFO


SOURCE_ACCOUNT_MAP = {
    'PERSONAL': 'PERSONAL_CASH_ACCOUNT',
    'CCC': 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'
}


def sync_reimbursements(fyle_credentials, workspace_id: int):
    platform = PlatformConnector(fyle_credentials)
    platform.reimbursements.sync()


def get_task_log_and_fund_source(workspace_id: int):
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


def schedule_expense_group_creation(workspace_id: int):
    """
    Schedule Expense group creation
    :param workspace_id: Workspace id
    :return: None
    """
    task_log, fund_source = get_task_log_and_fund_source(workspace_id)

    async_task('apps.fyle.tasks.create_expense_groups', workspace_id, fund_source, task_log)


def create_expense_groups(workspace_id: int, fund_source: List[str], task_log: TaskLog):
    """
    Create expense groups
    :param task_log: Task log object
    :param workspace_id: workspace id
    :param fund_source: expense fund source
    """
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

            filter_credit_expenses = True
            if expense_group_settings.import_card_credits:
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

            if expenses:
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

            if len(expenses) != reimbursable_expense_count:
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
                ).update(is_skipped=True)
                
                filtered_expenses = Expense.objects.filter(
                    is_skipped=False,
                    id__in=expenses_object_ids,
                    expensegroup__isnull=True,
                    org_id=workspace.fyle_org_id)   

            ExpenseGroup.create_expense_groups_by_report_id_fund_source(
                filtered_expenses, workspace_id
            )

            task_log.status = 'COMPLETE'
            task_log.save()

    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')
        task_log.detail = {
            'message': 'Insufficient permission to access the requested module'
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

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save()
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)
