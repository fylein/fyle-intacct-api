from apps.mappings.models import ImportLog
from apps.mappings.imports.modules.projects import Project
from apps.mappings.imports.modules.categories import Category
from apps.mappings.imports.modules.cost_centers import CostCenter

ATTRIBUTE_TYPE_TO_CLASS = {
    'PROJECT': Project,
    'CATEGORY': Category,
    'COST_CENTER': CostCenter,
}

def trigger_import_via_schedule(workspace_id: int, destination_field: str, attribute_type: str):
    """
    Trigger import via schedule
    :param workspace_id: Workspace id
    :param destination_field: Destination field
    :param attribute_type: Type of attribute (e.g., 'PROJECT', 'CATEGORY', 'COST_CENTER')
    """
    import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type=attribute_type).first()
    # sync_after = import_log.last_successful_run_at if import_log else None
    sync_after = None

    item_class = ATTRIBUTE_TYPE_TO_CLASS[attribute_type]
    item = item_class(workspace_id, destination_field, sync_after)
    item.trigger_import()
