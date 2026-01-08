import logging
from datetime import datetime, timezone

from django_q.models import Schedule
from django.utils.module_loading import import_string
from fyle.platform.exceptions import InternalServerError
from fyle_integrations_platform_connector import PlatformConnector
from fyle_accounting_mappings.helpers import EmployeesAutoMappingHelper
from fyle.platform.exceptions import InvalidTokenError as FyleInvalidTokenError
from fyle_accounting_mappings.models import CategoryMapping, EmployeeMapping, MappingSetting
from sageintacctsdk.exceptions import InvalidTokenError, NoPrivilegeError, WrongParamsError
from intacctsdk.exceptions import (
    BadRequestError as IntacctRESTBadRequestError,
    InvalidTokenError as IntacctRESTInvalidTokenError,
    InternalServerError as IntacctRESTInternalServerError
)

from apps.tasks.models import Error
from apps.mappings.models import GeneralMapping
from apps.mappings.constants import SYNC_METHODS
from apps.fyle.models import DependentFieldSetting
from fyle_integrations_imports.models import ImportLog
from fyle_integrations_imports.dataclasses import TaskSetting
from apps.sage_intacct.helpers import get_sage_intacct_connection
from apps.sage_intacct.enums import SageIntacctRestConnectionTypeEnum
from fyle_intacct_api.utils import invalidate_sage_intacct_credentials
from fyle_integrations_imports.queues import chain_import_fields_to_fyle
from workers.helpers import RoutingKeyEnum, WorkerActionEnum, publish_to_rabbitmq
from apps.mappings.helpers import get_project_billable_field_detail_key, is_project_billable_sync_allowed
from apps.workspaces.models import (
    Configuration,
    FeatureConfig,
    FyleCredential,
    SageIntacctCredential,
)

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def get_mapped_attributes_ids(source_attribute_type: str, destination_attribute_type: str, errored_attribute_ids: list[int]) -> list[int]:
    """
    Get Mapped Attributes Ids
    :param source_attribute_type: Source Attribute Type
    :param destination_attribute_type: Destination Attribute Type
    :param errored_attribute_ids: Errored Attribute Ids
    :return: List of Mapped Attribute Ids
    """
    mapped_attribute_ids = []

    if source_attribute_type == "EMPLOYEE":
        params = {
            'source_employee_id__in': errored_attribute_ids,
        }

        if destination_attribute_type == "EMPLOYEE":
            params['destination_employee_id__isnull'] = False
        else:
            params['destination_vendor_id__isnull'] = False
        mapped_attribute_ids: list[int] = EmployeeMapping.objects.filter(
            **params
        ).values_list('source_employee_id', flat=True)

    return mapped_attribute_ids


def resolve_expense_attribute_errors(
    source_attribute_type: str,
    workspace_id: int,
    destination_attribute_type: str = None
) -> None:
    """
    Resolve Expense Attribute Errors
    :param source_attribute_type: Source Attribute Type
    :param workspace_id: Workspace Id
    :param destination_attribute_type: Destination Attribute Type
    :return: None
    """
    errored_attribute_ids: list[int] = Error.objects.filter(
        is_resolved=False,
        workspace_id=workspace_id,
        type='{}_MAPPING'.format(source_attribute_type)
    ).values_list('expense_attribute_id', flat=True)

    if errored_attribute_ids:
        mapped_attribute_ids = get_mapped_attributes_ids(source_attribute_type, destination_attribute_type, errored_attribute_ids)

        if mapped_attribute_ids:
            Error.objects.filter(expense_attribute_id__in=mapped_attribute_ids).update(is_resolved=True, updated_at=datetime.now(timezone.utc))


