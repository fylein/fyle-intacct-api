import logging
import traceback
from datetime import datetime, timedelta
from dateutil import parser

from typing import List, Dict

from django_q.models import Schedule
from django_q.tasks import Chain
from fyle_integrations_platform_connector import PlatformConnector

from fyle.platform.exceptions import WrongParamsError, InvalidTokenError as FyleInvalidTokenError

from fyle_accounting_mappings.helpers import EmployeesAutoMappingHelper
from fyle_accounting_mappings.models import Mapping, MappingSetting, ExpenseAttribute, DestinationAttribute, \
    CategoryMapping, ExpenseField

from sageintacctsdk.exceptions import InvalidTokenError

from apps.mappings.models import GeneralMapping
from apps.sage_intacct.utils import SageIntacctConnector
from apps.workspaces.models import SageIntacctCredential, FyleCredential, Configuration
from .constants import FYLE_EXPENSE_SYSTEM_FIELDS

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def remove_duplicates(si_attributes: List[DestinationAttribute], is_dependent: bool = False):
    unique_attributes = []
    attribute_values = []

    if is_dependent:
        for attribute in si_attributes:
            # when we allow it for other types, we should explicitly fix all these
            if {attribute.detail['project_name']: attribute.value.lower()} not in attribute_values:
                unique_attributes.append(attribute)
                attribute_values.append({attribute.detail['project_name']: attribute.value.lower()})

    else:
        for attribute in si_attributes:
            if attribute.value.lower() not in attribute_values:
                unique_attributes.append(attribute)
                attribute_values.append(attribute.value.lower())

    return unique_attributes

def disable_expense_attributes(source_field, destination_field, workspace_id):

    # Get All the inactive destination attribute ids
    filter = {
        'mapping__isnull': False,
        'mapping__destination_type': destination_field
    }

    if source_field == 'CATEGORY':
        if destination_field == 'EXPENSE_TYPE':
            filter = {
                'destination_expense_head__isnull': False
            }
        elif destination_field == 'ACCOUNT':
            filter = {
                'destination_account__isnull': False
            }

    destination_attribute_ids = DestinationAttribute.objects.filter(
        attribute_type=destination_field,
        active=False,
        workspace_id=workspace_id,
        **filter
    ).values_list('id', flat=True)

    # Get all the expense attributes that are mapped to these destination_attribute_ids
    filter = {
        'mapping__destination_id__in': destination_attribute_ids
    }

    if source_field == 'CATEGORY':
        if destination_field == 'EXPENSE_TYPE':
            filter = {
                'categorymapping__destination_expense_head_id__in': destination_attribute_ids
            }
        elif destination_field == 'ACCOUNT':
            filter = {
                'categorymapping__destination_account_id__in': destination_attribute_ids
            }

    expense_attributes_to_disable = ExpenseAttribute.objects.filter(
        attribute_type=source_field,
        active=True,
        **filter
    )

    # Update active column to false for expense attributes to be disabled
    expense_attributes_ids = []
    if expense_attributes_to_disable :
        expense_attributes_ids = [expense_attribute.id for expense_attribute in expense_attributes_to_disable]
        expense_attributes_to_disable.update(active=False)

    return expense_attributes_ids

def create_fyle_projects_payload(projects: List[DestinationAttribute], existing_project_names: list,
                                 updated_projects: List[ExpenseAttribute] = None):
    """
    Create Fyle Projects Payload from Sage Intacct Projects and Customers
    :param projects: Sage Intacct Projects
    :return: Fyle Projects Payload
    """
    payload = []

    if updated_projects:
        for project in updated_projects:
            destination_id_of_project = project.mapping.first().destination.destination_id
            payload.append({
                'id': project.source_id,
                'name': project.value,
                'code': destination_id_of_project,
                'description': 'Project - {0}, Id - {1}'.format(
                    project.value,
                    destination_id_of_project
                ),
                'is_enabled': project.active
            })
    else:
        existing_project_names = [project_name.lower() for project_name in existing_project_names]
        for project in projects:
            if project.value.lower() not in existing_project_names:
                payload.append({
                    'name': project.value,
                    'code': project.destination_id,
                    'description': 'Sage Intacct Project - {0}, Id - {1}'.format(
                        project.value,
                        project.destination_id
                    ),
                    'is_enabled': True if project.active is None else project.active
                })

    return payload


