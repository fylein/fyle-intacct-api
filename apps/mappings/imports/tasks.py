from apps.mappings.models import ImportLog
from apps.mappings.imports.modules.projects import Project
from apps.mappings.imports.modules.categories import Category


# TODO: Add a common function later when we add more modules
def trigger_projects_import_via_schedule(workspace_id: int, destination_field: str):
    """
    Trigger projects import via schedule
    :param workspace_id: Workspace id
    :param destination_field: Destination field
    """
    print("""

        trigger_projects_import_via_schedule
    
    """)
    import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').first()
    sync_after = import_log.last_successful_run_at if import_log else None
    project = Project(workspace_id, destination_field, sync_after)
    project.trigger_import()

def trigger_categories_import_via_schedule(workspace_id: int, destination_field: str):
    """
    Trigger Categories import via schedule
    :param workspace_id: Workspace id
    :param destination_field: Destination field
    """
    print("""

        trigger_categories_import_via_schedule
    
    """)
    import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type='CATEGORY').first()
    # sync_after = import_log.last_successful_run_at if import_log else None
    sync_after = None
    category = Category(workspace_id, destination_field, sync_after)
    category.trigger_import()
