import logging
from datetime import datetime

from django.conf import settings
from django.db.models import Q

from fyle.platform.internals.decorators import retry
from fyle_integrations_platform_connector import PlatformConnector
from fyle.platform.exceptions import InternalServerError, RetryException

from apps.fyle.models import Expense
from apps.workspaces.models import Workspace

from apps.fyle.helpers import get_updated_accounting_export_summary, get_batched_expenses

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def __bulk_update_expenses(expense_to_be_updated: list[Expense]) -> None:
    """
    Bulk update expenses
    :param expense_to_be_updated: expenses to be updated
    :return: None
    """
    if expense_to_be_updated:
        current_time = datetime.now()
        for expense in expense_to_be_updated:
            expense.updated_at = current_time
        Expense.objects.bulk_update(expense_to_be_updated, ['is_skipped', 'accounting_export_summary', 'updated_at'], batch_size=50)


def update_expenses_in_progress(in_progress_expenses: list[Expense]) -> None:
    """
    Update expenses in progress in bulk
    :param in_progress_expenses: in progress expenses
    :return: None
    """
    expense_to_be_updated = []
    for expense in in_progress_expenses:
        expense_to_be_updated.append(
            Expense(
                id=expense.id,
                accounting_export_summary=get_updated_accounting_export_summary(
                    expense.expense_id,
                    'IN_PROGRESS',
                    None,
                    '{}/main/dashboard'.format(settings.INTACCT_INTEGRATION_APP_URL),
                    False
                )
            )
        )

    __bulk_update_expenses(expense_to_be_updated)


def mark_expenses_as_skipped(final_query: Q, expenses_object_ids: list, workspace: Workspace) -> None:
    """
    Mark expenses as skipped in bulk
    :param final_query: final query
    :param expenses_object_ids: expenses object ids
    :param workspace: workspace object
    :return: None
    """
    # We'll iterate through the list of expenses to be skipped, construct accounting export summary and update expenses
    expense_to_be_updated = []
    expenses_to_be_skipped = Expense.objects.filter(
        final_query,
        id__in=expenses_object_ids,
        org_id=workspace.fyle_org_id,
        is_skipped=False
    )

    expense_to_be_updated = []
    for expense in expenses_to_be_skipped:
        expense_to_be_updated.append(
            Expense(
                id=expense.id,
                is_skipped=True,
                accounting_export_summary=get_updated_accounting_export_summary(
                    expense.expense_id,
                    'SKIPPED',
                    None,
                    '{}/main/export_log'.format(settings.INTACCT_INTEGRATION_APP_URL),
                    False
                )
            )
        )

    if expense_to_be_updated:
        __bulk_update_expenses(expense_to_be_updated)

    # Return the updated expense objects
    return expenses_to_be_skipped


def mark_accounting_export_summary_as_synced(expenses: list[Expense]) -> None:
    """
    Mark accounting export summary as synced in bulk
    :param expenses: List of expenses
    :return: None
    """
    # Mark all expenses as synced
    expense_to_be_updated = []
    current_time = datetime.now()
    for expense in expenses:
        expense.accounting_export_summary['synced'] = True
        updated_accounting_export_summary = expense.accounting_export_summary
        expense_to_be_updated.append(
            Expense(
                id=expense.id,
                accounting_export_summary=updated_accounting_export_summary,
                previous_export_state=updated_accounting_export_summary['state'],
                updated_at=current_time
            )
        )

    Expense.objects.bulk_update(expense_to_be_updated, ['accounting_export_summary', 'previous_export_state', 'updated_at'], batch_size=50)