def post_projects_in_batches(platform: PlatformConnector, workspace_id: int, destination_field: str):
    existing_project_names = ExpenseAttribute.objects.filter(
        attribute_type='PROJECT', workspace_id=workspace_id).values_list('value', flat=True)
    si_attributes_count = DestinationAttribute.objects.filter(
        attribute_type=destination_field, workspace_id=workspace_id).count()
    page_size = 200

    for offset in range(0, si_attributes_count, page_size):
        limit = offset + page_size
        paginated_si_attributes = DestinationAttribute.objects.filter(
            attribute_type=destination_field, workspace_id=workspace_id).order_by('value', 'id')[offset:limit]

        paginated_si_attributes = remove_duplicates(paginated_si_attributes)

        fyle_payload: List[Dict] = create_fyle_projects_payload(
            paginated_si_attributes, existing_project_names)
        if fyle_payload:
            platform.projects.post_bulk(fyle_payload)
            platform.projects.sync()

        Mapping.bulk_create_mappings(paginated_si_attributes, 'PROJECT', destination_field, workspace_id)
    
    if destination_field == 'PROJECT':
        project_ids_to_be_changed = disable_expense_attributes('PROJECT', 'PROJECT', workspace_id)
        if project_ids_to_be_changed:
            expense_attributes = ExpenseAttribute.objects.filter(id__in=project_ids_to_be_changed)
            fyle_payload: List[Dict] = create_fyle_projects_payload(projects=[], existing_project_names=[], updated_projects=expense_attributes)
            platform.projects.post_bulk(fyle_payload)
            platform.projects.sync()


def auto_create_project_mappings(workspace_id: int):
    """
    Create Project Mappings
    :return: mappings
    """
    try:
        fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)

        platform = PlatformConnector(fyle_credentials=fyle_credentials)
        platform.projects.sync()

        mapping_setting = MappingSetting.objects.get(
            source_field='PROJECT', workspace_id=workspace_id
        )

        sync_sage_intacct_attributes(mapping_setting.destination_field, workspace_id)

        post_projects_in_batches(platform, workspace_id, mapping_setting.destination_field)

    except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id)
    
    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle')
    

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
        logger.exception(
            'Error while creating projects workspace_id - %s error: %s',
            workspace_id, error
        )


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
    except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct Credentials does not exist - %s', workspace_id)
    
    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle')


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

    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    platform.employees.sync()
    EmployeesAutoMappingHelper(workspace_id, 'CHARGE_CARD_NUMBER').ccc_mapping(
        default_charge_card_id, attribute_type='CHARGE_CARD_NUMBER'
    )


def schedule_auto_map_charge_card_employees(workspace_id: int):
    configuration = Configuration.objects.get(workspace_id=workspace_id)

    if configuration.auto_map_employees and \
        configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':

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


def get_all_categories_from_fyle(platform: PlatformConnector):
    categories_generator = platform.connection.v1beta.admin.categories.list_all(query_params={
            'order': 'id.desc'
        })

    categories = []

    for response in categories_generator:
        if response.get('data'):
            categories.extend(response['data'])

    category_name_map = {}
    for category in categories:
        if category['sub_category'] and category['name'] != category['sub_category']:
                    category['name'] = '{0} / {1}'.format(category['name'], category['sub_category'])
        category_name_map[category['name'].lower()] = category

    return category_name_map


def create_fyle_categories_payload(categories: List[DestinationAttribute], category_map: Dict, updated_categories: List[ExpenseAttribute] = [], destination_type: str = None):
    """
    Create Fyle Categories Payload from Sage Intacct Expense Types / Accounts
    :param workspace_id: Workspace integer id
    :param categories: Sage Intacct Categories / Accounts
    :return: Fyle Categories Payload
    """
    payload = []

    if updated_categories:
        for category in updated_categories:
            if destination_type == 'EXPENSE_TYPE':
                destination_id_of_category = category.categorymapping.destination_expense_head.destination_id
            elif destination_type == 'ACCOUNT':
                destination_id_of_category = category.categorymapping.destination_account.destination_id
            payload.append({
                'id': category.source_id,
                'name': category.value,
                'code': destination_id_of_category,
                'is_enabled': category.active
            })
    else:
        for category in categories:
            if category.value.lower() not in category_map:
                payload.append({
                    'name': category.value,
                    'code': category.destination_id,
                    'is_enabled': category.active
                })

    return payload


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
    
    elif sageintacct_attribute_type == 'TASK':
        sage_intacct_connection.sync_tasks()
    
    elif sageintacct_attribute_type == 'COST_TYPE':
        sage_intacct_connection.sync_cost_types()

    else:
        sage_intacct_connection.sync_user_defined_dimensions()


