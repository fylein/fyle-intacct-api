import logging
import traceback
from datetime import datetime

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

            mapping.source.auto_mapped = True
            mapping.source.auto_created = True
            mapping.source.save()

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
    sage_intacct_connection = SageIntacctConnector(credentials_object=sage_intacct_credentials, workspace_id=workspace_id)

    fyle_connection.sync_employees()
    if destination_type == 'EMPLOYEE':
        sage_intacct_connection.sync_employees()
    else:
        sage_intacct_connection.sync_vendors(workspace_id=workspace_id)

    Mapping.auto_map_employees('EMPLOYEE', destination_type, employee_mapping_preference, workspace_id)


def schedule_auto_map_employees(employee_mapping_preference: str, workspace_id: int):

    if employee_mapping_preference:
        start_datetime = datetime.now()
        
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.async_auto_map_employees',
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
    fyle_connection = FyleConnector(refresh_token=fyle_credentials.refresh_token, workspace_id=workspace_id)
    fyle_connection.sync_employees()

    Mapping.auto_map_ccc_employees('EMPLOYEE', 'CHARGE_CARD_NUMBER', default_charge_card_id, workspace_id)


def schedule_auto_map_charge_card_employees(workspace_id: int):
    general_settings = WorkspaceGeneralSettings.objects.get(workspace_id=workspace_id)

    if general_settings.auto_map_employees and general_settings.corporate_credit_card_expenses_object:
        start_datetime = datetime.now()

        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.async_auto_map_charge_card_account',
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

def create_fyle_categories_payload(categories: List[DestinationAttribute], workspace_id: int):
    """
    Create Fyle Categories Payload from Sage Intacct Expense Types / Accounts
    :param workspace_id: Workspace integer id
    :param categories: Sage Intacct Categories / Accounts
    :return: Fyle Categories Payload
    """
    payload = []

    existing_category_names = ExpenseAttribute.objects.filter(
        attribute_type='CATEGORY', workspace_id=workspace_id).values_list('value', flat=True)

    for category in categories:
        if category.value not in existing_category_names:
            payload.append({
                'name': category.value,
                'code': category.destination_id,
                'enabled': category.active
            })

    return payload

def upload_categories_to_fyle(workspace_id: int, reimbursable_expenses_object: str):
    """
    Upload categories to Fyle
    """
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
    si_credentials: SageIntacctCredential = SageIntacctCredential.objects.get(workspace_id=workspace_id)

    fyle_connection = FyleConnector(
        refresh_token=fyle_credentials.refresh_token,
        workspace_id=workspace_id
    )

    si_connection = SageIntacctConnector(
        credentials_object=si_credentials,
        workspace_id=workspace_id
    )
    fyle_connection.sync_categories(False)

    if reimbursable_expenses_object == 'EXPENSE_REPORT':
        si_attributes: List[DestinationAttribute] = si_connection.sync_expense_types()
    else:
        si_connection.sync_accounts(workspace_id)
        si_attributes: List[DestinationAttribute] = DestinationAttribute.objects.filter(
            workspace_id=workspace_id, attribute_type='ACCOUNT'
        ).all()

    fyle_payload: List[Dict] = create_fyle_categories_payload(si_attributes, workspace_id)

    if fyle_payload:
        fyle_connection.connection.Categories.post(fyle_payload)
        fyle_connection.sync_categories(False)

    return si_attributes

def create_credit_card_category_mappings(reimbursable_expenses_object,
                                         corporate_credit_card_expenses_object, workspace_id, destination):
    """
    Create credit card mappings
    """

    if reimbursable_expenses_object == 'EXPENSE_REPORT' and corporate_credit_card_expenses_object in ['BILL', 'CHARGE_CARD_TRANSACTION']:
        Mapping.create_or_update_mapping(
            source_type='CATEGORY',
            destination_type='CCC_ACCOUNT',
            source_value=destination.value,
            destination_value=destination.detail['gl_account_title'],
            destination_id=destination.detail['gl_account_no'],
            workspace_id=workspace_id
        )
    elif reimbursable_expenses_object == 'BILL' and corporate_credit_card_expenses_object in ['BILL', 'CHARGE_CARD_TRANSACTION']:
        Mapping.create_or_update_mapping(
            source_type='CATEGORY',
            destination_type='CCC_ACCOUNT',
            source_value=destination.value,
            destination_value=destination.value,
            destination_id=destination.destination_id,
            workspace_id=workspace_id
        )

def auto_create_category_mappings(workspace_id):
    """
    Create Category Mappings
    :return: mappings
    """
    general_settings: WorkspaceGeneralSettings = WorkspaceGeneralSettings.objects.get(workspace_id=workspace_id)

    reimbursable_expenses_object = general_settings.reimbursable_expenses_object
    corporate_credit_card_expenses_object = general_settings.corporate_credit_card_expenses_object

    category_mappings = []

    if reimbursable_expenses_object == 'EXPENSE_REPORT':
        reimbursable_destination_type = 'EXPENSE_TYPE'
    else:
        reimbursable_destination_type = 'ACCOUNT'

    try:
        fyle_categories = upload_categories_to_fyle(
            workspace_id=workspace_id, reimbursable_expenses_object=reimbursable_expenses_object)
        for category in fyle_categories:
            try:
                mapping = Mapping.create_or_update_mapping(
                    source_type='CATEGORY',
                    destination_type=reimbursable_destination_type,
                    source_value=category.value,
                    destination_value=category.value,
                    destination_id=category.destination_id,
                    workspace_id=workspace_id,
                )
                mapping.source.auto_mapped = True
                mapping.source.auto_created = True
                mapping.source.save()

                create_credit_card_category_mappings(
                    reimbursable_expenses_object, corporate_credit_card_expenses_object, workspace_id, category)
                category_mappings.append(mapping)

            except ExpenseAttribute.DoesNotExist:
                detail = {
                    'source_value': category.value,
                    'destination_value': category.value,
                    'destiantion_type': reimbursable_destination_type
                }
                logger.error(
                    'Error while creating categories auto mapping workspace_id - %s %s',
                    workspace_id, {'payload': detail}
                )
                raise ExpenseAttribute.DoesNotExist

        return category_mappings
    except WrongParamsError as exception:
        logger.error(
            'Error while creating categories workspace_id - %s in Fyle %s %s',
            workspace_id, exception.message, {'error': exception.response}
        )
    except Exception:
        error = traceback.format_exc()
        error = {
            'error': error
        }
        logger.error(
            'Error while creating categories workspace_id - %s error: %s',
            workspace_id, error
        )

def schedule_categories_creation(import_categories, workspace_id):
    if import_categories:
        start_datetime = datetime.now()
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.auto_create_category_mappings',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.auto_create_category_mappings',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()
