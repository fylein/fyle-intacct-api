from unittest import mock
from fyle_integrations_platform_connector import PlatformConnector
from fyle_accounting_mappings.models import (
    DestinationAttribute,
    ExpenseAttribute,
    Mapping,
    MappingSetting
)

from apps.workspaces.models import FyleCredential, Workspace, Configuration
from apps.mappings.imports.modules.cost_centers import CostCenter, disable_cost_centers
from .fixtures import cost_center_data


def test_sync_expense_atrributes(mocker, db):
    """
    Test sync expense attributes
    """
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.workspace.fyle_org_id = 'ortL3T2BabCW'
    fyle_credentials.workspace.save()

    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    mocker.patch(
        'fyle.platform.apis.v1.admin.CostCenters.list_all',
        return_value=[]
    )

    cost_center_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='COST_CENTER').count()
    assert cost_center_count == 566

    category = CostCenter(workspace_id, 'CLASS', None)
    category.sync_expense_attributes(platform)

    cost_center_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='COST_CENTER').count()
    assert cost_center_count == 566

    mocker.patch(
        'fyle.platform.apis.v1.admin.CostCenters.list_all',
        return_value=cost_center_data['create_new_auto_create_cost_centers_expense_attributes_1']
    )

    category.sync_expense_attributes(platform)

    cost_center_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='COST_CENTER').count()
    # NOTE : we are not using cost_center_data['..'][0]['count'] because some duplicates where present in the data
    assert cost_center_count == 566 + 7


def test_auto_create_destination_attributes(mocker, db):
    """
    Test auto create destination attributes
    """
    cost_center = CostCenter(1, 'CLASS', None)
    cost_center.sync_after = None

    Workspace.objects.filter(id=1).update(fyle_org_id='ortL3T2BabCW')

    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(workspace_id=1, source_type='COST_CENTER', destination_type='CLASS').delete()
    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='CLASS').delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='COST_CENTER').delete()

    # create new case for projects import
    with mock.patch('fyle.platform.apis.v1.admin.CostCenters.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.CostCenters.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.Classes.get_all_generator',
            return_value=cost_center_data['create_new_auto_create_cost_centers_destination_attributes']
        )
        mocker.patch(
            'sageintacctsdk.apis.Classes.count',
            return_value=7
        )
        mock_call.side_effect = [
            cost_center_data['create_new_auto_create_cost_centers_expense_attributes_0'],
            cost_center_data['create_new_auto_create_cost_centers_expense_attributes_1']
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'COST_CENTER').count()

        assert expense_attributes_count == 0

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='COST_CENTER', destination_type='CLASS').count()

        assert mappings_count == 0

        cost_center.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'COST_CENTER').count()

        assert expense_attributes_count == 7

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='COST_CENTER', destination_type='CLASS').count()

        assert mappings_count == 7

    # create new project sub-sequent run (we will be adding 2 new CLASSES)
    with mock.patch('fyle.platform.apis.v1.admin.CostCenters.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.CostCenters.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.Classes.get_all_generator',
            return_value=cost_center_data['create_new_auto_create_cost_centers_destination_attributes_subsequent_run']
        )
        mocker.patch(
            'sageintacctsdk.apis.Classes.count',
            return_value=7 + 2
        )
        mock_call.side_effect = [
            [],
            cost_center_data['create_new_auto_create_cost_centers_expense_attributes_2']
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'COST_CENTER').count()

        assert expense_attributes_count == 7

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='COST_CENTER', destination_type='CLASS').count()

        assert mappings_count == 7

        cost_center.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'COST_CENTER').count()

        assert expense_attributes_count == 7 + 2

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='COST_CENTER', destination_type='CLASS').count()

        assert mappings_count == 7 + 2


def test_construct_fyle_payload(db):
    """
    Test construct fyle payload
    """
    cost_center = CostCenter(1, 'CLASS', None)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='CLASS')
    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = cost_center.get_auto_sync_permission()

    fyle_payload = cost_center.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed
    )

    assert fyle_payload == cost_center_data['create_fyle_cost_center_payload_create_new_case']


