from apps.mappings.models import ImportLog
from apps.mappings.imports.modules.projects import Project


# TODO: Add a common function later when we add more modules
def trigger_projects_import_via_schedule(workspace_id: int, destination_field: str):
    import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').first()
    sync_after = import_log.last_successful_run_at if import_log else None
    project = Project(workspace_id, destination_field, sync_after)
    project.trigger_import()
