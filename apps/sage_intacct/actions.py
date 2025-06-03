import logging
from django.db.models import Q
from django.conf import settings

from apps.workspaces.models import FyleCredential
from apps.fyle.helpers import patch_request
from apps.workspaces.models import LastExportDetail
from apps.fyle.actions import post_accounting_export_summary
from apps.tasks.models import TaskLog

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def patch_integration_settings(workspace_id: int, errors: int = None, is_token_expired: bool = None) -> None:
    """
    Patch integration settings
    """
    refresh_token = FyleCredential.objects.get(workspace_id=workspace_id).refresh_token
    url = '{}/integrations/'.format(settings.INTEGRATIONS_SETTINGS_API)
    payload = {
        'tpa_name': 'Fyle Sage Intacct Integration'
    }

    if errors is not None:
        payload['errors_count'] = errors

    if is_token_expired is not None:
        payload['is_token_expired'] = is_token_expired

    try:
        patch_request(url, payload, refresh_token)
    except Exception as error:
        logger.error(error, exc_info=True)


def update_last_export_details(workspace_id: int) -> LastExportDetail:
    """
    Update last export details
    :param workspace_id: Workspace Id
    :return: Last Export Detail
    """
    last_export_detail = LastExportDetail.objects.get(workspace_id=workspace_id)

    failed_exports = TaskLog.objects.filter(
        ~Q(type__in=['CREATING_REIMBURSEMENT', 'FETCHING_EXPENSES', 'CREATING_AP_PAYMENT']), workspace_id=workspace_id, status__in=['FAILED', 'FATAL']
    ).count()

    successful_exports = TaskLog.objects.filter(
        ~Q(type__in=['CREATING_REIMBURSEMENT', 'FETCHING_EXPENSES', 'CREATING_AP_PAYMENT']),
        workspace_id=workspace_id,
        status='COMPLETE',
        updated_at__gt=last_export_detail.last_exported_at
    ).count()

    last_export_detail.failed_expense_groups_count = failed_exports
    last_export_detail.successful_expense_groups_count = successful_exports
    last_export_detail.total_expense_groups_count = failed_exports + successful_exports
    last_export_detail.save()

    patch_integration_settings(workspace_id, errors=failed_exports)
    try:
        post_accounting_export_summary(workspace_id=workspace_id)
    except Exception as e:
        logger.error(f"Error posting accounting export summary: {e} for workspace id {workspace_id}")

    return last_export_detail