def auto_map_employees(workspace_id: int) -> None:
    """
    Auto Map Employees
    :param workspace_id: Workspace Id
    :return: None
    """
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    employee_mapping_preference = configuration.auto_map_employees

    destination_type = configuration.employee_field_mapping

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    try:
        platform = PlatformConnector(fyle_credentials=fyle_credentials)
        sage_intacct_connection = get_sage_intacct_connection(
            workspace_id=workspace_id,
            connection_type=SageIntacctRestConnectionTypeEnum.SYNC.value
        )

        platform.employees.sync()
        if destination_type == 'EMPLOYEE':
            sage_intacct_connection.sync_employees()
        else:
            sage_intacct_connection.sync_vendors()

        EmployeesAutoMappingHelper(workspace_id, destination_type, employee_mapping_preference).reimburse_mapping()
        resolve_expense_attribute_errors(
            source_attribute_type="EMPLOYEE",
            workspace_id=workspace_id,
            destination_attribute_type=destination_type,
        )

    except SageIntacctCredential.DoesNotExist:
        logger.info('Sage Intacct credentials does not exist workspace_id - {0}'.format(workspace_id))

    except InvalidTokenError:
        invalidate_sage_intacct_credentials(workspace_id)
        logger.info('Invalid Sage Intacct Token Error for workspace_id - {0}'.format(workspace_id))

    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle')

    except (WrongParamsError, InternalServerError) as e:
        logger.info('Error while syncing employee/vendor from Sage Intacct in workspace - %s %s', workspace_id, e)

    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')

    except IntacctRESTInvalidTokenError:
        invalidate_sage_intacct_credentials(workspace_id)
        logger.info('Invalid Sage Intacct REST Token Error for workspace_id - {0}'.format(workspace_id))

    except (IntacctRESTBadRequestError, IntacctRESTInternalServerError) as e:
        logger.info('REST API error while syncing employee/vendor from Sage Intacct in workspace - %s %s', workspace_id, e)

    except Exception:
        logger.exception('Error while auto mapping employees in workspace - %s', workspace_id)


def auto_map_accounting_fields(workspace_id: int) -> None:
    """
    Auto Map Accounting Fields
    :param employee_mapping_preference: Employee Mapping Preference
    :param workspace_id: Workspace Id
    :return: None
    """
    configuration = Configuration.objects.filter(workspace_id=workspace_id).first()
    if not configuration:
        return

    if configuration.auto_map_employees:
        payload = {
            'workspace_id': workspace_id,
            'action': WorkerActionEnum.AUTO_MAP_EMPLOYEES.value,
            'data': {
                'workspace_id': workspace_id
            }
        }
        publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)

    if (
        configuration.auto_map_employees
        and configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION'
    ):
        payload = {
            'workspace_id': workspace_id,
            'action': WorkerActionEnum.AUTO_MAP_CHARGE_CARD_ACCOUNT.value,
            'data': {
                'workspace_id': workspace_id
            }
        }
        publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)


def schedule_auto_map_accounting_fields(workspace_id: int) -> None:
    """
    Schedule Auto Map Accounting Fields to Fyle Fields
    :param workspace_id: Workspace Id
    :return: None
    """
    Schedule.objects.update_or_create(
        func='apps.mappings.tasks.auto_map_accounting_fields',
        args='{}'.format(workspace_id),
        defaults={
            'schedule_type': Schedule.MINUTES,
            'minutes': 24 * 60,
            'next_run': datetime.now()
        }
    )


def auto_map_charge_card_account(workspace_id: int) -> None:
    """
    Auto Map Charge Card Account
    :param workspace_id: Workspace Id
    :return: None
    """
    general_mappings = GeneralMapping.objects.filter(workspace_id=workspace_id).first()
    if not (general_mappings and general_mappings.default_charge_card_id):
        return

    default_charge_card_id = general_mappings.default_charge_card_id

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    try:
        platform = PlatformConnector(fyle_credentials=fyle_credentials)

        platform.employees.sync()
        EmployeesAutoMappingHelper(workspace_id, 'CHARGE_CARD_NUMBER').ccc_mapping(
            default_charge_card_id, attribute_type='CHARGE_CARD_NUMBER'
        )
    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle in workspace - %s', workspace_id)
    except InternalServerError:
        logger.info('Fyle Internal Server Error in workspace - %s', workspace_id)


