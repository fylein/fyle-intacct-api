import logging
from datetime import datetime, timezone

from fyle_accounting_mappings.models import ExpenseAttribute
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum, ExpenseStateEnum, FundSourceEnum

from apps.fyle.models import ExpenseGroupSettings
from apps.sage_intacct.actions import update_last_export_details
from apps.mappings.helpers import get_project_billable_field_detail_key, is_project_billable_sync_allowed
from apps.workspaces.apis.export_settings.helpers import clear_workspace_errors_on_export_type_change
from fyle_integrations_imports.models import ImportLog
from apps.workspaces.models import Configuration, LastExportDetail
from workers.helpers import RoutingKeyEnum, WorkerActionEnum, publish_to_rabbitmq

logger = logging.getLogger(__name__)
logger.level = logging.INFO


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

        # Sync project billable on export type change
        if self.__should_sync_billable_status():
            billable_field = get_project_billable_field_detail_key(self.__workspace_id)
            payload = {
                'workspace_id': self.__workspace_id,
                'action': WorkerActionEnum.SYNC_PROJECT_BILLABLE_TO_FYLE.value,
                'data': {
                    'workspace_id': self.__workspace_id,
                    'billable_field': billable_field
                }
            }
            publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)
            logger.info(f'Triggered project billable sync for workspace {self.__workspace_id}')

    def __should_sync_billable_status(self) -> bool:
        """
        Check if we need to sync billable status to Fyle.
        """
        # Must have project import enabled and a valid billable field
        if not is_project_billable_sync_allowed(workspace_id=self.__workspace_id):
            return False

        # If old config exists, only sync if export types changed
        if self.__old_configurations:
            old_reimb = self.__old_configurations.get('reimbursable_expenses_object')
            old_ccc = self.__old_configurations.get('corporate_credit_card_expenses_object')
            new_reimb = self.__configuration.reimbursable_expenses_object
            new_ccc = self.__configuration.corporate_credit_card_expenses_object

            if old_reimb != new_reimb or old_ccc != new_ccc:
                return True

        return False

    def post_save_expense_group_settings(self, expense_group_settings_instance: ExpenseGroupSettings) -> None:
        existing_expense_group_setting = self.__old_configurations.get('expense_group_settings')

        if existing_expense_group_setting:
            configuration = Configuration.objects.filter(workspace_id=self.__workspace_id).first()
            if configuration:
                if configuration.reimbursable_expenses_object and existing_expense_group_setting.expense_state != expense_group_settings_instance.expense_state and existing_expense_group_setting.expense_state == ExpenseStateEnum.PAID and expense_group_settings_instance.expense_state == ExpenseStateEnum.PAYMENT_PROCESSING:
                    logger.info(f'Reimbursable expense state changed from {existing_expense_group_setting.expense_state} to {expense_group_settings_instance.expense_state} for workspace {self.__workspace_id}, so pulling the data from Fyle')
                    payload = {
                        'workspace_id': self.__workspace_id,
                        'action': WorkerActionEnum.CREATE_EXPENSE_GROUP.value,
                        'data': {
                            'workspace_id': self.__workspace_id,
                            'fund_source': [FundSourceEnum.PERSONAL],
                            'task_log': None,
                            'imported_from': ExpenseImportSourceEnum.CONFIGURATION_UPDATE
                        }
                    }
                    publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.EXPORT_P1.value)

                if configuration.corporate_credit_card_expenses_object and existing_expense_group_setting.ccc_expense_state != expense_group_settings_instance.ccc_expense_state and existing_expense_group_setting.ccc_expense_state == ExpenseStateEnum.PAID and expense_group_settings_instance.ccc_expense_state == ExpenseStateEnum.APPROVED:
                    logger.info(f'Corporate credit card expense state changed from {existing_expense_group_setting.ccc_expense_state} to {expense_group_settings_instance.ccc_expense_state} for workspace {self.__workspace_id}, so pulling the data from Fyle')
                    payload = {
                        'workspace_id': self.__workspace_id,
                        'action': WorkerActionEnum.CREATE_EXPENSE_GROUP.value,
                        'data': {
                            'workspace_id': self.__workspace_id,
                            'fund_source': [FundSourceEnum.CCC],
                            'task_log': None,
                            'imported_from': ExpenseImportSourceEnum.CONFIGURATION_UPDATE
                        }
                    }
                    publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.EXPORT_P1.value)
