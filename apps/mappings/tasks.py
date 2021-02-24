import logging
import traceback
from datetime import datetime, timedelta

from typing import List, Dict

from django_q.models import Schedule
from django.db.models import Q

from fylesdk import WrongParamsError
from fyle_accounting_mappings.models import Mapping, MappingSetting, ExpenseAttribute, DestinationAttribute

from apps.fyle.utils import FyleConnector
from apps.mappings.models import GeneralMapping
from apps.sage_intacct.utils import SageIntacctConnector
from apps.workspaces.models import SageIntacctCredential, FyleCredential, WorkspaceGeneralSettings

logger = logging.getLogger(__name__)


def create_fyle_projects_payload(projects: List[DestinationAttribute], workspace_id: int):
    """
    Create Fyle Projects Payload from Sage Intacct Projects and Customers
    :param projects: Sage Intacct Projects
    :param workspace_id: integer id of workspace
    :return: Fyle Projects Payload
    """
    payload = []
    existing_project_names = ExpenseAttribute.objects.filter(
        attribute_type='PROJECT',
        workspace_id=workspace_id).values_list('value', flat=True)

    for project in projects:
        if project.value not in existing_project_names:
            payload.append({
                'name': project.value,
                'code': project.destination_id,
                'description': 'Sage Intacct Project - {0}, Id - {1}'.format(
                    project.value,
                    project.destination_id
                ),
                'active': True if project.active is None else project.active
            })

    return payload


def upload_projects_to_fyle(workspace_id):
    """
    Upload projects to Fyle
    """
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_credentials: SageIntacctCredential = SageIntacctCredential.objects.get(workspace_id=workspace_id)

    fyle_connection = FyleConnector(
        refresh_token=fyle_credentials.refresh_token,
        workspace_id=workspace_id
    )

    si_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials,
        workspace_id=workspace_id
    )

    fyle_connection.sync_projects()
    si_projects = si_connection.sync_projects()

    fyle_payload: List[Dict] = create_fyle_projects_payload(si_projects, workspace_id)
    if fyle_payload:
        fyle_connection.connection.Projects.post(fyle_payload)
        fyle_connection.sync_projects()

    return si_projects


def auto_create_project_mappings(workspace_id):
    """
    Create Project Mappings
    :return: mappings
    """
    si_projects = upload_projects_to_fyle(workspace_id=workspace_id)
    project_mappings = []

    try:
        for project in si_projects:
            mapping = Mapping.create_or_update_mapping(
                source_type='PROJECT',
                destination_type='PROJECT',
                source_value=project.value,
                destination_value=project.value,
                destination_id=project.destination_id,
                workspace_id=workspace_id
            )
            project_mappings.append(mapping)

        return project_mappings

    except WrongParamsError as exception:
        logger.error(
            'Error while creating projects workspace_id - %s in Fyle %s %s',
            workspace_id, exception.message, {'error': exception.response}
        )

    except Exception:
        error = traceback.format_exc()
        error = {
            'error': error
        }
        logger.error(
            'Error while creating projects workspace_id - %s error: %s',
            workspace_id, error
        )


def schedule_projects_creation(import_projects, workspace_id):
    if import_projects:
        start_datetime = datetime.now()
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.auto_create_project_mappings',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.auto_create_project_mappings',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()

def filter_expense_attributes(workspace_id: int, **filters):
    return ExpenseAttribute.objects.filter(attribute_type='EMPLOYEE', workspace_id=workspace_id, **filters).all()

def auto_create_employee_mappings(source_attributes: List[ExpenseAttribute], mapping_attributes: dict):
    for source in source_attributes:
        mapping = Mapping.objects.filter(
            source_type='EMPLOYEE',
            destination_type=mapping_attributes['destination_type'],
            source__value=source.value,
            workspace_id=mapping_attributes['workspace_id']
        ).first()

        if not mapping:
            Mapping.create_or_update_mapping(
                source_type='EMPLOYEE',
                destination_type=mapping_attributes['destination_type'],
                source_value=source.value,
                destination_value=mapping_attributes['destination_value'],
                destination_id=mapping_attributes['destination_id'],
                workspace_id=mapping_attributes['workspace_id']
            )

            if mapping_attributes['destination_type'] != 'CHARGE_CARD_NUMBER':
                source.auto_mapped = True
                source.save(update_fields=['auto_mapped'])

