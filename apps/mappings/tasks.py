import logging
import traceback
from datetime import datetime, timedelta
from dateutil import parser

from typing import List, Dict

from django_q.models import Schedule
from django_q.tasks import Chain
from fyle_integrations_platform_connector import PlatformConnector

from fyle.platform.exceptions import (
    WrongParamsError,
    InvalidTokenError as FyleInvalidTokenError,
    InternalServerError
)

from fyle_accounting_mappings.helpers import EmployeesAutoMappingHelper
from fyle_accounting_mappings.models import (
    Mapping,
    MappingSetting,
    ExpenseAttribute,
    DestinationAttribute,
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
from .constants import FYLE_EXPENSE_SYSTEM_FIELDS

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def get_mapped_attributes_ids(source_attribute_type: str, destination_attribute_type: str, errored_attribute_ids: List[int]):

    mapped_attribute_ids = []

    if source_attribute_type == "TAX_GROUP":
        mapped_attribute_ids: List[int] = Mapping.objects.filter(
            source_id__in=errored_attribute_ids
        ).values_list('source_id', flat=True)

    elif source_attribute_type == "EMPLOYEE":
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

    except InternalServerError:
        logger.error('Internal server error while importing to Fyle')

    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')

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

# Delete this 
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


def construct_custom_field_placeholder(source_placeholder: str, fyle_attribute: str, existing_attribute: Dict):
    new_placeholder = None
    placeholder = None

    if existing_attribute:
        placeholder = existing_attribute['placeholder'] if 'placeholder' in existing_attribute else None

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

    return new_placeholder


def create_fyle_expense_custom_field_payload(sageintacct_attributes: List[DestinationAttribute], workspace_id: int,
                                            fyle_attribute: str, platform: PlatformConnector, source_placeholder: str = None):
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
        placeholder = construct_custom_field_placeholder(source_placeholder, fyle_attribute, existing_attribute)

        expense_custom_field_payload = {
            'field_name': fyle_attribute,
            'type': 'SELECT',
            'is_enabled': True,
            'is_mandatory': False,
            'placeholder': placeholder,
            'options': fyle_expense_custom_field_options,
            'code': None
        }


        if custom_field_id:
            expense_field = platform.expense_custom_fields.get_by_id(custom_field_id)
            expense_custom_field_payload['id'] = custom_field_id
            expense_custom_field_payload['is_mandatory'] = expense_field['is_mandatory']

        return expense_custom_field_payload


def upload_attributes_to_fyle(workspace_id: int, sageintacct_attribute_type: str, fyle_attribute_type: str, source_placeholder: str = None):
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
        source_placeholder=source_placeholder
    )

    if fyle_custom_field_payload:
        platform.expense_custom_fields.post(fyle_custom_field_payload)
        platform.expense_custom_fields.sync()

    return sageintacct_attributes


def auto_create_expense_fields_mappings(
    workspace_id: int, sageintacct_attribute_type: str, fyle_attribute_type: str, source_placeholder: str = None
):
    """
    Create Fyle Attributes Mappings
    :return: mappings
    """
    try:
        fyle_attributes = None
        fyle_attributes = upload_attributes_to_fyle(
            workspace_id=workspace_id,
            sageintacct_attribute_type=sageintacct_attribute_type,
            fyle_attribute_type=fyle_attribute_type,
            source_placeholder=source_placeholder
        )

        if fyle_attributes:
            Mapping.bulk_create_mappings(fyle_attributes, fyle_attribute_type, sageintacct_attribute_type, workspace_id)

    except InvalidTokenError:
        logger.info('Invalid Token or Invalid fyle credentials - %s', workspace_id)

    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle')
    
    except InternalServerError:
        logger.error('Internal server error while importing to Fyle')

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
                sync_sage_intacct_attributes(mapping_setting.destination_field, workspace_id)
                auto_create_expense_fields_mappings(
                    workspace_id, mapping_setting.destination_field, mapping_setting.source_field,
                    mapping_setting.source_placeholder
                )
        except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
            logger.info('Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id)
        except NoPrivilegeError:
            logger.info('Insufficient permission to access the requested module')


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
    resolve_expense_attribute_errors(
        source_attribute_type="TAX_GROUP", workspace_id=workspace_id
    )


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

    except InternalServerError:
        logger.error('Internal server error while importing to Fyle')

    except WrongParamsError as exception:
        logger.error(
            'Error while creating tax groups workspace_id - %s in Fyle %s %s',
            workspace_id, exception.message, {'error': exception.response}
        )

    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')

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

    platform_connection.merchants.sync()


def auto_create_vendors_as_merchants(workspace_id):
    try:
        fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)

        fyle_connection = PlatformConnector(fyle_credentials)

        existing_merchants_name = ExpenseAttribute.objects.filter(attribute_type='MERCHANT', workspace_id=workspace_id)
        first_run = False if existing_merchants_name else True

        fyle_connection.merchants.sync()

        sync_sage_intacct_attributes('VENDOR', workspace_id)
        post_merchants(fyle_connection, workspace_id, first_run)

    except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id)
    
    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle - %s', workspace_id)
    
    except InternalServerError:
        logger.error('Internal server error while importing to Fyle')

    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')

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
    project_mapping = MappingSetting.objects.filter(
        source_field='PROJECT',
        workspace_id=workspace_id,
        import_to_fyle=True
    ).first()
    dependent_fields = DependentFieldSetting.objects.filter(workspace_id=workspace_id, is_import_enabled=True).first()

    chain = Chain()

    if configuration.import_vendors_as_merchants:
        chain.append('apps.mappings.tasks.auto_create_vendors_as_merchants', workspace_id)

    if project_mapping and dependent_fields:
        chain.append('apps.sage_intacct.dependent_fields.import_dependent_fields_to_fyle', workspace_id)

    if chain.length() > 0:
        chain.run()
