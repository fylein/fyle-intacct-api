from datetime import datetime, timedelta, timezone
from apps.mappings.tasks import (
    schedule_auto_map_employees,
    schedule_auto_map_charge_card_employees
)
from apps.workspaces.models import Configuration
from apps.mappings.imports.schedules import schedule_or_delete_fyle_import_tasks as new_schedule_or_delete_fyle_import_tasks
from apps.mappings.models import ImportLog


def schedule_or_delete_auto_mapping_tasks(configuration: Configuration):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    new_schedule_or_delete_fyle_import_tasks(configuration)
    schedule_auto_map_employees(
        employee_mapping_preference=configuration.auto_map_employees, workspace_id=int(configuration.workspace_id))

    if not configuration.auto_map_employees:
        schedule_auto_map_charge_card_employees(workspace_id=int(configuration.workspace_id))


def prepend_code_to_name(prepend_code_in_name: bool, value: str, code: str = None) -> str:
    """
    Format the attribute name based on the use_code_in_naming flag
    """
    if prepend_code_in_name and code:
        return "{}: {}".format(code, value)
    return value


def is_project_sync_allowed(import_log: ImportLog = None) -> bool:
    """
    Check if job sync is allowed
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
