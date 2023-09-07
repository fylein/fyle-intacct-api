from unittest import mock
from django_q.models import Schedule
from fyle_accounting_mappings.models import DestinationAttribute, CategoryMapping, \
    Mapping, MappingSetting, EmployeeMapping, ExpenseAttribute
from apps.mappings.tasks import *
from fyle_integrations_platform_connector import PlatformConnector
from ..test_sageintacct.fixtures import data as intacct_data
from ..test_fyle.fixtures import data as fyle_data
from .fixtures import data
from tests.helper import dict_compare_keys
from apps.workspaces.models import FyleCredential, Configuration
from apps.fyle.models import ExpenseGroup
from fyle.platform.exceptions import InvalidTokenError as FyleInvalidTokenError, InternalServerError
from sageintacctsdk.exceptions import NoPrivilegeError


def test_resolve_expense_attribute_errors(db):
    workspace_id = 1
    expense_group = ExpenseGroup.objects.get(id=3)

    employee_attribute = ExpenseAttribute.objects.filter(
        value=expense_group.description.get('employee_email'),
        workspace_id=expense_group.workspace_id,
        attribute_type='EMPLOYEE'
    ).first()

    error, _ = Error.objects.update_or_create(
        workspace_id=expense_group.workspace_id,
        expense_attribute=employee_attribute,
        defaults={
            'type': 'EMPLOYEE_MAPPING',
            'error_title': employee_attribute.value,
            'error_detail': 'Employee mapping is missing',
            'is_resolved': False
        }
    )

    resolve_expense_attribute_errors('EMPLOYEE', workspace_id, 'EMPLOYEE')
    assert Error.objects.get(id=error.id).is_resolved == True

    error, _ = Error.objects.update_or_create(
        workspace_id=expense_group.workspace_id,
        expense_attribute=employee_attribute,
        defaults={
            'type': 'EMPLOYEE_MAPPING',
            'error_title': employee_attribute.value,
            'error_detail': 'Employee mapping is missing',
            'is_resolved': False
        }
    )

    resolve_expense_attribute_errors('EMPLOYEE', workspace_id, 'VENDOR')
    assert Error.objects.get(id=error.id).is_resolved == True

    source_category = ExpenseAttribute.objects.filter(
        id=106,
        workspace_id=1,
        attribute_type='CATEGORY'
    ).first()

    Error.objects.update_or_create(
        workspace_id=1,
        expense_attribute=source_category,
        defaults={
            'type': 'CATEGORY_MAPPING',
            'error_title': source_category.value,
            'error_detail': 'Category mapping is missing',
            'is_resolved': False
        }
    )

    resolve_expense_attribute_errors('CATEGORY', workspace_id, 'ACCOUNT')
    assert Error.objects.get(id=error.id).is_resolved == True


def test_auto_create_tax_codes_mappings(db, mocker):
    workspace_id = 1
    mocker.patch(
        'fyle_integrations_platform_connector.apis.TaxGroups.post_bulk',
        return_value=[]
    )

    mocker.patch(
        'fyle_integrations_platform_connector.apis.TaxGroups.sync',
        return_value=[]
    )
    mocker.patch(
        'sageintacctsdk.apis.Dimensions.get_all',
        return_value=intacct_data['get_dimensions']
    )

    tax_code = ExpenseAttribute.objects.filter(value='UK Purchase Services Zero Rate').first()
    tax_code.value = 'random'
    tax_code.save()

    tax_groups = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_CODE').count()
    mappings = Mapping.objects.filter(workspace_id=workspace_id, destination_type='TAX_CODE').count()
    
    assert tax_groups == 0
    assert mappings == 0

    auto_create_tax_codes_mappings(workspace_id=workspace_id)

    tax_groups = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_CODE').count()
    mappings = Mapping.objects.filter(workspace_id=workspace_id, destination_type='TAX_CODE').count()
    
    assert mappings == 0

    with mock.patch('fyle_integrations_platform_connector.apis.TaxGroups.sync') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response='invalid params')
        auto_create_tax_codes_mappings(workspace_id=workspace_id)

        mock_call.side_effect = InternalServerError(msg='internal server error', response='internal server error')
        auto_create_tax_codes_mappings(workspace_id=workspace_id)

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        auto_create_tax_codes_mappings(workspace_id=workspace_id)

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.delete()

    response = auto_create_tax_codes_mappings(workspace_id)

    assert response == None


