import logging
from datetime import datetime, timedelta, timezone

from fyle_accounting_mappings.models import ExpenseAttribute

from apps.mappings.schedules import schedule_or_delete_fyle_import_tasks as new_schedule_or_delete_fyle_import_tasks
from apps.mappings.tasks import schedule_auto_map_accounting_fields
from apps.workspaces.models import Configuration
from apps.workspaces.models import Configuration as WorkspaceGeneralSettings
from apps.workspaces.tasks import patch_integration_settings_for_unmapped_cards
from fyle_integrations_imports.models import ImportLog

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def schedule_or_delete_auto_mapping_tasks(configuration: Configuration) -> None:
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    new_schedule_or_delete_fyle_import_tasks(configuration)
    schedule_auto_map_accounting_fields(workspace_id=configuration.workspace_id)


def prepend_code_to_name(prepend_code_in_name: bool, value: str, code: str = None) -> str:
    """
    Format the attribute name based on the use_code_in_naming flag
    :param prepend_code_in_name: Boolean flag to prepend code in name
    :param value: Value of the attribute
    :param code: Code of the attribute
    :return: Formatted attribute name
    """
    if prepend_code_in_name and code:
        return "{}: {}".format(code, value)
    return value


def is_project_sync_allowed(import_log: ImportLog = None) -> bool:
    """
    Check if job sync is allowed
    :param import_log: Import Log Instance
    :return: Boolean
    """
    time_difference = datetime.now(timezone.utc) - timedelta(minutes=30)
    time_difference = time_difference.replace(tzinfo=timezone.utc)

    if (
        not import_log
        or import_log.last_successful_run_at is None
        or import_log.last_successful_run_at < time_difference
    ):
        return True

    return False


def patch_corporate_card_integration_settings(workspace_id: int) -> None:
    """
    Patch integration settings for unmapped corporate cards.
    This is called when corporate card mapping is created or when a corporate card is created via webhook.

    :param workspace_id: Workspace ID
    :return: None
    """
    workspace_general_settings = WorkspaceGeneralSettings.objects.filter(workspace_id=workspace_id).first()

    if workspace_general_settings and workspace_general_settings.corporate_credit_card_expenses_object in ('CHARGE_CARD_TRANSACTION',):
        unmapped_card_count = ExpenseAttribute.objects.filter(
            attribute_type="CORPORATE_CARD", workspace_id=workspace_id, active=True, mapping__isnull=True
        ).count()

        patch_integration_settings_for_unmapped_cards(workspace_id=workspace_id, unmapped_card_count=unmapped_card_count)
        logger.info(f"Patched integration settings for workspace {workspace_id}, unmapped card count: {unmapped_card_count}")