def update_failed_expenses(failed_expenses: list[Expense], is_mapping_error: bool) -> None:
    """
    Update failed expenses
    :param failed_expenses: Failed expenses
    :param is_mapping_error: Is mapping error
    :return: None
    """
    expense_to_be_updated = []
    for expense in failed_expenses:
        error_type = 'MAPPING' if is_mapping_error else 'ACCOUNTING_INTEGRATION_ERROR'

        # Skip dummy updates (if it is already in error state with the same error type)
        if not (expense.accounting_export_summary.get('state') == 'ERROR' and \
            expense.accounting_export_summary.get('error_type') == error_type):
            expense_to_be_updated.append(
                Expense(
                    id=expense.id,
                    accounting_export_summary=get_updated_accounting_export_summary(
                        expense.expense_id,
                        'ERROR',
                        error_type,
                        '{}/main/dashboard'.format(settings.INTACCT_INTEGRATION_APP_URL),
                        False
                    )
                )
            )

    __bulk_update_expenses(expense_to_be_updated)


def update_complete_expenses(exported_expenses: list[Expense], url: str) -> None:
    """
    Update complete expenses
    :param exported_expenses: Exported expenses
    :param url: Export url
    :return: None
    """
    expense_to_be_updated = []
    for expense in exported_expenses:
        expense_to_be_updated.append(
            Expense(
                id=expense.id,
                accounting_export_summary=get_updated_accounting_export_summary(
                    expense.expense_id,
                    'COMPLETE',
                    None,
                    url,
                    False
                )
            )
        )

    __bulk_update_expenses(expense_to_be_updated)


def __handle_post_accounting_export_summary_exception(exception: Exception, workspace_id: int) -> None:
    """
    Handle post accounting export summary exception
    :param exception: Exception
    :param workspace_id: Workspace id
    :return: None
    """
    error_response = exception.__dict__
    expense_to_be_updated = []
    if (
        'message' in error_response and error_response['message'] == 'Some of the parameters are wrong'
        and 'response' in error_response and 'data' in error_response['response'] and error_response['response']['data']
    ):
        logger.info('Error while syncing workspace %s %s',workspace_id, error_response)
        current_time = datetime.now()
        for expense in error_response['response']['data']:
            if expense['message'] == 'Permission denied to perform this action.':
                expense_instance = Expense.objects.get(expense_id=expense['key'], workspace_id=workspace_id)
                expense_to_be_updated.append(
                    Expense(
                        id=expense_instance.id,
                        accounting_export_summary=get_updated_accounting_export_summary(
                            expense_instance.expense_id,
                            'DELETED',
                            None,
                            '{}/main/dashboard'.format(settings.INTACCT_INTEGRATION_APP_URL),
                            True
                        ),
                        updated_at=current_time
                    )
                )
        if expense_to_be_updated:
            Expense.objects.bulk_update(expense_to_be_updated, ['accounting_export_summary', 'updated_at'], batch_size=50)
    else:
        logger.error('Error while syncing accounting export summary, workspace_id: %s %s', workspace_id, str(error_response))


@retry(n=3, backoff=1, exceptions=InternalServerError)
def bulk_post_accounting_export_summary(platform: PlatformConnector, payload: list[dict]) -> None:
    """
    Bulk post accounting export summary with retry of 3 times and backoff of 1 second which handles InternalServerError
    :param platform: Platform connector object
    :param payload: Payload
    :return: None
    """
    platform.expenses.post_bulk_accounting_export_summary(payload)


def create_generator_and_post_in_batches(accounting_export_summary_batches: list[dict], platform: PlatformConnector, workspace_id: int) -> None:
    """
    Create generator and post in batches
    :param accounting_export_summary_batches: Accounting export summary batches
    :param platform: Platform connector object
    :param workspace_id: Workspace id
    :return: None
    """
    for batched_payload in accounting_export_summary_batches:
        try:
            if batched_payload:
                bulk_post_accounting_export_summary(platform, batched_payload)

                batched_expenses = get_batched_expenses(batched_payload, workspace_id)
                mark_accounting_export_summary_as_synced(batched_expenses)
        except RetryException:
            logger.error(
                'Internal server error while posting accounting export summary to Fyle workspace_id: %s',
                workspace_id
            )
        except Exception as exception:
            __handle_post_accounting_export_summary_exception(exception, workspace_id)
