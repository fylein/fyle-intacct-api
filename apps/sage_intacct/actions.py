import logging

from django.db.models import Q
from django.utils.module_loading import import_string

from apps.tasks.models import TaskLog
from apps.workspaces.models import LastExportDetail

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def update_last_export_details(workspace_id: int) -> LastExportDetail:
    """
    Update last export details
    :param workspace_id: Workspace Id
    :return: Last Export Detail
    """
    is_task_processing = TaskLog.objects.filter(workspace_id=workspace_id, status__in=['IN_PROGRESS', 'ENQUEUED']).exists()
    if is_task_processing:
        logger.info(f"Task is processing for workspace id {workspace_id}, so skipping the update of last export details")
        return

    logger.info(f"Updating last export details for workspace id {workspace_id}")
    last_export_detail = LastExportDetail.objects.get(workspace_id=workspace_id)

    failed_exports = TaskLog.objects.filter(
        ~Q(type__in=['CREATING_REIMBURSEMENT', 'FETCHING_EXPENSES', 'CREATING_AP_PAYMENT']), workspace_id=workspace_id, status__in=['FAILED', 'FATAL']
    ).count()

    filters = {
        'workspace_id': workspace_id,
        'status': 'COMPLETE'
    }

    if last_export_detail.last_exported_at:
        filters['updated_at__gt'] = last_export_detail.last_exported_at

    successful_exports = TaskLog.objects.filter(~Q(type__in=['CREATING_REIMBURSEMENT', 'FETCHING_EXPENSES', 'CREATING_AP_PAYMENT']), **filters).count()

    last_export_detail.failed_expense_groups_count = failed_exports
    last_export_detail.successful_expense_groups_count = successful_exports
    last_export_detail.total_expense_groups_count = failed_exports + successful_exports
    last_export_detail.save()

    import_string('apps.workspaces.tasks.patch_integration_settings')(workspace_id, errors=failed_exports)
    try:
        import_string('apps.fyle.actions.post_accounting_export_summary')(workspace_id=workspace_id)
    except Exception as e:
        logger.error(f"Error posting accounting export summary: {e} for workspace id {workspace_id}")

    return last_export_detail
