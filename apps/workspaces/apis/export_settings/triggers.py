from datetime import datetime, timezone

from apps.workspaces.apis.export_settings.helpers import clear_workspace_errors_on_export_type_change
from fyle_accounting_mappings.models import ExpenseAttribute

from apps.sage_intacct.actions import update_last_export_details
from apps.workspaces.models import Configuration, LastExportDetail
from fyle_integrations_imports.models import ImportLog


class ExportSettingsTrigger:
    """
    Class containing all triggers for export_settings
    """
    def __init__(self, workspace_id: int, configuration: Configuration, old_configurations: dict):
        self.__workspace_id = workspace_id
        self.__configuration = configuration
        self.__old_configurations = old_configurations

    def post_save_configurations(self, is_category_mapping_changed: bool = False) -> None:
        """
        Run post save action for configurations
        """
        if is_category_mapping_changed and self.__configuration.import_categories:
            ImportLog.objects.filter(workspace_id=self.__workspace_id, attribute_type='CATEGORY').update(last_successful_run_at=None, updated_at=datetime.now(timezone.utc))
            ExpenseAttribute.objects.filter(workspace_id=self.__workspace_id, attribute_type='CATEGORY').update(auto_mapped=False)

        if self.__old_configurations and self.__configuration:
            clear_workspace_errors_on_export_type_change(self.__workspace_id, self.__old_configurations, self.__configuration)

        last_export_detail = LastExportDetail.objects.filter(workspace_id=self.__workspace_id).first()
        if last_export_detail.last_exported_at:
            update_last_export_details(self.__workspace_id)