def create_fyle_cost_centers_payload(sageintacct_attributes: List[DestinationAttribute], existing_fyle_cost_centers: list):
    """
    Create Fyle Cost Centers Payload from SageIntacct Objects
    :param workspace_id: Workspace integer id
    :param sageintacct_attributes: SageIntacct Objects
    :param fyle_attribute: Fyle Attribute
    :return: Fyle Cost Centers Payload
    """
    fyle_cost_centers_payload = []

    for si_attribute in sageintacct_attributes:
        if si_attribute.value not in existing_fyle_cost_centers:
            fyle_cost_centers_payload.append({
                'name': si_attribute.value,
                'is_enabled': True if si_attribute.active is None else si_attribute.active,
                'description': 'Cost Center - {0}, Id - {1}'.format(
                    si_attribute.value,
                    si_attribute.destination_id
                )
            })

    return fyle_cost_centers_payload


def post_cost_centers_in_batches(platform: PlatformConnector, workspace_id: int, sageintacct_attribute_type: str):
    existing_cost_center_names = ExpenseAttribute.objects.filter(
        attribute_type='COST_CENTER', workspace_id=workspace_id).values_list('value', flat=True)

    si_attributes_count = DestinationAttribute.objects.filter(
        attribute_type=sageintacct_attribute_type, workspace_id=workspace_id).count()

    page_size = 200

    for offset in range(0, si_attributes_count, page_size):
        limit = offset + page_size
        paginated_si_attributes = DestinationAttribute.objects.filter(
            attribute_type=sageintacct_attribute_type, workspace_id=workspace_id).order_by('value', 'id')[offset:limit]

        paginated_si_attributes = remove_duplicates(paginated_si_attributes)

        fyle_payload: List[Dict] = create_fyle_cost_centers_payload(
            paginated_si_attributes, existing_cost_center_names)

        if fyle_payload:
            platform.cost_centers.post_bulk(fyle_payload)
            platform.cost_centers.sync()

        Mapping.bulk_create_mappings(paginated_si_attributes, 'COST_CENTER', sageintacct_attribute_type, workspace_id)


def auto_create_cost_center_mappings(workspace_id: int):
    """
    Create Cost Center Mappings
    """
    try:
        fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)

        platform = PlatformConnector(fyle_credentials=fyle_credentials)

        mapping_setting = MappingSetting.objects.get(
            source_field='COST_CENTER', import_to_fyle=True, workspace_id=workspace_id
        )

        platform.cost_centers.sync()

        sync_sage_intacct_attributes(mapping_setting.destination_field, workspace_id)

        post_cost_centers_in_batches(platform, workspace_id, mapping_setting.destination_field)

    except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id)
    
    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle')

    except WrongParamsError as exception:
        logger.error(
            'Error while creating cost centers workspace_id - %s in Fyle %s %s',
            workspace_id, exception.message, {'error': exception.response}
        )

    except Exception:
        error = traceback.format_exc()
        error = {
            'error': error
        }
        logger.exception(
            'Error while creating cost centers workspace_id - %s error: %s',
            workspace_id, error
        )


def schedule_cost_centers_creation(import_to_fyle, workspace_id):
    if import_to_fyle:
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.auto_create_cost_center_mappings',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': datetime.now()
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.auto_create_cost_center_mappings',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()


