from apps.mappings.models import ImportLog
from apps.mappings.imports.modules.projects import Project
from apps.mappings.imports.modules.categories import Category
from apps.mappings.imports.modules.cost_centers import CostCenter
from apps.mappings.imports.modules.tax_groups import TaxGroup

SOURCE_FIELD_CLASS_MAP = {
    'PROJECT': Project,
    'CATEGORY': Category,
    'COST_CENTER': CostCenter,
    'TAX_GROUP': TaxGroup
}

def trigger_import_via_schedule(workspace_id: int, destination_field: str, source_field: str):
    """
    Trigger import via schedule
    :param workspace_id: Workspace id
    :param destination_field: Destination field
    :param source_field: Type of attribute (e.g., 'PROJECT', 'CATEGORY', 'COST_CENTER')
    """
    import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type=source_field).first()
    sync_after = import_log.last_successful_run_at if import_log else None

    module_class = SOURCE_FIELD_CLASS_MAP[source_field]
    item = module_class(workspace_id, destination_field, sync_after)
    item.trigger_import()
