from enum import Enum

from fyle_accounting_library.rabbitmq.data_class import RabbitMQData
from fyle_accounting_library.rabbitmq.enums import RabbitMQExchangeEnum
from fyle_accounting_library.rabbitmq.connector import RabbitMQConnection


class RoutingKeyEnum(str, Enum):
    """
    Routing key enum
    """
    IMPORT = 'IMPORT.*'
    UTILITY = 'UTILITY.*'
    EXPORT_P0 = 'EXPORT.P0.*'
    EXPORT_P1 = 'EXPORT.P1.*'


class WorkerActionEnum(str, Enum):
    """
    Worker action enum
    """
    DIRECT_EXPORT = 'EXPORT.P0.DIRECT_EXPORT'
    DASHBOARD_SYNC = 'EXPORT.P0.DASHBOARD_SYNC'
    CREATE_AP_PAYMENT = 'EXPORT.P1.CREATE_AP_PAYMENT'
    AUTO_MAP_EMPLOYEES = 'IMPORT.AUTO_MAP_EMPLOYEES'
    CREATE_EXPENSE_GROUP = 'EXPORT.P1.CREATE_EXPENSE_GROUP'
    UPDATE_WORKSPACE_NAME = 'UTILITY.UPDATE_WORKSPACE_NAME'
    EXPENSE_STATE_CHANGE = 'EXPORT.P1.EXPENSE_STATE_CHANGE'
    RE_EXPORT_STUCK_EXPORTS = 'EXPORT.P1.RE_EXPORT_STUCK_EXPORTS'
    IMPORT_DIMENSIONS_TO_FYLE = 'IMPORT.IMPORT_DIMENSIONS_TO_FYLE'
    CREATE_ADMIN_SUBSCRIPTION = 'UTILITY.CREATE_ADMIN_SUBSCRIPTION'
    TRIGGER_EMAIL_NOTIFICATION = 'UTILITY.TRIGGER_EMAIL_NOTIFICATION'
    RESET_COST_TYPE_IMPORT_FLAG = 'IMPORT.RESET_COST_TYPE_IMPORT_FLAG'
    SYNC_SAGE_INTACCT_DIMENSION = 'IMPORT.SYNC_SAGE_INTACCT_DIMENSION'
    BACKGROUND_SCHEDULE_EXPORT = 'EXPORT.P1.BACKGROUND_SCHEDULE_EXPORT'
    AUTO_MAP_CHARGE_CARD_ACCOUNT = 'IMPORT.AUTO_MAP_CHARGE_CARD_ACCOUNT'
    CHECK_AND_CREATE_CCC_MAPPINGS = 'IMPORT.CHECK_AND_CREATE_CCC_MAPPINGS'
    HANDLE_FYLE_REFRESH_DIMENSION = 'IMPORT.HANDLE_FYLE_REFRESH_DIMENSION'
    EXPENSE_UPDATED_AFTER_APPROVAL = 'UTILITY.EXPENSE_UPDATED_AFTER_APPROVAL'
    CREATE_SAGE_INTACCT_REIMBURSEMENT = 'EXPORT.P1.CREATE_SAGE_INTACCT_REIMBURSEMENT'
    CHECK_INTERVAL_AND_SYNC_FYLE_DIMENSION = 'IMPORT.CHECK_INTERVAL_AND_SYNC_FYLE_DIMENSION'
    CHECK_INTERVAL_AND_SYNC_SAGE_INTACCT_DIMENSION = 'IMPORT.CHECK_INTERVAL_AND_SYNC_SAGE_INTACCT_DIMENSION'
    CHECK_SAGE_INTACCT_OBJECT_STATUS_AND_PROCESS_FYLE_REIMBURSEMENTS = 'EXPORT.P1.CHECK_SAGE_INTACCT_OBJECT_STATUS_AND_PROCESS_FYLE_REIMBURSEMENTS'
    EXPENSE_ADDED_EJECTED_FROM_REPORT = 'UTILITY.EXPENSE_ADDED_EJECTED_FROM_REPORT'
    SYNC_PROJECT_BILLABLE_TO_FYLE = 'IMPORT.SYNC_PROJECT_BILLABLE_TO_FYLE'


QUEUE_BINDKEY_MAP = {
    'intacct_import': RoutingKeyEnum.IMPORT,
    'intacct_utility': RoutingKeyEnum.UTILITY,
    'intacct_export.p0': RoutingKeyEnum.EXPORT_P0,
    'intacct_export.p1': RoutingKeyEnum.EXPORT_P1
}


