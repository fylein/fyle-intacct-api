import logging
from datetime import datetime, timezone

from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum, ExpenseStateEnum, FundSourceEnum
from fyle_accounting_mappings.models import ExpenseAttribute

from apps.fyle.models import ExpenseGroupSettings
from apps.sage_intacct.actions import update_last_export_details
from apps.workspaces.apis.export_settings.helpers import clear_workspace_errors_on_export_type_change
from apps.workspaces.models import Configuration, LastExportDetail
from fyle_integrations_imports.models import ImportLog
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

    def post_save_expense_group_settings(self, expense_group_settings_instance: ExpenseGroupSettings):
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
