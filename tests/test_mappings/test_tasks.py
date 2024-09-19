from django_q.models import Schedule
from fyle_accounting_mappings.models import (
    DestinationAttribute,
    Mapping,
    EmployeeMapping,
    ExpenseAttribute
)
from apps.mappings.tasks import *
from ..test_sageintacct.fixtures import data as intacct_data
from ..test_fyle.fixtures import data as fyle_data
from apps.workspaces.models import Configuration
from apps.fyle.models import ExpenseGroup
from fyle.platform.exceptions import (
    InvalidTokenError as FyleInvalidTokenError,
    InternalServerError
)


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


def test_async_auto_map_employees(mocker, db):
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Vendors.get_all_generator',
        return_value=intacct_data['get_vendors']
    )

    mocker.patch(
        'sageintacctsdk.apis.Employees.get_all_generator',
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


def test_sync_sage_intacct_attributes(mocker, db, create_dependent_field_setting, create_cost_type):
    workspace_id = 1
    mocker.patch(
        'sageintacctsdk.apis.Locations.get_all_generator',
        return_value=intacct_data['get_locations']
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=5
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all_generator',
        return_value=intacct_data['get_projects']
    )
    mocker.patch(
        'sageintacctsdk.apis.Departments.get_all_generator',
        return_value=intacct_data['get_departments']
    )
    mocker.patch(
        'sageintacctsdk.apis.Vendors.get_all_generator',
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
    
    mock_call = mocker.patch(
        'fyle_integrations_platform_connector.apis.Employees.sync',
        return_value=[]
    )
    mocker.patch(
        'fyle_accounting_mappings.helpers.EmployeesAutoMappingHelper.ccc_mapping',
        return_value=None
    )

    async_auto_map_charge_card_account(workspace_id)

    mock_call.side_effect = FyleInvalidTokenError('Invalid Token')
    async_auto_map_charge_card_account(workspace_id)

    mock_call.side_effect = InternalServerError('Internal Server Error')
    async_auto_map_charge_card_account(workspace_id)

    assert mock_call.call_count == 3


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
