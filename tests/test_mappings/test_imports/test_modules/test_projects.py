from apps.workspaces.models import Configuration
from apps.mappings.imports.modules.projects import Project, disable_projects
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute
from apps.sage_intacct.models import CostType, DependentFieldSetting
from apps.sage_intacct.dependent_fields import update_and_disable_cost_code
from .fixtures import data


def test_construct_fyle_payload(db):
    project = Project(1, 'PROJECT', None)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT')
    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = project.get_auto_sync_permission()

    fyle_payload = project.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed
    )

    assert fyle_payload == data['create_fyle_project_payload_create_new_case']

    # disable case
    DestinationAttribute.objects.filter(
        workspace_id=1,
        attribute_type='PROJECT',
        value__in=['Fyle Sage Intacct Integration','Platform APIs']
    ).update(active=False)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT')

    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes]
    existing_fyle_attributes_map = project.get_existing_fyle_attributes(paginated_destination_attribute_values)

    fyle_payload = project.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed
    )

    assert fyle_payload == data['create_fyle_project_payload_create_disable_case']


def test_disable_projects(
    db,
    mocker,
    add_project_mappings,
    add_configuration
):
    workspace_id = 1

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project',
            'updated_value': 'new_project',
            'code': 'old_project_code',
            'updated_code': 'old_project_code'
        }
    }

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='PROJECT',
        display_name='Project',
        value='old_project',
        source_id='source_id',
        active=True
    )

    mock_platform = mocker.patch('apps.mappings.imports.modules.projects.PlatformConnector')
    bulk_post_call = mocker.patch.object(mock_platform.return_value.projects, 'post_bulk')
    sync_call = mocker.patch.object(mock_platform.return_value.projects, 'sync')

    disable_cost_code_call = mocker.patch('apps.mappings.imports.modules.projects.update_and_disable_cost_code')

    disable_projects(workspace_id, projects_to_disable)

    assert bulk_post_call.call_count == 1
    assert sync_call.call_count == 2
    disable_cost_code_call.assert_called_once()

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project_2',
            'updated_value': 'new_project',
            'code': 'old_project_code',
            'updated_code': 'new_project_code'
        }
    }

    disable_projects(workspace_id, projects_to_disable)
    assert bulk_post_call.call_count == 1
    assert sync_call.call_count == 4
    disable_cost_code_call.call_count == 2

    # Test disable projects with code in naming
    import_settings = Configuration.objects.get(workspace_id=workspace_id)
    import_settings.import_code_fields = ['PROJECT']
    import_settings.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='PROJECT',
        display_name='Project',
        value='old_project_code old_project',
        source_id='source_id_123',
        active=True
    )

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project',
            'updated_value': 'new_project',
            'code': 'old_project_code',
            'updated_code': 'old_project_code'
        }
    }

    payload = [{
        'name': 'old_project_code old_project',
        'code': 'destination_id',
        'description': 'Sage Intacct Project - {0}, Id - {1}'.format(
            'old_project_code old_project',
            'destination_id'
        ),
        'is_enabled': False,
        'id': 'source_id_123'
    }]

    assert disable_projects(workspace_id, projects_to_disable) == payload


def test_update_and_disable_cost_code(
    db,
    mocker,
    add_dependent_field_setting,
    add_cost_type,
    add_configuration
):
    workspace_id = 1

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project',
            'updated_value': 'new_project',
            'code': 'new_project_code',
            'updated_code': 'new_project_code'
        }
    }

    import_settings = Configuration.objects.get(workspace_id=workspace_id)
    use_code_in_naming = False
    if 'PROJECT' in import_settings.import_code_fields:
        use_code_in_naming = True

    cost_type = CostType.objects.filter(workspace_id=workspace_id).first()
    cost_type.project_name = 'old_project'
    cost_type.project_id = 'destination_id'
    cost_type.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='PROJECT',
        display_name='Project',
        value='old_project',
        source_id='source_id',
        active=True
    )

    mock_platform = mocker.patch('apps.mappings.imports.modules.projects.PlatformConnector')
    mocker.patch.object(mock_platform.return_value.dependent_fields, 'bulk_post_dependent_expense_field_values')

    update_and_disable_cost_code(workspace_id, projects_to_disable, mock_platform, use_code_in_naming)

    updated_cost_type = CostType.objects.filter(workspace_id=workspace_id, project_id='new_project_code').first()
    assert updated_cost_type.project_name == 'new_project'

    # Test with code in naming
    use_code_in_naming = True

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='PROJECT',
        display_name='Project',
        value='old_project_code old_project',
        source_id='source_id_123',
        active=True
    )

    update_and_disable_cost_code(workspace_id, projects_to_disable, mock_platform, use_code_in_naming)
    assert updated_cost_type.project_name == 'new_project'
    assert updated_cost_type.project_id == 'new_project_code'

    # Delete dependent field setting
    updated_cost_type.project_name = 'old_project'
    updated_cost_type.save()

    DependentFieldSetting.objects.get(workspace_id=workspace_id).delete()

    update_and_disable_cost_code(workspace_id, projects_to_disable, mock_platform, use_code_in_naming)

    updated_cost_type = CostType.objects.filter(workspace_id=workspace_id, project_id='new_project_code').first()
    assert updated_cost_type.project_name == 'old_project'
