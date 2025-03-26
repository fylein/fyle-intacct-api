from datetime import datetime, timezone

from fyle_accounting_mappings.models import ExpenseAttribute

from apps.fyle.models import ExpenseGroup
from apps.tasks.models import TaskLog, Error
from apps.sage_intacct.tasks import update_last_export_details
from apps.workspaces.models import Configuration, LastExportDetail
from apps.mappings.models import ImportLog


class ExportSettingsTrigger:
    """
    Class containing all triggers for export_settings
    """
    def __init__(self, workspace_id: int, configuration: Configuration):
        self.__workspace_id = workspace_id
        self.__configuration = configuration

    def post_save_configurations(self, is_category_mapping_changed: bool = False) -> None:
        """
        Run post save action for configurations
        """
        # Delete all task logs and errors for unselected exports
        fund_source = []

        if self.__configuration.reimbursable_expenses_object:
            fund_source.append('PERSONAL')
        if self.__configuration.corporate_credit_card_expenses_object:
            fund_source.append('CCC')

        if is_category_mapping_changed and self.__configuration.import_categories:
            ImportLog.objects.filter(workspace_id=self.__workspace_id, attribute_type='CATEGORY').update(last_successful_run_at=None, updated_at=datetime.now(timezone.utc))
            ExpenseAttribute.objects.filter(workspace_id=self.__workspace_id, attribute_type__in='CATEGORY').update(auto_mapped=False)

        expense_group_ids = ExpenseGroup.objects.filter(
            workspace_id=self.__workspace_id,
            exported_at__isnull=True
        ).exclude(fund_source__in=fund_source).values_list('id', flat=True)

        if expense_group_ids:
            Error.objects.filter(workspace_id=self.__workspace_id, expense_group_id__in=expense_group_ids).delete()
            TaskLog.objects.filter(workspace_id=self.__workspace_id, expense_group_id__in=expense_group_ids, status__in=['FAILED', 'FATAL']).delete()
            last_export_detail = LastExportDetail.objects.filter(workspace_id=self.__workspace_id).first()
            if last_export_detail.last_exported_at:
                update_last_export_details(self.__workspace_id)