def construct_filters_employee_mappings(employee: DestinationAttribute, employee_mapping_preference: str):
    filters = {}
    if employee_mapping_preference == 'EMAIL':
        if employee.detail and employee.detail['email']:
            filters = {
                'value__iexact': employee.detail['email']
            }

    elif employee_mapping_preference == 'NAME':
        filters = {
            'detail__full_name__iexact': employee.value
        }

    elif employee_mapping_preference == 'EMPLOYEE_CODE':
        filters = {
            'detail__employee_code__iexact': employee.value
        }

    return filters

def async_auto_map_employees(workspace_id: int):
    general_settings = WorkspaceGeneralSettings.objects.get(workspace_id=workspace_id)

    employee_mapping_preference = general_settings.auto_map_employees
    mapping_setting = MappingSetting.objects.filter(
        ~Q(destination_field='CHARGE_CARD_NUMBER'),
        source_field='EMPLOYEE', workspace_id=workspace_id
    ).first()

    destination_type = mapping_setting.destination_field

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_connection = FyleConnector(refresh_token=fyle_credentials.refresh_token, workspace_id=workspace_id)

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=sageintacct_credentials, workspace_id=workspace_id)

    fyle_connection.sync_employees()

    if destination_type == 'EMPLOYEE':
        sage_intacct_connection.sync_employees()
    else:
        sage_intacct_connection.sync_vendors()

    source_attribute = []
    employee_attributes = DestinationAttribute.objects.filter(attribute_type=destination_type,
                                                              workspace_id=workspace_id).all()

    for employee in employee_attributes:
        filters = construct_filters_employee_mappings(employee, employee_mapping_preference)
        if filters:
            filters['auto_mapped'] = False
            source_attribute = filter_expense_attributes(workspace_id, **filters)
        mapping_attributes = {
            'destination_type': destination_type,
            'destination_value': employee.value,
            'destination_id': employee.destination_id,
            'workspace_id': workspace_id
        }
        auto_create_employee_mappings(source_attribute, mapping_attributes)                       

def schedule_auto_map_employees(employee_mapping_preference: str, workspace_id: str):
    Schedule.objects.create(
        func='apps.mappings.tasks.async_auto_map_employees',
        args='"{0}", {1}'.format(employee_mapping_preference, workspace_id),
        schedule_type=Schedule.ONCE,
        next_run=datetime.now() + timedelta(minutes=5)
    )

    if employee_mapping_preference:
        start_datetime = datetime.now()
        
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.async_auto_map_employees',
            args='{0}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime + timedelta(minutes=5)
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.async_auto_map_employees',
            args='{}'.format(workspace_id)
        ).first()

    if schedule:
        schedule.delete()       


def async_auto_map_ccc_account(workspace_id: int):
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    default_ccc_account_id = general_mappings.default_charge_card_id
    default_ccc_account_name = general_mappings.default_charge_card_name
    
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_connection = FyleConnector(refresh_token=fyle_credentials.refresh_token, workspace_id=workspace_id)


    source_attributes = fyle_connection.sync_employees()

    
    mapping_attributes = {
        'destination_type': 'CHARGE_CARD_NUMBER',
        'destination_value': default_ccc_account_name,
        'destination_id': default_ccc_account_id,
        'workspace_id': workspace_id
    }

    auto_create_employee_mappings(source_attributes, mapping_attributes)


def schedule_auto_map_ccc_employees(workspace_id: int):
    general_settings = WorkspaceGeneralSettings.objects.get(workspace_id=workspace_id)

    if general_settings.auto_map_employees:
        start_datetime = datetime.now()

        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.async_auto_map_ccc_account',
            args='{0}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime + timedelta(minutes=5)
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.async_auto_map_ccc_account',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()