def create_fyle_expense_custom_field_payload(sageintacct_attributes: List[DestinationAttribute], workspace_id: int,
                                            fyle_attribute: str, platform: PlatformConnector, parent_field_id: int = None, source_placeholder: str = None):
    """
    Create Fyle Expense Custom Field Payload from SageIntacct Objects
    :param workspace_id: Workspace ID
    :param sageintacct_attributes: SageIntacct Objects
    :param fyle_attribute: Fyle Attribute
    :return: Fyle Expense Custom Field Payload
    """

    fyle_expense_custom_field_options = []

    [fyle_expense_custom_field_options.append(sageintacct_attribute.value) for sageintacct_attribute in sageintacct_attributes]

    if fyle_attribute.lower() not in FYLE_EXPENSE_SYSTEM_FIELDS:
        existing_attribute = ExpenseAttribute.objects.filter(
            attribute_type=fyle_attribute, workspace_id=workspace_id).values_list('detail', flat=True).first()

        custom_field_id = None
        placeholder = None

        if existing_attribute is not None:
            placeholder = existing_attribute['placeholder'] if 'placeholder' in existing_attribute else None
            custom_field_id = existing_attribute['custom_field_id']

        fyle_attribute = fyle_attribute.replace('_', ' ').title()
        new_placeholder = None

        # Here is the explanation of what's happening in the if-else ladder below
        # source_field is the field that's save in mapping settings, this field user may or may not fill in the custom field form
        # placeholder is the field that's saved in the detail column of destination attributes
        # fyle_attribute is what we're constructing when both of these fields would not be available

        if not (source_placeholder or placeholder):
            # If source_placeholder and placeholder are both None, then we're creating adding a self constructed placeholder
            new_placeholder = 'Select {0}'.format(fyle_attribute)
        elif not source_placeholder and placeholder:
            # If source_placeholder is None but placeholder is not, then we're choosing same place holder as 1 in detail section
            new_placeholder = placeholder
        elif source_placeholder and not placeholder:
            # If source_placeholder is not None but placeholder is None, then we're choosing the placeholder as filled by user in form
            new_placeholder = source_placeholder
        else:
            # Else, we're choosing the placeholder as filled by user in form or None
            new_placeholder = source_placeholder


        # if parent field is there that means it is a dependent field
        if parent_field_id:
            expense_custom_field_payload = {
                'field_name': fyle_attribute,
                'column_name': fyle_attribute,
                'type': 'DEPENDENT_SELECT',
                'is_custom': True,
                'is_enabled': True,
                'is_mandatory': False,
                'placeholder': new_placeholder,
                'options': fyle_expense_custom_field_options,
                'parent_field_id': parent_field_id,
                'code': None,
            }
        else:
            expense_custom_field_payload = {
                'field_name': fyle_attribute,
                'type': 'SELECT',
                'is_enabled': True,
                'is_mandatory': False,
                'placeholder': new_placeholder,
                'options': fyle_expense_custom_field_options,
                'code': None
            }


        if custom_field_id:
            expense_field = platform.expense_custom_fields.get_by_id(custom_field_id)
            expense_custom_field_payload['id'] = custom_field_id
            expense_custom_field_payload['is_mandatory'] = expense_field['is_mandatory']

        return expense_custom_field_payload



def upload_dependent_field_to_fyle(
    workspace_id: int, sageintacct_attribute_type: str, fyle_attribute_type: str, parent_field_id: str, source_placeholder: str = None
):
    """
    Upload Dependent Fields To Fyle
    """

    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)
    dependent_fields = upload_attributes_to_fyle(workspace_id, sageintacct_attribute_type, fyle_attribute_type, parent_field_id, source_placeholder)
    
    expense_field_id = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type=fyle_attribute_type
    ).first().detail['custom_field_id']

    sage_intacct_attributes: List[DestinationAttribute] = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type=sageintacct_attribute_type
    )
    sage_intacct_attributes = remove_duplicates(sage_intacct_attributes, True)
    expense_attribite_type = ExpenseField.objects.get(workspace_id=workspace_id, source_field_id=parent_field_id).attribute_type

    dependent_field_values = []
    for attribute in sage_intacct_attributes:
        # If anyone can think of a better way to handle this please mention i will be happy to fix
        parent_expense_field_value = None
        if attribute.attribute_type == 'COST_TYPE':
            expense_attributes = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type=expense_attribite_type).values_list('value', flat=True)
            parent_value = DestinationAttribute.objects.filter(
                workspace_id=workspace_id,
                attribute_type='TASK',
                detail__project_name=attribute.detail['project_name'],
                detail__external_id=attribute.detail['task_id']
            ).first().value

            # parent value is combination of these two so filterig it out
            parent_expense_field_value = parent_value if parent_value in expense_attributes else None

        else:
            expense_attributes = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').values_list('value', flat=True)
            parent_value = DestinationAttribute.objects.filter(
                workspace_id=workspace_id,
                attribute_type='PROJECT',
                value=attribute.detail['project_name'],
            ).first().value

            parent_expense_field_value = parent_value if parent_value in expense_attributes else None

        if parent_expense_field_value:
            payload = {
                "parent_expense_field_id": parent_field_id,
                "parent_expense_field_value": parent_expense_field_value,
                "expense_field_id": expense_field_id,
                "expense_field_value": attribute.value,
                "is_enabled": True
            }

            dependent_field_values.append(payload)

    if dependent_field_values:
        platform.expense_fields.bulk_post_dependent_expense_field_values(dependent_field_values)
        platform.expense_fields.sync()

    return dependent_fields