ACTION_METHOD_MAP = {
    WorkerActionEnum.DIRECT_EXPORT: 'apps.fyle.tasks.import_and_export_expenses',
    WorkerActionEnum.DASHBOARD_SYNC: 'apps.workspaces.actions.export_to_intacct',
    WorkerActionEnum.AUTO_MAP_EMPLOYEES: 'apps.mappings.tasks.auto_map_employees',
    WorkerActionEnum.CREATE_EXPENSE_GROUP: 'apps.fyle.tasks.create_expense_groups',
    WorkerActionEnum.CREATE_AP_PAYMENT: 'apps.sage_intacct.tasks.create_ap_payment',
    WorkerActionEnum.EXPENSE_STATE_CHANGE: 'apps.fyle.tasks.import_and_export_expenses',
    WorkerActionEnum.UPDATE_WORKSPACE_NAME: 'apps.workspaces.tasks.update_workspace_name',
    WorkerActionEnum.RE_EXPORT_STUCK_EXPORTS: 'apps.internal.tasks.retrigger_stuck_exports',
    WorkerActionEnum.BACKGROUND_SCHEDULE_EXPORT: 'apps.workspaces.actions.export_to_intacct',
    WorkerActionEnum.IMPORT_DIMENSIONS_TO_FYLE: 'apps.mappings.tasks.initiate_import_to_fyle',
    WorkerActionEnum.SYNC_SAGE_INTACCT_DIMENSION: 'apps.sage_intacct.helpers.sync_dimensions',
    WorkerActionEnum.HANDLE_FYLE_REFRESH_DIMENSION: 'apps.fyle.helpers.handle_refresh_dimensions',
    WorkerActionEnum.CREATE_ADMIN_SUBSCRIPTION: 'apps.workspaces.tasks.create_admin_subscriptions',
    WorkerActionEnum.TRIGGER_EMAIL_NOTIFICATION: 'apps.workspaces.tasks.trigger_email_notification',
    WorkerActionEnum.EXPENSE_UPDATED_AFTER_APPROVAL: 'apps.fyle.tasks.update_non_exported_expenses',
    WorkerActionEnum.AUTO_MAP_CHARGE_CARD_ACCOUNT: 'apps.mappings.tasks.auto_map_charge_card_account',
    WorkerActionEnum.CHECK_AND_CREATE_CCC_MAPPINGS: 'apps.mappings.tasks.check_and_create_ccc_mappings',
    WorkerActionEnum.CHECK_INTERVAL_AND_SYNC_FYLE_DIMENSION: 'apps.fyle.helpers.check_interval_and_sync_dimension',
    WorkerActionEnum.CREATE_SAGE_INTACCT_REIMBURSEMENT: 'apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
    WorkerActionEnum.RESET_COST_TYPE_IMPORT_FLAG: 'apps.sage_intacct.dependent_fields.reset_flag_and_disable_cost_type_field',
    WorkerActionEnum.CHECK_INTERVAL_AND_SYNC_SAGE_INTACCT_DIMENSION: 'apps.sage_intacct.helpers.check_interval_and_sync_dimension',
    WorkerActionEnum.CHECK_SAGE_INTACCT_OBJECT_STATUS_AND_PROCESS_FYLE_REIMBURSEMENTS: 'apps.sage_intacct.tasks.check_sage_intacct_object_status_and_process_fyle_reimbursements',
    WorkerActionEnum.EXPENSE_ADDED_EJECTED_FROM_REPORT: 'apps.fyle.tasks.handle_expense_report_change',
    WorkerActionEnum.SYNC_PROJECT_BILLABLE_TO_FYLE: 'apps.workspaces.apis.export_settings.helpers.sync_project_billable_to_fyle',
}


def get_routing_key(queue_name: str) -> str:
    """
    Get the routing key for a given queue name
    :param queue_name: str
    :return: str
    """
    return QUEUE_BINDKEY_MAP.get(queue_name)


def publish_to_rabbitmq(payload: dict, routing_key: RoutingKeyEnum) -> None:
    """
    Publish messages to RabbitMQ
    :param: payload: dict
    :param: routing_key: RoutingKeyEnum
    :return: None
    """
    rabbitmq = RabbitMQConnection.get_instance(RabbitMQExchangeEnum.INTACCT_EXCHANGE)
    data = RabbitMQData(new=payload)
    rabbitmq.publish(routing_key, data)