def test_schedule_tax_groups_creation(db):
    workspace_id = 1
    schedule_tax_groups_creation(import_tax_codes=True, workspace_id=workspace_id)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.auto_create_tax_codes_mappings',
        args='{}'.format(workspace_id),
    ).first()
    
    assert schedule.func == 'apps.mappings.tasks.auto_create_tax_codes_mappings'

    schedule_tax_groups_creation(import_tax_codes=False, workspace_id=workspace_id)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.auto_create_tax_codes_mappings',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None


def test_remove_duplicates(db):

    attributes = DestinationAttribute.objects.filter(attribute_type='EMPLOYEE')
    assert len(attributes) == 55

    attributes = remove_duplicates(attributes)
    assert len(attributes) == 55


def test_async_auto_map_employees(mocker, db):
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Vendors.get_all',
        return_value=intacct_data['get_vendors']
    )

    mocker.patch(
        'sageintacctsdk.apis.Employees.get_all',
        return_value=intacct_data['get_employees']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Employees.list_all',
        return_value=fyle_data['get_all_employees']
    )

    general_settings = Configuration.objects.get(workspace_id=workspace_id)

    general_settings.employee_field_mapping = 'EMPLOYEE'
    general_settings.save()

    async_auto_map_employees(workspace_id)

    employee_mappings = EmployeeMapping.objects.filter(workspace_id=workspace_id).count()
    assert employee_mappings == 1

    general_settings.employee_field_mapping = 'VENDOR'
    general_settings.save()

    async_auto_map_employees(workspace_id)

    employee_mappings = EmployeeMapping.objects.filter(workspace_id=workspace_id).count()
    assert employee_mappings == 1


def test_schedule_auto_map_employees(db):
    workspace_id = 1

    schedule_auto_map_employees(employee_mapping_preference=True, workspace_id=workspace_id)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.async_auto_map_employees',
        args='{}'.format(workspace_id),
    ).first()
    
    assert schedule.func == 'apps.mappings.tasks.async_auto_map_employees'

    schedule_auto_map_employees(employee_mapping_preference=False, workspace_id=workspace_id)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.async_auto_map_employees',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None


def test_auto_create_cost_center_mappings(db, mocker, create_mapping_setting):
    workspace_id = 1
    mocker.patch(
        'fyle_integrations_platform_connector.apis.CostCenters.post_bulk',
        return_value=[]
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.CostCenters.sync',
        return_value=[]
    )
    mocker.patch(
        'sageintacctsdk.apis.Departments.get_all',
        return_value=intacct_data['get_departments']
    )
    mocker.patch(
        'sageintacctsdk.apis.Dimensions.get_all',
        return_value=intacct_data['get_user_defined_dimensions']
    )
    mocker.patch(
        'sageintacctsdk.apis.DimensionValues.get_all',
        return_value=intacct_data['get_dimension_value']
    )

    response = auto_create_cost_center_mappings(workspace_id=workspace_id)
    assert response == None

    cost_center = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='COST_CENTER').count()
    mappings = Mapping.objects.filter(workspace_id=workspace_id, source_type='COST_CENTER').count()

    assert cost_center == 1
    assert mappings == 0

    with mock.patch('fyle_integrations_platform_connector.apis.CostCenters.sync') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response='invalid params')
        auto_create_cost_center_mappings(workspace_id=workspace_id)

        mock_call.side_effect = FyleInvalidTokenError(msg='invalid token for fyle', response='invalid params')
        auto_create_cost_center_mappings(workspace_id=workspace_id)

        mock_call.side_effect = InternalServerError(msg='internal server error', response='internal server error')
        auto_create_cost_center_mappings(workspace_id=workspace_id)

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        auto_create_cost_center_mappings(workspace_id=workspace_id)

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.delete()

    response = auto_create_cost_center_mappings(workspace_id=workspace_id)
    assert response == None