def upload_attributes_to_fyle(workspace_id: int, sageintacct_attribute_type: str, fyle_attribute_type: str,
                              parent_field_id: int = None, source_placeholder: str = None):
    """
    Upload attributes to Fyle
    """

    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)

    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    sageintacct_attributes: List[DestinationAttribute] = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type=sageintacct_attribute_type
    )

    sageintacct_attributes = remove_duplicates(sageintacct_attributes)

    fyle_custom_field_payload = create_fyle_expense_custom_field_payload(
        fyle_attribute=fyle_attribute_type,
        sageintacct_attributes=sageintacct_attributes,
        workspace_id=workspace_id,
        platform=platform,
        parent_field_id=parent_field_id,
        source_placeholder=source_placeholder
    )

    if fyle_custom_field_payload:
        platform.expense_custom_fields.post(fyle_custom_field_payload)
        platform.expense_custom_fields.sync()

    return sageintacct_attributes


def auto_create_expense_fields_mappings(
    workspace_id: int, sageintacct_attribute_type: str, fyle_attribute_type: str, parent_field_id: int = None, source_placeholder: str = None
):
    """
    Create Fyle Attributes Mappings
    :return: mappings
    """
    try:
        if parent_field_id:
            fyle_attributes = upload_dependent_field_to_fyle(workspace_id=workspace_id,sageintacct_attribute_type=sageintacct_attribute_type, 
                fyle_attribute_type=fyle_attribute_type, parent_field_id=parent_field_id, source_placeholder=source_placeholder
            )
        else:
            fyle_attributes = upload_attributes_to_fyle(workspace_id=workspace_id, 
                sageintacct_attribute_type=sageintacct_attribute_type, fyle_attribute_type=fyle_attribute_type, source_placeholder=source_placeholder)

        if fyle_attributes:
            Mapping.bulk_create_mappings(fyle_attributes, fyle_attribute_type, sageintacct_attribute_type, workspace_id)

    except InvalidTokenError:
        logger.info('Invalid Token or Invalid fyle credentials - %s', workspace_id)

    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle')

    except WrongParamsError as exception:
        logger.error(
            'Error while creating %s workspace_id - %s in Fyle %s %s',
            fyle_attribute_type, workspace_id, exception.message, {'error': exception.response}
        )
    except Exception:
        error = traceback.format_exc()
        error = {
            'error': error
        }
        logger.exception(
            'Error while creating %s workspace_id - %s error: %s', fyle_attribute_type, workspace_id, error
        )


def async_auto_create_custom_field_mappings(workspace_id: str):
    mapping_settings = MappingSetting.objects.filter(
        is_custom=True, import_to_fyle=True, workspace_id=workspace_id
    ).all()

    for mapping_setting in mapping_settings:
        try:
            if mapping_setting.import_to_fyle:
                parent_field = mapping_setting.expense_field.source_field_id if mapping_setting.expense_field else None
                sync_sage_intacct_attributes(mapping_setting.destination_field, workspace_id)
                auto_create_expense_fields_mappings(
                    workspace_id, mapping_setting.destination_field, mapping_setting.source_field,
                    parent_field, mapping_setting.source_placeholder
                )
        except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
            logger.info('Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id)


def schedule_fyle_attributes_creation(workspace_id: int):
    mapping_settings = MappingSetting.objects.filter(
        is_custom=True, import_to_fyle=True, workspace_id=workspace_id
    ).all()

    if mapping_settings:
        schedule, _= Schedule.objects.get_or_create(
            func='apps.mappings.tasks.async_auto_create_custom_field_mappings',
            args='{0}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': datetime.now() + timedelta(hours=24)
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.async_auto_create_custom_field_mappings',
            args=workspace_id
        ).first()

        if schedule:
            schedule.delete()


def sync_expense_types_and_accounts(reimbursable_expenses_object: str, corporate_credit_card_expenses_object: str,
    si_connection: SageIntacctConnector):
    if reimbursable_expenses_object == 'EXPENSE_REPORT' or corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
        si_connection.sync_expense_types()

    if reimbursable_expenses_object == 'BILL' or \
        corporate_credit_card_expenses_object in ('BILL', 'CHARGE_CARD_TRANSACTION', 'JOURNAL_ENTRY'):
        si_connection.sync_accounts()


def upload_categories_to_fyle(workspace_id: int, reimbursable_expenses_object: str,
    corporate_credit_card_expenses_object: str, fyle_credentials: FyleCredential):
    """
    Upload categories to Fyle
    """
    si_credentials: SageIntacctCredential = SageIntacctCredential.objects.get(workspace_id=workspace_id)

    platform = PlatformConnector(fyle_credentials)

    category_map = get_all_categories_from_fyle(platform=platform)


    si_connection = SageIntacctConnector(
        credentials_object=si_credentials,
        workspace_id=workspace_id
    )
    platform.categories.sync()
    

    sync_expense_types_and_accounts(reimbursable_expenses_object, corporate_credit_card_expenses_object, si_connection)

    if reimbursable_expenses_object == 'EXPENSE_REPORT':
        si_attributes: List[DestinationAttribute] = DestinationAttribute.objects.filter(
            workspace_id=workspace_id, attribute_type='EXPENSE_TYPE'
        )
    else:
        si_attributes: List[DestinationAttribute] = DestinationAttribute.objects.filter(
            workspace_id=workspace_id, attribute_type='ACCOUNT'
        ).all()

    si_attributes = remove_duplicates(si_attributes)

    fyle_payload: List[Dict] = create_fyle_categories_payload(si_attributes, category_map)
    if fyle_payload:
        platform.categories.post_bulk(fyle_payload)
        platform.categories.sync()

    return si_attributes


def bulk_create_ccc_category_mappings(workspace_id: int):
    """
    Create Category Mappings for CCC Expenses
    :param workspace_id: Workspace ID
    """
    category_mappings = CategoryMapping.objects.filter(
        workspace_id=workspace_id,
        destination_account__isnull=True
    ).all()

    gl_account_ids = []

    for category_mapping in category_mappings:
        if category_mapping.destination_expense_head.detail and \
            'gl_account_no' in category_mapping.destination_expense_head.detail and \
                category_mapping.destination_expense_head.detail['gl_account_no']:
            gl_account_ids.append(category_mapping.destination_expense_head.detail['gl_account_no'])

    # Retreiving accounts for creating ccc mapping
    destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=workspace_id,
        attribute_type='ACCOUNT',
        destination_id__in=gl_account_ids
    ).values('id', 'destination_id')

    destination_id_pk_map = {}

    for attribute in destination_attributes:
        destination_id_pk_map[attribute['destination_id'].lower()] = attribute['id']

    mapping_updation_batch = []

    for category_mapping in category_mappings:
        ccc_account_id = destination_id_pk_map[category_mapping.destination_expense_head.detail['gl_account_no'].lower()]
        mapping_updation_batch.append(
            CategoryMapping(
                id=category_mapping.id,
                destination_account_id=ccc_account_id
            )
        )

    if mapping_updation_batch:
        CategoryMapping.objects.bulk_update(
            mapping_updation_batch, fields=['destination_account'], batch_size=50
        )


