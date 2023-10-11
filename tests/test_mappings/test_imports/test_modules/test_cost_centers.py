import pytest
from unittest import mock
from apps.mappings.imports.modules.cost_centers import CostCenter
from fyle_accounting_mappings.models import (
    DestinationAttribute,
    ExpenseAttribute,
    Mapping
)
from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential
from .fixtures import cost_center_data


def test_sync_expense_atrributes(mocker, db):
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.CostCenters.list_all',
        return_value=[]
    )

    cost_center_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='COST_CENTER').count()
    assert cost_center_count == 566

    category = CostCenter(workspace_id, 'CLASS', None)
    category.sync_expense_attributes(platform)

    cost_center_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='COST_CENTER').count()
    assert cost_center_count == 566

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.CostCenters.list_all',
        return_value=cost_center_data['create_new_auto_create_cost_centers_expense_attributes_1']
    )

    category.sync_expense_attributes(platform)

    cost_center_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='COST_CENTER').count()
    # NOTE : we are not using cost_center_data['..'][0]['count'] because some duplicates where present in the data
    assert cost_center_count == 566 + 7

def test_auto_create_destination_attributes(mocker, db):
    cost_center = CostCenter(1, 'CLASS', None)
    cost_center.sync_after = None

    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(workspace_id=1, source_type='COST_CENTER', destination_type='CLASS').delete()
    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='CLASS').delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='COST_CENTER').delete()

    # create new case for projects import
    with mock.patch('fyle.platform.apis.v1beta.admin.CostCenters.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.CostCenters.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.Classes.get_all',
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
    with mock.patch('fyle.platform.apis.v1beta.admin.CostCenters.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.CostCenters.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.Classes.get_all',
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
