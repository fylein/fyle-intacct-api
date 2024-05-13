import logging
from datetime import datetime

from typing import List

from django_q.models import Schedule
from django_q.tasks import Chain
from fyle_integrations_platform_connector import PlatformConnector

from fyle.platform.exceptions import (
    InvalidTokenError as FyleInvalidTokenError,
    InternalServerError
)

from fyle_accounting_mappings.helpers import EmployeesAutoMappingHelper
from fyle_accounting_mappings.models import (
    MappingSetting,
    EmployeeMapping
)
from sageintacctsdk.exceptions import (
    InvalidTokenError,
    NoPrivilegeError
)
from apps.mappings.models import GeneralMapping
from apps.sage_intacct.utils import SageIntacctConnector
from apps.tasks.models import Error
from apps.workspaces.models import (
    SageIntacctCredential,
    FyleCredential,
    Configuration
)
from apps.fyle.models import DependentFieldSetting


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def get_mapped_attributes_ids(source_attribute_type: str, destination_attribute_type: str, errored_attribute_ids: List[int]):

    mapped_attribute_ids = []

    if source_attribute_type == "EMPLOYEE":
        params = {
            'source_employee_id__in': errored_attribute_ids,
        }

        if destination_attribute_type == "EMPLOYEE":
            params['destination_employee_id__isnull'] = False
        else:
            params['destination_vendor_id__isnull'] = False
        mapped_attribute_ids: List[int] = EmployeeMapping.objects.filter(
            **params
        ).values_list('source_employee_id', flat=True)

    return mapped_attribute_ids


def resolve_expense_attribute_errors(
    source_attribute_type: str, workspace_id: int, destination_attribute_type: str = None):
    """
    Resolve Expense Attribute Errors
    :return: None
    """
    errored_attribute_ids: List[int] = Error.objects.filter(
        is_resolved=False,
        workspace_id=workspace_id,
        type='{}_MAPPING'.format(source_attribute_type)
    ).values_list('expense_attribute_id', flat=True)

    if errored_attribute_ids:
        mapped_attribute_ids = get_mapped_attributes_ids(source_attribute_type, destination_attribute_type, errored_attribute_ids)

        if mapped_attribute_ids:
            Error.objects.filter(expense_attribute_id__in=mapped_attribute_ids).update(is_resolved=True)


def async_auto_map_employees(workspace_id: int):
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

    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')


def schedule_auto_map_employees(employee_mapping_preference: str, workspace_id: int):
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


def async_auto_map_charge_card_account(workspace_id: int):
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


def schedule_auto_map_charge_card_employees(workspace_id: int):
    configuration = Configuration.objects.get(workspace_id=workspace_id)

    if configuration.auto_map_employees and \
        configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':

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


def sync_sage_intacct_attributes(sageintacct_attribute_type: str, workspace_id: int):
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

    elif sageintacct_attribute_type == 'CUSTOMER':
        sage_intacct_connection.sync_customers()

    else:
        sage_intacct_connection.sync_user_defined_dimensions()


def auto_import_and_map_fyle_fields(workspace_id):
    """
    Auto import and map fyle fields
    """
    project_mapping = MappingSetting.objects.filter(
        source_field='PROJECT',
        workspace_id=workspace_id,
        import_to_fyle=True
    ).first()
    dependent_fields = DependentFieldSetting.objects.filter(workspace_id=workspace_id, is_import_enabled=True).first()

    chain = Chain()

    if project_mapping and dependent_fields:
        chain.append('apps.sage_intacct.dependent_fields.import_dependent_fields_to_fyle', workspace_id, q_options={'cluster': 'import', 'timeout': 27000})

    if chain.length() > 0:
        chain.run()