def construct_filter_based_on_destination(reimbursable_destination_type: str):
    """
    Construct Filter Based on Destination
    :param reimbursable_destination_type: Reimbursable Destination Type
    :return: Filter
    """
    filters = {}
    if reimbursable_destination_type == 'EXPENSE_TYPE':
        filters['destination_expense_head__isnull'] = True
    elif reimbursable_destination_type == 'ACCOUNT':
        filters['destination_account__isnull'] = True

    return filters


def filter_unmapped_destinations(reimbursable_destination_type: str, destination_attributes: List[DestinationAttribute]):
    """
    Filter unmapped destinations based on workspace
    :param reimbursable_destination_type: Reimbursable destination type
    :param destination_attributes: List of destination attributes
    """
    filters = construct_filter_based_on_destination(reimbursable_destination_type)

    destination_attribute_ids = [destination_attribute.id for destination_attribute in destination_attributes]

    # Filtering unmapped categories
    destination_attributes = DestinationAttribute.objects.filter(
        pk__in=destination_attribute_ids,
        **filters
    ).values('id', 'value')

    return destination_attributes


def bulk_create_update_category_mappings(mapping_creation_batch: List[CategoryMapping]):
    """
    Bulk Create and Update Category Mappings
    :param mapping_creation_batch: List of Category Mappings
    """
    expense_attributes_to_be_updated = []
    created_mappings = []

    if mapping_creation_batch:
        created_mappings = CategoryMapping.objects.bulk_create(mapping_creation_batch, batch_size=50)

    for category_mapping in created_mappings:
        expense_attributes_to_be_updated.append(
            ExpenseAttribute(
                id=category_mapping.source_category.id,
                auto_mapped=True
            )
        )

    if expense_attributes_to_be_updated:
        ExpenseAttribute.objects.bulk_update(
            expense_attributes_to_be_updated, fields=['auto_mapped'], batch_size=50)


