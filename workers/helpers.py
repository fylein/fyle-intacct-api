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
    CREATE_EXPENSE_GROUP = 'EXPORT.P1.CREATE_EXPENSE_GROUP'
    UPDATE_WORKSPACE_NAME = 'UTILITY.UPDATE_WORKSPACE_NAME'
    EXPENSE_STATE_CHANGE = 'EXPORT.P1.EXPENSE_STATE_CHANGE'
    IMPORT_DIMENSIONS_TO_FYLE = 'IMPORT.IMPORT_DIMENSIONS_TO_FYLE'
    CREATE_ADMIN_SUBSCRIPTION = 'UTILITY.CREATE_ADMIN_SUBSCRIPTION'
    RESET_COST_TYPE_IMPORT_FLAG = 'IMPORT.RESET_COST_TYPE_IMPORT_FLAG'
    SYNC_SAGE_INTACCT_DIMENSION = 'IMPORT.SYNC_SAGE_INTACCT_DIMENSION'
    BACKGROUND_SCHEDULE_EXPORT = 'EXPORT.P1.BACKGROUND_SCHEDULE_EXPORT'
    CHECK_AND_CREATE_CCC_MAPPINGS = 'IMPORT.CHECK_AND_CREATE_CCC_MAPPINGS'
    HANDLE_FYLE_REFRESH_DIMENSION = 'IMPORT.HANDLE_FYLE_REFRESH_DIMENSION'
    EXPENSE_UPDATED_AFTER_APPROVAL = 'UTILITY.EXPENSE_UPDATED_AFTER_APPROVAL'
    CHECK_INTERVAL_AND_SYNC_FYLE_DIMENSION = 'IMPORT.CHECK_INTERVAL_AND_SYNC_FYLE_DIMENSION'
    CHECK_INTERVAL_AND_SYNC_SAGE_INTACCT_DIMENSION = 'IMPORT.CHECK_INTERVAL_AND_SYNC_SAGE_INTACCT_DIMENSION'


QUEUE_BINDKEY_MAP = {
    'intacct_import': RoutingKeyEnum.IMPORT,
    'intacct_utility': RoutingKeyEnum.UTILITY,
    'intacct_export.p0': RoutingKeyEnum.EXPORT_P0,
    'intacct_export.p1': RoutingKeyEnum.EXPORT_P1
}


ACTION_METHOD_MAP = {
    WorkerActionEnum.DIRECT_EXPORT: 'apps.fyle.tasks.import_and_export_expenses',
    WorkerActionEnum.DASHBOARD_SYNC: 'apps.workspaces.actions.export_to_intacct',
    WorkerActionEnum.CREATE_EXPENSE_GROUP: 'apps.fyle.tasks.create_expense_groups',
    WorkerActionEnum.EXPENSE_STATE_CHANGE: 'apps.fyle.tasks.import_and_export_expenses',
    WorkerActionEnum.UPDATE_WORKSPACE_NAME: 'apps.workspaces.tasks.update_workspace_name',
    WorkerActionEnum.BACKGROUND_SCHEDULE_EXPORT: 'apps.workspaces.actions.export_to_intacct',
    WorkerActionEnum.SYNC_SAGE_INTACCT_DIMENSION: 'apps.sage_intacct.helpers.sync_dimensions',
    WorkerActionEnum.IMPORT_DIMENSIONS_TO_FYLE: 'apps.mappings.tasks.initiate_import_to_fyle',
    WorkerActionEnum.HANDLE_FYLE_REFRESH_DIMENSION: 'apps.fyle.helpers.handle_refresh_dimensions',
    WorkerActionEnum.CREATE_ADMIN_SUBSCRIPTION: 'apps.workspaces.tasks.create_admin_subscriptions',
    WorkerActionEnum.EXPENSE_UPDATED_AFTER_APPROVAL: 'apps.fyle.tasks.update_non_exported_expenses',
    WorkerActionEnum.CHECK_AND_CREATE_CCC_MAPPINGS: 'apps.mappings.tasks.check_and_create_ccc_mappings',
    WorkerActionEnum.CHECK_INTERVAL_AND_SYNC_FYLE_DIMENSION: 'apps.fyle.helpers.check_interval_and_sync_dimension',
    WorkerActionEnum.RESET_COST_TYPE_IMPORT_FLAG: 'apps.sage_intacct.dependent_fields.reset_flag_and_disable_cost_type_field',
    WorkerActionEnum.CHECK_INTERVAL_AND_SYNC_SAGE_INTACCT_DIMENSION: 'apps.sage_intacct.helpers.check_interval_and_sync_dimension'
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