def test_post_cost_centers_in_batches(mocker, db):
    workspace_id = 1

    mocker.patch(
        'fyle_integrations_platform_connector.apis.CostCenters.post_bulk',
        return_value=[]
    )

    mocker.patch(
        'fyle_integrations_platform_connector.apis.CostCenters.sync',
        return_value=[]
    )

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_connection = PlatformConnector(fyle_credentials)

    post_cost_centers_in_batches(fyle_connection, workspace_id, 'DEPARTMENT')


def test_schedule_cost_centers_creation(db):
    workspace_id = 1

    schedule_cost_centers_creation(import_to_fyle=True, workspace_id=workspace_id)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.auto_create_cost_center_mappings',
        args='{}'.format(workspace_id),
    ).first()
    
    assert schedule.func == 'apps.mappings.tasks.auto_create_cost_center_mappings'

    schedule_cost_centers_creation(import_to_fyle=False, workspace_id=workspace_id)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.auto_create_cost_center_mappings',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None


def test_schedule_fyle_attributes_creation(db, mocker):
    workspace_id = 1

    mapping_setting = MappingSetting.objects.last()
    mapping_setting.is_custom=True
    mapping_setting.import_to_fyle=True
    mapping_setting.save()
    
    schedule_fyle_attributes_creation(workspace_id)

    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )

    mocker.patch(
        'sageintacctsdk.apis.Dimensions.get_all',
        return_value=intacct_data['get_dimensions']
    )

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.async_auto_create_custom_field_mappings',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.async_auto_create_custom_field_mappings'

    async_auto_create_custom_field_mappings(workspace_id)

    schedule_fyle_attributes_creation(2)
    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.async_auto_create_custom_field_mappings',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.async_auto_create_custom_field_mappings'

    with mock.patch('apps.mappings.tasks.async_auto_create_custom_field_mappings') as mock_call:
        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        async_auto_create_custom_field_mappings(workspace_id=workspace_id)


def test_auto_create_expense_fields_mappings(db, mocker, create_mapping_setting):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.sync',
        return_value=[]
    )
    workspace_id = 1
    
    auto_create_expense_fields_mappings(workspace_id, 'TASK', 'COST_CODES', None)
    mappings = Mapping.objects.filter(workspace_id=workspace_id, destination_type='TASK').count()
    assert mappings == 0

    auto_create_expense_fields_mappings(workspace_id, 'COST_CENTER', 'COST_CENTER', 'Select Cost Center')

    cost_center = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='COST_CENTER').count()
    mappings = Mapping.objects.filter(workspace_id=workspace_id, source_type='COST_CENTER').count()

    assert cost_center == 1
    assert mappings == 0    


def test_sync_sage_intacct_attributes(mocker, db, create_dependent_field_setting, create_cost_type):
    workspace_id = 1
    mocker.patch(
        'sageintacctsdk.apis.Locations.get_all',
        return_value=intacct_data['get_locations']
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=5
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all',
        return_value=intacct_data['get_projects']
    )
    mocker.patch(
        'sageintacctsdk.apis.Departments.get_all',
        return_value=intacct_data['get_departments']
    )
    mocker.patch(
        'sageintacctsdk.apis.Vendors.get_all',
        return_value=intacct_data['get_vendors']
    )

    mocker.patch(
        'sageintacctsdk.apis.CostTypes.get_all_generator',
        return_value=[]
    )

    sync_sage_intacct_attributes('DEPARTMENT', workspace_id=workspace_id)
    sync_sage_intacct_attributes('LOCATION', workspace_id=workspace_id)
    sync_sage_intacct_attributes('PROJECT', workspace_id=workspace_id)
    sync_sage_intacct_attributes('VENDOR', workspace_id=workspace_id)
    sync_sage_intacct_attributes('COST_TYPE', workspace_id)

    projects = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    mappings = Mapping.objects.filter(workspace_id=workspace_id, destination_type='PROJECT').count()

    assert mappings == projects