def create_category_mappings(destination_attributes: List[DestinationAttribute],
                             reimbursable_destination_type: str, workspace_id: int):
    """
    Bulk create category mappings
    :param destination_attributes: Desitination Attributes
    :param reimbursable_destination_type: Reimbursable Destination Type
    :param workspace_id: Workspace ID
    :return: None
    """
    destination_attributes = filter_unmapped_destinations(reimbursable_destination_type, destination_attributes)

    attribute_value_list = []
    attribute_value_list = [destination_attribute['value'] for destination_attribute in destination_attributes]

    # Filtering unmapped categories
    source_attributes = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        value__in=attribute_value_list,
        categorymapping__source_category__isnull=True
    ).values('id', 'value')

    source_attributes_id_map = {source_attribute['value'].lower(): source_attribute['id'] \
        for source_attribute in source_attributes}

    mapping_creation_batch = []

    for destination_attribute in destination_attributes:
        if destination_attribute['value'].lower() in source_attributes_id_map:
            destination = {}
            if reimbursable_destination_type == 'EXPENSE_TYPE':
                destination['destination_expense_head_id'] = destination_attribute['id']
            elif reimbursable_destination_type == 'ACCOUNT':
                destination['destination_account_id'] = destination_attribute['id']

            mapping_creation_batch.append(
                CategoryMapping(
                    source_category_id=source_attributes_id_map[destination_attribute['value'].lower()],
                    workspace_id=workspace_id,
                    **destination
                )
            )

    bulk_create_update_category_mappings(mapping_creation_batch)


def auto_create_category_mappings(workspace_id):
    """
    Create Category Mappings
    :return: mappings
    """
    configuration: Configuration = Configuration.objects.get(workspace_id=workspace_id)

    reimbursable_expenses_object = configuration.reimbursable_expenses_object
    corporate_credit_card_expenses_object = configuration.corporate_credit_card_expenses_object

    if reimbursable_expenses_object == 'EXPENSE_REPORT':
        reimbursable_destination_type = 'EXPENSE_TYPE'
    else:
        reimbursable_destination_type = 'ACCOUNT'

    try:
        fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
        platform = PlatformConnector(fyle_credentials=fyle_credentials)

        fyle_categories = upload_categories_to_fyle(
            workspace_id=workspace_id, reimbursable_expenses_object=reimbursable_expenses_object,
            corporate_credit_card_expenses_object=corporate_credit_card_expenses_object, fyle_credentials=fyle_credentials)

        create_category_mappings(fyle_categories, reimbursable_destination_type, workspace_id)

        # auto-sync categories and expense accounts
        category_ids_to_be_changed = disable_expense_attributes('CATEGORY', reimbursable_destination_type, workspace_id)
        if category_ids_to_be_changed:
            expense_attributes = ExpenseAttribute.objects.filter(id__in=category_ids_to_be_changed)
            fyle_payload: List[Dict] = create_fyle_categories_payload(categories=[], category_map={}, updated_categories=expense_attributes, destination_type=reimbursable_destination_type)

            platform.categories.post_bulk(fyle_payload)
            platform.categories.sync()

        if reimbursable_expenses_object == 'EXPENSE_REPORT' and \
                corporate_credit_card_expenses_object in ('BILL', 'CHARGE_CARD_TRANSACTION', 'JOURNAL_ENTRY'):
            bulk_create_ccc_category_mappings(workspace_id)

        return []

    except InvalidTokenError:
        logger.info('Invalid Token or Invalid fyle credentials - %s', workspace_id)
    
    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle')

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
        logger.exception(
            'Error while creating categories workspace_id - %s error: %s',
            workspace_id, error
        )


def upload_tax_groups_to_fyle(platform_connection: PlatformConnector, workspace_id: int):
    existing_tax_codes_name = ExpenseAttribute.objects.filter(
        attribute_type='TAX_GROUP', workspace_id=workspace_id).values_list('value', flat=True)

    si_attributes = DestinationAttribute.objects.filter(
        attribute_type='TAX_DETAIL', workspace_id=workspace_id).order_by('value', 'id')

    si_attributes = remove_duplicates(si_attributes)

    fyle_payload: List[Dict] = create_fyle_tax_group_payload(si_attributes, existing_tax_codes_name)

    if fyle_payload:
        platform_connection.tax_groups.post_bulk(fyle_payload)

    platform_connection.tax_groups.sync()
    Mapping.bulk_create_mappings(si_attributes, 'TAX_GROUP', 'TAX_DETAIL', workspace_id)


def create_fyle_tax_group_payload(si_attributes: List[DestinationAttribute], existing_fyle_tax_groups: list):
    """
    Create Fyle Cost Centers Payload from Sage Intacct Objects
    :param existing_fyle_tax_groups: Existing cost center names
    :param si_attributes: Sage Intacct Objects
    :return: Fyle Cost Centers Payload
    """

    fyle_tax_group_payload = []
    for si_attribute in si_attributes:
        if si_attribute.value not in existing_fyle_tax_groups:
            fyle_tax_group_payload.append(
                {
                    'name': si_attribute.value,
                    'is_enabled': True,
                    'percentage': round((si_attribute.detail['tax_rate']/100), 2)
                }
            )

    return fyle_tax_group_payload


