from fyle_accounting_mappings.models import DestinationAttribute, EmployeeMapping, ExpenseAttribute, Mapping

from apps.fyle.models import ExpenseGroup
from apps.mappings.tasks import (
    check_and_create_ccc_mappings,
    construct_tasks_and_chain_import_fields_to_fyle,
    initiate_import_to_fyle,
    resolve_expense_attribute_errors,
    sync_sage_intacct_attributes,
    auto_map_accounting_fields
)
from apps.tasks.models import Error
from apps.workspaces.models import Configuration, FeatureConfig, SageIntacctCredential
from workers.helpers import WorkerActionEnum, RoutingKeyEnum
from tests.test_fyle.fixtures import data as fyle_data
from tests.test_sageintacct.fixtures import data as intacct_data


def test_resolve_expense_attribute_errors(db):
    """
    Test resolve expense attribute errors
    """
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
    """
    Test async auto map employees
    """
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
        'fyle.platform.apis.v1.admin.Employees.list_all',
        return_value=fyle_data['get_all_employees']
    )

    general_settings = Configuration.objects.get(workspace_id=workspace_id)

    general_settings.employee_field_mapping = 'EMPLOYEE'
    general_settings.save()

    auto_map_accounting_fields(workspace_id)

    employee_mappings = EmployeeMapping.objects.filter(workspace_id=workspace_id).count()
    assert employee_mappings == 1

    general_settings.employee_field_mapping = 'VENDOR'
    general_settings.save()

    auto_map_accounting_fields(workspace_id)

    employee_mappings = EmployeeMapping.objects.filter(workspace_id=workspace_id).count()
    assert employee_mappings == 1


def test_sync_sage_intacct_attributes(mocker, db, create_dependent_field_setting, create_cost_type):
    """
    Test sync sage intacct attributes
    """
    workspace_id = 1
    mocker.patch(
        'sageintacctsdk.apis.Locations.count',
        return_value=1
    )
    mocker.patch(
        'sageintacctsdk.apis.Departments.count',
        return_value=1
    )
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
    mocker.patch(
        'sageintacctsdk.apis.CostTypes.count',
        return_value=0
    )

    mocker.patch(
        'sageintacctsdk.apis.Allocations.get_all_generator',
        return_value=[]
    )

    mock_platform = mocker.patch('fyle_integrations_imports.modules.projects.PlatformConnector')
    mocker.patch.object(mock_platform.return_value.projects, 'post_bulk')
    mocker.patch.object(mock_platform.return_value.projects, 'sync')

    sync_sage_intacct_attributes('DEPARTMENT', workspace_id=workspace_id)
    sync_sage_intacct_attributes('LOCATION', workspace_id=workspace_id)
    sync_sage_intacct_attributes('PROJECT', workspace_id=workspace_id)
    sync_sage_intacct_attributes('VENDOR', workspace_id=workspace_id)

    sync_sage_intacct_attributes('COST_TYPE', workspace_id)

    sync_sage_intacct_attributes('ALLOCATION', workspace_id)

    projects = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    mappings = Mapping.objects.filter(workspace_id=workspace_id, destination_type='PROJECT').count()

    assert mappings == projects


def test_check_and_create_ccc_mappings(mocker, db):
    """
    Test check and create CCC mappings
    """
    workspace_id = 1

    mock_bulk_create = mocker.patch(
        'fyle_accounting_mappings.models.CategoryMapping.bulk_create_ccc_category_mappings'
    )

    Configuration.objects.filter(workspace_id=999).delete()
    check_and_create_ccc_mappings(workspace_id=999)
    mock_bulk_create.assert_not_called()

    mock_bulk_create.reset_mock()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'BILL'
    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()

    check_and_create_ccc_mappings(workspace_id=workspace_id)
    mock_bulk_create.assert_not_called()

    mock_bulk_create.reset_mock()

    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.corporate_credit_card_expenses_object = 'BILL'
    configuration.save()

    check_and_create_ccc_mappings(workspace_id=workspace_id)
    mock_bulk_create.assert_not_called()

    mock_bulk_create.reset_mock()

    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    check_and_create_ccc_mappings(workspace_id=workspace_id)
    mock_bulk_create.assert_called_once_with(workspace_id)


def test_initiate_import_to_fyle_with_account_destination(mocker, db):
    """
    Test initiate_import_to_fyle with ACCOUNT destination field
    """
    workspace_id = 1

    SageIntacctCredential.objects.filter(workspace_id=workspace_id).update(is_expired=False)

    mock_chain_import = mocker.patch('apps.mappings.tasks.chain_import_fields_to_fyle', return_value=None)

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.import_categories = True
    configuration.reimbursable_expenses_object = 'BILL'
    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()

    initiate_import_to_fyle(workspace_id)

    mock_chain_import.assert_called_once()

    call_args = mock_chain_import.call_args

    if call_args[0] and len(call_args[0]) > 1:
        task_settings = call_args[0].get('task_settings')
    else:
        task_settings = call_args.kwargs.get('task_settings', {})

    assert 'import_categories' in task_settings
    import_categories = task_settings['import_categories']
    assert import_categories['destination_field'] == 'ACCOUNT'
    assert 'accounts' in import_categories['destination_sync_methods']
    assert import_categories['is_auto_sync_enabled'] == True
    assert import_categories['is_3d_mapping'] == True


def test_construct_tasks_and_chain_import_fields_to_fyle_with_rabbitmq(mocker, db):
    """
    Test construct_tasks_and_chain_import_fields_to_fyle with rabbitmq enabled
    """
    workspace_id = 1

    # Mock FeatureConfig with rabbitmq enabled
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_via_rabbitmq = True
    feature_config.save()

    # Mock publish_to_rabbitmq
    mock_publish = mocker.patch('apps.mappings.tasks.publish_to_rabbitmq')
    mock_initiate_import = mocker.patch('apps.mappings.tasks.initiate_import_to_fyle')

    # Call the function
    construct_tasks_and_chain_import_fields_to_fyle(workspace_id)

    # Verify publish_to_rabbitmq was called with correct payload
    expected_payload = {
        'workspace_id': workspace_id,
        'action': WorkerActionEnum.IMPORT_DIMENSIONS_TO_FYLE.value,
        'data': {
            'workspace_id': workspace_id,
            'run_in_rabbitmq_worker': True
        }
    }

    mock_publish.assert_called_once_with(
        payload=expected_payload,
        routing_key=RoutingKeyEnum.IMPORT.value
    )

    # Verify initiate_import_to_fyle was NOT called
    mock_initiate_import.assert_not_called()


def test_construct_tasks_and_chain_import_fields_to_fyle_without_rabbitmq(mocker, db):
    """
    Test construct_tasks_and_chain_import_fields_to_fyle with rabbitmq disabled
    """
    workspace_id = 1

    # Mock FeatureConfig with rabbitmq disabled
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_via_rabbitmq = False
    feature_config.save()

    # Mock publish_to_rabbitmq and initiate_import_to_fyle
    mock_publish = mocker.patch('apps.mappings.tasks.publish_to_rabbitmq')
    mock_initiate_import = mocker.patch('apps.mappings.tasks.initiate_import_to_fyle')

    # Call the function
    construct_tasks_and_chain_import_fields_to_fyle(workspace_id)

    # Verify initiate_import_to_fyle was called with correct parameters
    mock_initiate_import.assert_called_once_with(workspace_id=workspace_id)

    # Verify publish_to_rabbitmq was NOT called
    mock_publish.assert_not_called()
