import logging
from datetime import datetime, timezone

from django_q.models import Schedule
from django.utils.module_loading import import_string

from fyle_accounting_mappings.models import EmployeeMapping, MappingSetting
from fyle_accounting_mappings.helpers import EmployeesAutoMappingHelper
from fyle_integrations_imports.dataclasses import TaskSetting
from fyle_integrations_imports.queues import chain_import_fields_to_fyle
from fyle_integrations_platform_connector import PlatformConnector
from fyle.platform.exceptions import (
    InvalidTokenError as FyleInvalidTokenError,
    InternalServerError
)

from sageintacctsdk.exceptions import InvalidTokenError, NoPrivilegeError, WrongParamsError

from apps.mappings.constants import SYNC_METHODS
from fyle_integrations_imports.models import ImportLog
from apps.fyle.models import DependentFieldSetting
from apps.mappings.models import GeneralMapping
from apps.sage_intacct.utils import SageIntacctConnector
from apps.tasks.models import Error
from apps.workspaces.models import (
    SageIntacctCredential,
    FyleCredential,
    Configuration
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


def async_auto_map_employees(workspace_id: int) -> None:
    """
    Async Auto Map Employees
    :param workspace_id: Workspace Id
    :return: None
    """
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    employee_mapping_preference = configuration.auto_map_employees

    destination_type = configuration.employee_field_mapping

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    try:
        platform = PlatformConnector(fyle_credentials=fyle_credentials)
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
        sage_intacct_connection = SageIntacctConnector(
            credentials_object=sage_intacct_credentials, workspace_id=workspace_id)

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

    except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct Credentials does not exist - %s', workspace_id)

    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle')

    except WrongParamsError:
        logger.info('Error while syncing employee/vendor from Sage Intacct in workspace - %s', workspace_id)

    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')


def schedule_auto_map_employees(employee_mapping_preference: str, workspace_id: int) -> None:
    """
    Schedule Auto Map Employees
    :param employee_mapping_preference: Employee Mapping Preference
    :param workspace_id: Workspace Id
    :return: None
    """
    if employee_mapping_preference:
        start_datetime = datetime.now()

        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.async_auto_map_employees',
            cluster='import',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.async_auto_map_employees',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()


def async_auto_map_charge_card_account(workspace_id: int) -> None:
    """
    Async Auto Map Charge Card Account
    :param workspace_id: Workspace Id
    :return: None
    """
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
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


def schedule_auto_map_charge_card_employees(workspace_id: int) -> None:
    """
    Schedule Auto Map Charge Card Employees
    :param workspace_id: Workspace Id
    :return: None
    """
    configuration = Configuration.objects.get(workspace_id=workspace_id)

    if (
        configuration.auto_map_employees
        and configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION'
    ):

        start_datetime = datetime.now()

        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.async_auto_map_charge_card_account',
            cluster='import',
            args='{0}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )

    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.async_auto_map_charge_card_account',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()


def sync_sage_intacct_attributes(sageintacct_attribute_type: str, workspace_id: int) -> None:
    """
    Sync Sage Intacct Attributes
    :param sageintacct_attribute_type: Sage Intacct Attribute Type
    :param workspace_id: Workspace Id
    :return: None
    """
    sage_intacct_credentials: SageIntacctCredential = SageIntacctCredential.objects.get(workspace_id=workspace_id)

    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
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

    else:
        sage_intacct_connection.sync_user_defined_dimensions()


def construct_tasks_and_chain_import_fields_to_fyle(workspace_id: int) -> None:
    """
    Chain import fields to Fyle
    :param workspace_id: Workspace Id
    :return: None
    """
    mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    dependent_fields = DependentFieldSetting.objects.filter(workspace_id=workspace_id, is_import_enabled=True).first()
    credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)

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
        'sdk_connection_string': 'apps.sage_intacct.utils.SageIntacctConnector',
        'custom_properties': None,
        'import_dependent_fields': None
    }

    if configuration.import_tax_codes:
        task_settings['import_tax'] = {
            'destination_field': 'TAX_DETAIL',
            'destination_sync_methods': SYNC_METHODS['TAX_DETAIL'],
            'is_auto_sync_enabled': False,
            'is_3d_mapping': False,
        }

    if configuration.import_categories:
        if configuration.reimbursable_expenses_object == 'EXPENSE_REPORT' or \
            configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            destination_field = 'EXPENSE_TYPE'
        else:
            destination_field = 'ACCOUNT'

        task_settings['import_categories'] = {
            'destination_field': destination_field,
            'destination_sync_methods': [SYNC_METHODS[destination_field]],
            'is_auto_sync_enabled': True,
            'is_3d_mapping': True,
            'charts_of_accounts': [],
            'prepend_code_to_name': True if destination_field in configuration.import_code_fields else False,
            'import_without_destination_id': True,
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
            task_settings['mapping_settings'].append({
                'source_field': setting.source_field,
                'destination_field': setting.destination_field,
                'destination_sync_methods': [SYNC_METHODS[setting.destination_field]],
                'is_auto_sync_enabled': True,
                'is_custom': setting.is_custom,
                'import_without_destination_id': True,
                'prepend_code_to_name': True if setting.destination_field in configuration.import_code_fields else False
            })

    if project_mapping and is_sync_allowed and dependent_fields and dependent_fields.is_import_enabled:
        task_settings['import_dependent_fields'] = {
            'func': 'apps.sage_intacct.dependent_fields.import_dependent_fields_to_fyle',
            'args': {
                'workspace_id': workspace_id
            }
        }

    chain_import_fields_to_fyle(workspace_id, task_settings)