def auto_create_tax_codes_mappings(workspace_id: int):
    """
    Create Tax Codes Mappings
    :return: None
    """
    try:
        fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)

        platform = PlatformConnector(fyle_credentials=fyle_credentials)
        platform.tax_groups.sync()

        mapping_setting = MappingSetting.objects.get(
            source_field='TAX_GROUP', workspace_id=workspace_id
        )

        sync_sage_intacct_attributes(mapping_setting.destination_field, workspace_id)

        upload_tax_groups_to_fyle(platform, workspace_id)

    except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id)
    
    except FyleInvalidTokenError:
        logger.info('Invalid Token for Fyle')

    except WrongParamsError as exception:
        logger.error(
            'Error while creating tax groups workspace_id - %s in Fyle %s %s',
            workspace_id, exception.message, {'error': exception.response}
        )

    except Exception:
        error = traceback.format_exc()
        error = {
            'error': error
        }
        logger.exception(
            'Error while creating tax groups workspace_id - %s error: %s',
            workspace_id, error
        )


def schedule_tax_groups_creation(import_tax_codes, workspace_id):
    if import_tax_codes:
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.auto_create_tax_codes_mappings',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': datetime.now()
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.auto_create_tax_codes_mappings',
            args='{}'.format(workspace_id),
        ).first()

        if schedule:
            schedule.delete()


def create_fyle_merchants_payload(vendors, existing_merchants_name):
    payload: List[str] = []
    for vendor in vendors:
        if vendor.value not in existing_merchants_name:
            payload.append(vendor.value)
    return payload


def post_merchants(platform_connection: PlatformConnector, workspace_id: int, first_run: bool):
    existing_merchants_name = ExpenseAttribute.objects.filter(
        attribute_type='MERCHANT', workspace_id=workspace_id).values_list('value', flat=True)

    if first_run:
        sage_intacct_attributes = DestinationAttribute.objects.filter(
            attribute_type='VENDOR', workspace_id=workspace_id).order_by('value', 'id')
    else:
        merchant = platform_connection.merchants.get()
        merchant_updated_at = parser.isoparse(merchant['updated_at']).strftime('%Y-%m-%d')
        sage_intacct_attributes = DestinationAttribute.objects.filter(
            attribute_type='VENDOR',
            workspace_id=workspace_id,
            updated_at__gte=merchant_updated_at
        ).order_by('value', 'id')

    sage_intacct_attributes = remove_duplicates(sage_intacct_attributes)

    fyle_payload: List[str] = create_fyle_merchants_payload(sage_intacct_attributes, existing_merchants_name)

    if fyle_payload:
        platform_connection.merchants.post(fyle_payload)

    platform_connection.merchants.sync(workspace_id)


def auto_create_vendors_as_merchants(workspace_id):
    try:
        fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)

        fyle_connection = PlatformConnector(fyle_credentials)

        existing_merchants_name = ExpenseAttribute.objects.filter(attribute_type='MERCHANT', workspace_id=workspace_id)
        first_run = False if existing_merchants_name else True

        fyle_connection.merchants.sync(workspace_id)

        sync_sage_intacct_attributes('VENDOR', workspace_id)
        post_merchants(fyle_connection, workspace_id, first_run)

    except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id)
    
    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle - %s', workspace_id)

    except WrongParamsError as exception:
        logger.error(
            'Error while posting vendors as merchants to fyle for workspace_id - %s in Fyle %s %s',
            workspace_id, exception.message, {'error': exception.response}
        )

    except Exception:
        error = traceback.format_exc()
        error = {
            'error': error
        }
        logger.exception(
            'Error while posting vendors as merchants to fyle for workspace_id - %s error: %s',
            workspace_id, error)


def auto_import_and_map_fyle_fields(workspace_id):
    """
    Auto import and map fyle fields
    """
    configuration: Configuration = Configuration.objects.get(workspace_id=workspace_id)
    project_mapping = MappingSetting.objects.filter(source_field='PROJECT', workspace_id=configuration.workspace_id).first()

    chain = Chain()

    if configuration.import_vendors_as_merchants:
        chain.append('apps.mappings.tasks.auto_create_vendors_as_merchants', workspace_id)

    if configuration.import_categories:
        chain.append('apps.mappings.tasks.auto_create_category_mappings', workspace_id)

    if project_mapping and project_mapping.import_to_fyle:
        chain.append('apps.mappings.tasks.auto_create_project_mappings', workspace_id)

    if chain.length() > 0:
        chain.run()

