import logging
import traceback
from datetime import datetime, timedelta
from dateutil import parser

from typing import List, Dict

from django_q.models import Schedule
from django.db.models import Q, Count
from fyle_integrations_platform_connector import PlatformConnector

from fyle.platform.exceptions import WrongParamsError
from fyle_accounting_mappings.models import Mapping, MappingSetting, ExpenseAttribute, DestinationAttribute, \
    CategoryMapping

from apps.mappings.models import GeneralMapping
from apps.sage_intacct.utils import SageIntacctConnector
from apps.workspaces.models import SageIntacctCredential, FyleCredential, Configuration
from .constants import FYLE_EXPENSE_SYSTEM_FIELDS

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def remove_duplicates(si_attributes: List[DestinationAttribute]):
    unique_attributes = []

    attribute_values = []

    for attribute in si_attributes:
        if attribute.value.lower() not in attribute_values:
            unique_attributes.append(attribute)
            attribute_values.append(attribute.value.lower())

    return unique_attributes


def create_fyle_projects_payload(projects: List[DestinationAttribute], existing_project_names: list):
    """
    Create Fyle Projects Payload from Sage Intacct Projects and Customers
    :param projects: Sage Intacct Projects
    :return: Fyle Projects Payload
    """
    payload = []

    for project in projects:
        if project.value not in existing_project_names:
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


def post_projects_in_batches(platform: PlatformConnector,
                             workspace_id: int, destination_field: str):
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


def schedule_projects_creation(import_to_fyle, workspace_id):
    if import_to_fyle:
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.auto_create_project_mappings',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': datetime.now()
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
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    employee_mapping_preference = configuration.auto_map_employees

    destination_type = configuration.employee_field_mapping

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(
        credentials_object=sage_intacct_credentials, workspace_id=workspace_id)

    platform.employees.sync()
    if destination_type == 'EMPLOYEE':
        sage_intacct_connection.sync_employees()
    else:
        sage_intacct_connection.sync_vendors()

    Mapping.auto_map_employees(destination_type, employee_mapping_preference, workspace_id)


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
    Mapping.auto_map_ccc_employees('CHARGE_CARD_NUMBER', default_charge_card_id, workspace_id)


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


def create_fyle_categories_payload(categories: List[DestinationAttribute], workspace_id: int, category_map: Dict):
    """
    Create Fyle Categories Payload from Sage Intacct Expense Types / Accounts
    :param workspace_id: Workspace integer id
    :param categories: Sage Intacct Categories / Accounts
    :return: Fyle Categories Payload
    """
    payload = []

    for category in categories:
        if category.value.lower() not in category_map:
            payload.append({
                'name': category.value,
                'code': category.destination_id,
                'is_enabled': True if category.active is None else category.active,
                'restricted_project_ids': None
            })
        else:
            payload.append({
                'id': category_map[category.value.lower()]['id'],
                'name': category.value,
                'code': category.destination_id,
                'is_enabled': category_map[category.value.lower()]['is_enabled'],
                'restricted_project_ids': None
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
                                             fyle_attribute: str, platform: PlatformConnector):
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
        if existing_attribute is not None:
            custom_field_id = existing_attribute['custom_field_id']

        fyle_attribute = fyle_attribute.replace('_', ' ').title()

        expense_custom_field_payload = {
            'field_name': fyle_attribute,
            'type': 'SELECT',
            'is_enabled': True,
            'is_mandatory': False,
            'placeholder': 'Select {0}'.format(fyle_attribute),
            'options': fyle_expense_custom_field_options,
            'code': None
        }

        if custom_field_id:
            expense_field = platform.expense_custom_fields.get_by_id(custom_field_id)
            expense_custom_field_payload['id'] = custom_field_id
            expense_custom_field_payload['is_mandatory'] = expense_field['is_mandatory']

        return expense_custom_field_payload


def upload_attributes_to_fyle(workspace_id: int, sageintacct_attribute_type: str, fyle_attribute_type: str):
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
        platform=platform
    )

    if fyle_custom_field_payload:
        platform.expense_custom_fields.post(fyle_custom_field_payload)
        platform.expense_custom_fields.sync()

    return sageintacct_attributes


def auto_create_expense_fields_mappings(workspace_id: int, sageintacct_attribute_type: str, fyle_attribute_type: str):
    """
    Create Fyle Attributes Mappings
    :return: mappings
    """
    try:
        fyle_attributes = upload_attributes_to_fyle(workspace_id=workspace_id, sageintacct_attribute_type=sageintacct_attribute_type, fyle_attribute_type=fyle_attribute_type)
        if fyle_attributes:
            Mapping.bulk_create_mappings(fyle_attributes, fyle_attribute_type, sageintacct_attribute_type, workspace_id)

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
        if mapping_setting.import_to_fyle:
            sync_sage_intacct_attributes(mapping_setting.destination_field, workspace_id)
            auto_create_expense_fields_mappings(
                workspace_id, mapping_setting.destination_field, mapping_setting.source_field
            )


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
    corporate_credit_card_expenses_object: str):
    """
    Upload categories to Fyle
    """
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
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

    fyle_payload: List[Dict] = create_fyle_categories_payload(si_attributes, workspace_id, category_map)
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

    account_internal_ids = []

    for category_mapping in category_mappings:
        if category_mapping.destination_expense_head.detail and \
            'account_internal_id' in category_mapping.destination_expense_head.detail and \
                category_mapping.destination_expense_head.detail['account_internal_id']:
            account_internal_ids.append(category_mapping.destination_expense_head.detail['account_internal_id'])

    # Retreiving accounts for creating ccc mapping
    destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=workspace_id,
        attribute_type='ACCOUNT',
        destination_id__in=account_internal_ids
    ).values('id', 'destination_id')

    destination_id_pk_map = {}

    for attribute in destination_attributes:
        destination_id_pk_map[attribute['destination_id'].lower()] = attribute['id']

    mapping_updation_batch = []

    for category_mapping in category_mappings:
        ccc_account_id = destination_id_pk_map[category_mapping.destination_expense_head.detail['account_internal_id'].lower()]
        mapping_updation_batch.append(
            CategoryMapping(
                id=category_mapping.id,
                source_category_id=category_mapping.source_category.id,
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
        fyle_categories = upload_categories_to_fyle(
            workspace_id=workspace_id, reimbursable_expenses_object=reimbursable_expenses_object,
            corporate_credit_card_expenses_object=corporate_credit_card_expenses_object)

        create_category_mappings(fyle_categories, reimbursable_destination_type, workspace_id)

        if reimbursable_expenses_object == 'EXPENSE REPORT' and \
                corporate_credit_card_expenses_object in ('BILL', 'CHARGE_CARD_TRANSACTION', 'JOURNAL_ENTRY'):
            bulk_create_ccc_category_mappings(workspace_id)

        return []

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
        logger.error(
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


def schedule_vendors_as_merchants_creation(import_vendors_as_merchants, workspace_id):
    if import_vendors_as_merchants:
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.auto_create_vendors_as_merchants',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': datetime.now()
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.auto_create_vendors_as_merchants',
            args='{}'.format(workspace_id),
        ).first()

        if schedule:
            schedule.delete()