def test_get_existing_fyle_attributes(
    db,
    add_cost_center_mappings,
    add_configuration
):
    """
    Test get existing fyle attributes
    """
    cost_center = CostCenter(98, 'DEPARTMENT', None)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=98, attribute_type='DEPARTMENT')
    paginated_destination_attributes_without_duplicates = cost_center.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = cost_center.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {}

    # with code prepending
    cost_center.prepend_code_to_name = True
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=98, attribute_type='DEPARTMENT', code__isnull=False)
    paginated_destination_attributes_without_duplicates = cost_center.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = cost_center.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {'123: cre platform': '10065', '123: integrations cre': '10082'}


def test_construct_fyle_payload_with_code(
    db,
    add_cost_center_mappings,
    add_configuration
):
    """
    Test construct fyle payload with code
    """
    cost_center = CostCenter(98, 'DEPARTMENT', None, True)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=98, attribute_type='DEPARTMENT')
    paginated_destination_attributes_without_duplicates = cost_center.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = cost_center.get_existing_fyle_attributes(paginated_destination_attribute_values)

    # already exists
    fyle_payload = cost_center.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == []

    # create new case
    existing_fyle_attributes_map = {}
    fyle_payload = cost_center.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == cost_center_data["create_fyle_cost_center_payload_with_code_create_new_case"]


def test_disable_cost_centers(
    db,
    mocker,
    add_cost_center_mappings,
    add_configuration
):
    """
    Test disable cost centers
    """
    workspace_id = 98

    mocker.patch(
        'django.db.models.signals.post_save.send'
    )
    FyleCredential.objects.create(
        workspace_id=workspace_id,
        refresh_token='refresh_token',
        cluster_domain='cluster_domain'
    )
    MappingSetting.objects.create(
        workspace_id=workspace_id,
        source_field='COST_CENTER',
        destination_field='PROJECT',
        import_to_fyle=True,
        is_custom=False
    )

    cost_centers_to_disable = {
        'destination_id': {
            'value': 'old_cost_center',
            'updated_value': 'new_cost_center',
            'code': 'old_cost_center_code',
            'updated_code': 'old_cost_center_code'
        }
    }

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='COST_CENTER',
        display_name='CostCenter',
        value='old_cost_center',
        source_id='source_id',
        active=True
    )

    mock_platform = mocker.patch('apps.mappings.imports.modules.cost_centers.PlatformConnector')
    bulk_post_call = mocker.patch.object(mock_platform.return_value.cost_centers, 'post_bulk')

    disable_cost_centers(workspace_id, cost_centers_to_disable, is_import_to_fyle_enabled=True)

    assert bulk_post_call.call_count == 1

    cost_centers_to_disable = {
        'destination_id': {
            'value': 'old_cost_center_2',
            'updated_value': 'new_cost_center',
            'code': 'old_cost_center_code',
            'updated_code': 'new_cost_center_code'
        }
    }

    disable_cost_centers(workspace_id, cost_centers_to_disable, is_import_to_fyle_enabled=True)
    assert bulk_post_call.call_count == 1

    # Test disable projects with code in naming
    import_settings = Configuration.objects.get(workspace_id=workspace_id)
    import_settings.import_code_fields = ['PROJECT']
    import_settings.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='COST_CENTER',
        display_name='CostCenter',
        value='old_cost_center_code: old_cost_center',
        source_id='source_id_123',
        active=True
    )

    cost_centers_to_disable = {
        'destination_id': {
            'value': 'old_cost_center',
            'updated_value': 'new_cost_center',
            'code': 'old_cost_center_code',
            'updated_code': 'old_cost_center_code'
        }
    }

    payload = [
        {
            'name': 'old_cost_center_code: old_cost_center',
            'is_enabled': False,
            'id': 'source_id_123',
            'description': 'Cost Center - old_cost_center_code: old_cost_center, Id - destination_id'
        }
    ]

    bulk_payload = disable_cost_centers(workspace_id, cost_centers_to_disable, is_import_to_fyle_enabled=True)
    assert bulk_payload == payload