def sync_sage_intacct_attributes(sageintacct_attribute_type: str, workspace_id: int) -> None:
    """
    Sync Sage Intacct Attributes
    :param sageintacct_attribute_type: Sage Intacct Attribute Type
    :param workspace_id: Workspace Id
    :return: None
    """
    sage_intacct_connection = get_sage_intacct_connection(
        workspace_id=workspace_id,
        connection_type=SageIntacctRestConnectionTypeEnum.SYNC.value
    )

    if sageintacct_attribute_type == 'LOCATION':
        sage_intacct_connection.sync_locations()

    elif sageintacct_attribute_type == 'PROJECT':
        sage_intacct_connection.sync_projects()

    elif sageintacct_attribute_type == 'DEPARTMENT':
        sage_intacct_connection.sync_departments()

    elif sageintacct_attribute_type == 'VENDOR':
        sage_intacct_connection.sync_vendors()

    elif sageintacct_attribute_type == 'CLASS':
        sage_intacct_connection.sync_classes()

    elif sageintacct_attribute_type == 'TAX_DETAIL':
        sage_intacct_connection.sync_tax_details()

    elif sageintacct_attribute_type == 'ITEM':
        sage_intacct_connection.sync_items()

    elif sageintacct_attribute_type == 'COST_TYPE':
        sage_intacct_connection.sync_cost_types()

    elif sageintacct_attribute_type == 'COST_CODE':
        sage_intacct_connection.sync_cost_codes()

    elif sageintacct_attribute_type == 'CUSTOMER':
        sage_intacct_connection.sync_customers()

    elif sageintacct_attribute_type == 'ALLOCATION':
        sage_intacct_connection.sync_allocations()

    else:
        sage_intacct_connection.sync_user_defined_dimensions()


def construct_tasks_and_chain_import_fields_to_fyle(workspace_id: int) -> None:
    """
    Initiate the Import of dimensions to Fyle
    :param workspace_id: Workspace Id
    :return: None

    Schedule will hit this func, if we want to process things via worker,
    we can publish to rabbitmq else chain it as usual.
    """
    feature_configs = FeatureConfig.objects.get(workspace_id=workspace_id)
    if feature_configs.import_via_rabbitmq:
        payload = {
            'workspace_id': workspace_id,
            'action': WorkerActionEnum.IMPORT_DIMENSIONS_TO_FYLE.value,
            'data': {
                'workspace_id': workspace_id,
                'run_in_rabbitmq_worker': True
            }
        }
        publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)
    else:
        initiate_import_to_fyle(workspace_id=workspace_id)