def test_async_auto_map_charge_card_account(mocker, db):
    workspace_id = 1
    
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Employees.sync',
        return_value=[]
    )
    mocker.patch(
        'fyle_accounting_mappings.helpers.EmployeesAutoMappingHelper.ccc_mapping',
        return_value=None
    )

    async_auto_map_charge_card_account(workspace_id)


def test_schedule_auto_map_charge_card_employees(db):
    workspace_id = 1

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.auto_map_employees = 'EMAIL'
    configuration.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    configuration.save()

    schedule_auto_map_charge_card_employees(workspace_id=workspace_id)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.async_auto_map_charge_card_account',
        args='{}'.format(workspace_id),
    ).first()
    
    assert schedule.func == 'apps.mappings.tasks.async_auto_map_charge_card_account'

    configuration.corporate_credit_card_expenses_object = 'BILL'
    configuration.save()

    schedule_auto_map_charge_card_employees(workspace_id=workspace_id)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.async_auto_map_charge_card_account',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None


def test_auto_create_vendors_as_merchants(db, mocker):
    workspace_id = 1
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Merchants.post_bulk',
        return_value=[]
    )

    mocker.patch(
        'fyle_integrations_platform_connector.apis.Merchants.sync',
        return_value=[]
    )

    mocker.patch(
        'sageintacctsdk.apis.Vendors.get_all',
        return_value=intacct_data['get_vendors']
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Merchants.get',
        return_value=fyle_data['get_merchant']
    )

    merchant = ExpenseAttribute.objects.filter(value='Ashwin from NetSuite').first()
    merchant.value = 'random'
    merchant.save()

    merchants = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    mappings = Mapping.objects.filter(workspace_id=workspace_id, destination_type='VENDOR').count()
    
    assert merchants == 68
    assert mappings == 0

    auto_create_vendors_as_merchants(workspace_id=workspace_id)

    merchants = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    mappings = Mapping.objects.filter(workspace_id=workspace_id, destination_type='VENDOR').count()
    
    assert mappings == 0

    with mock.patch('fyle_integrations_platform_connector.apis.Merchants.sync') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response='invalid params')
        auto_create_vendors_as_merchants(workspace_id=workspace_id)

        mock_call.side_effect = FyleInvalidTokenError(msg='invalid params', response='invalid params')
        auto_create_vendors_as_merchants(workspace_id=workspace_id)

        mock_call.side_effect = InternalServerError(msg='internal server error', response='internal server error')
        auto_create_vendors_as_merchants(workspace_id=workspace_id)

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        auto_create_vendors_as_merchants(workspace_id=workspace_id)

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.delete()

    response = auto_create_vendors_as_merchants(workspace_id)

    assert response == None


def test_post_merchants(mocker, db):
    workspace_id = 1
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Merchants.post_bulk',
        return_value=[]
    )

    mocker.patch(
        'fyle_integrations_platform_connector.apis.Merchants.sync',
        return_value=[]
    )

    mocker.patch(
        'fyle_integrations_platform_connector.apis.Merchants.get',
        return_value=fyle_data['get_merchant']
    )

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_connection = PlatformConnector(fyle_credentials)

    post_merchants(fyle_connection, workspace_id, False)


def test_auto_import_and_map_fyle_fields(db):
    workspace_id = 1

    auto_import_and_map_fyle_fields(workspace_id=workspace_id)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None