def initiate_import_to_fyle(workspace_id: int, run_in_rabbitmq_worker: bool = False) -> None:
    """
    Initiate import fields to Fyle
    :param workspace_id: Workspace Id
    :return: None
    """
    mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    dependent_fields = DependentFieldSetting.objects.filter(workspace_id=workspace_id, is_import_enabled=True).first()

    try:
        credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace_id=workspace_id)
    except SageIntacctCredential.DoesNotExist:
        logger.info('Active Sage Intacct credentials not found for workspace_id - %s', workspace_id)
        return

    project_import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').first()
    # We'll only sync PROJECT and Dependent Fields together in one run
    is_sync_allowed = import_string('apps.mappings.helpers.is_project_sync_allowed')(project_import_log)

    custom_field_mapping_settings = []
    project_mapping = None

    for setting in mapping_settings:
        if setting.is_custom:
            custom_field_mapping_settings.append(setting)
        if setting.source_field == 'PROJECT':
            project_mapping = setting

    task_settings: TaskSetting = {
        'import_tax': None,
        'import_vendors_as_merchants': None,
        'import_categories': None,
        'import_items': None,
        'mapping_settings': [],
        'credentials': credentials,
        'sdk_connection_string': 'apps.sage_intacct.helpers.get_sage_intacct_connection_from_imports_module',
        'custom_properties': None,
        'import_dependent_fields': None
    }

    if configuration.import_tax_codes:
        task_settings['import_tax'] = {
            'destination_field': 'TAX_DETAIL',
            'destination_sync_methods': [SYNC_METHODS['TAX_DETAIL']],
            'is_auto_sync_enabled': False,
            'is_3d_mapping': False,
        }

    if configuration.import_categories:
        destination_sync_methods = []
        destination_field = None
        if configuration.reimbursable_expenses_object == 'EXPENSE_REPORT' or \
            configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            destination_field = 'EXPENSE_TYPE'
            destination_sync_methods.append(SYNC_METHODS['ACCOUNT'])
            destination_sync_methods.append(SYNC_METHODS['EXPENSE_TYPE'])
        else:
            destination_field = 'ACCOUNT'
            destination_sync_methods.append(SYNC_METHODS['ACCOUNT'])

        task_settings['import_categories'] = {
            'destination_field': destination_field,
            'destination_sync_methods': destination_sync_methods,
            'is_auto_sync_enabled': True,
            'is_3d_mapping': True,
            'charts_of_accounts': [],
            'prepend_code_to_name': True if destination_field in configuration.import_code_fields else False,
            'import_without_destination_id': False,
            'use_mapping_table': False
        }

    if configuration.import_vendors_as_merchants:
        task_settings['import_vendors_as_merchants'] = {
            'destination_field': 'VENDOR',
            'destination_sync_methods': ['vendors'],
            'is_auto_sync_enabled': True,
            'is_3d_mapping': False,
            'prepend_code_to_name': False,
        }

    for setting in mapping_settings:
        if (
            setting.source_field in ['PROJECT', 'COST_CENTER']
            or setting.is_custom
        ):
            task_setting = {
                'source_field': setting.source_field,
                'destination_field': setting.destination_field,
                'destination_sync_methods': [SYNC_METHODS.get(setting.destination_field, 'user_defined_dimensions')],
                'is_auto_sync_enabled': True,
                'is_custom': setting.is_custom,
                'import_without_destination_id': False,
                'prepend_code_to_name': True if setting.destination_field in configuration.import_code_fields else False
            }

            if is_project_billable_sync_allowed(workspace_id=workspace_id):
                billable_field_detail_key = get_project_billable_field_detail_key(workspace_id=workspace_id)
                task_setting['project_billable_field_detail_key'] = billable_field_detail_key

            task_settings['mapping_settings'].append(task_setting)

    if project_mapping and is_sync_allowed and dependent_fields and dependent_fields.is_import_enabled:
        task_settings['import_dependent_fields'] = {
            'func': 'apps.sage_intacct.dependent_fields.import_dependent_fields_to_fyle',
            'args': {
                'workspace_id': workspace_id
            }
        }

    chain_import_fields_to_fyle(
        workspace_id=workspace_id,
        task_settings=task_settings,
        run_in_rabbitmq_worker=run_in_rabbitmq_worker
    )


def check_and_create_ccc_mappings(workspace_id: int) -> None:
    """
    Check and Create CCC Mappings
    :param workspace_id: Workspace Id
    :return: None
    """
    configuration = Configuration.objects.filter(workspace_id=workspace_id).first()
    if configuration and (
        configuration.reimbursable_expenses_object == 'EXPENSE_REPORT'
        and (configuration.corporate_credit_card_expenses_object and configuration.corporate_credit_card_expenses_object not in ['JOURNAL_ENTRY', 'BILL', 'CHARGE_CARD_TRANSACTION'])
    ):
        logger.info('Creating CCC Mappings for workspace_id - %s', workspace_id)
        CategoryMapping.bulk_create_ccc_category_mappings(workspace_id)
