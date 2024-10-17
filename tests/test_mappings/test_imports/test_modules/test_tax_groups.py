import pytest
from unittest import mock
from apps.mappings.imports.modules.tax_groups import TaxGroup
from fyle_accounting_mappings.models import (
    DestinationAttribute,
    ExpenseAttribute,
    Mapping
)
from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential, Workspace
from .fixtures import tax_groups_data


def test_sync_destination_atrributes(mocker, db):
    mocker.patch(
        'sageintacctsdk.apis.TaxDetails.count',
        return_value=100
    )
    mocker.patch(
        'sageintacctsdk.apis.TaxDetails.get_all_generator',
        return_value=tax_groups_data['get_tax_details_destination_attributes']
    )
    workspace_id = 1

    tax_details_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_DETAIL').count()
    assert tax_details_count == 54

    tax_group = TaxGroup(workspace_id, 'TAX_DETAIL', None)
    tax_group.sync_destination_attributes('TAX_DETAIL')

    tax_details_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_DETAIL').count()
    assert tax_details_count == 59


def test_sync_expense_atrributes(mocker, db):
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    # delete all expense attributes, destination attributes and mappings
    Mapping.objects.filter(workspace_id=1, source_type='TAX_GROUP', destination_type='TAX_DETAIL').delete()
    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='TAX_DETAIL').delete()
    ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_GROUP').delete()

    tax_group_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_GROUP').count()
    assert tax_group_count == 0

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.TaxGroups.list_all',
        return_value=[]
    )

    tax_group = TaxGroup(workspace_id, 'TAX_DETAIL', None)
    tax_group.sync_expense_attributes(platform)

    tax_group_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_GROUP').count()
    assert tax_group_count == 0

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.TaxGroups.list_all',
        return_value=tax_groups_data['create_new_auto_create_tax_groups_expense_attributes_0']
    )

    tax_group.sync_expense_attributes(platform)

    tax_group_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_GROUP').count()
    # NOTE : we are not using tax_groups_data['..'][0]['count'] because some duplicates where present in the data
    assert tax_group_count == 68

def test_auto_create_destination_attributes(mocker, db):
    workspace_id = 1
    tax_group = TaxGroup(workspace_id, 'TAX_DETAIL', None)
    tax_group.sync_after = None

    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(id=160).delete()
    Mapping.objects.filter(workspace_id=workspace_id, source_type='TAX_GROUP', destination_type='TAX_DETAIL').delete()
    DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_DETAIL').delete()
    ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_GROUP').delete()

    # create new case for tax-groups import
    with mock.patch('fyle.platform.apis.v1beta.admin.TaxGroups.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.TaxGroups.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.TaxDetails.count',
            return_value=100
        )
        mocker.patch(
            'sageintacctsdk.apis.TaxDetails.get_all_generator',
            return_value=tax_groups_data['get_tax_details_destination_attributes']
        )

        mock_call.side_effect = [
            tax_groups_data['create_new_auto_create_tax_groups_expense_attributes_0'],
            tax_groups_data['create_new_auto_create_tax_groups_expense_attributes_1'] 
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type = 'TAX_GROUP').count()

        assert expense_attributes_count == 0

        mappings_count = Mapping.objects.filter(workspace_id=workspace_id, source_type='TAX_GROUP', destination_type='TAX_DETAIL').count()
        
        assert mappings_count == 0

        tax_group.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type = 'TAX_GROUP').count()

        assert expense_attributes_count == 69

        mappings_count = Mapping.objects.filter(workspace_id=workspace_id, source_type='TAX_GROUP', destination_type='TAX_DETAIL').count()
        
        assert mappings_count == 59

    # create new tax-groups sub-sequent run (we will be adding 2 new tax-details)
    with mock.patch('fyle.platform.apis.v1beta.admin.TaxGroups.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.TaxGroups.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.TaxDetails.get_all_generator',
            return_value=tax_groups_data['get_tax_details_destination_attributes_subsequent_run']
        )

        mock_call.side_effect = [
            [],
            tax_groups_data['create_new_auto_create_tax_groups_expense_attributes_2'] 
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type = 'TAX_GROUP').count()

        assert expense_attributes_count == 69

        mappings_count = Mapping.objects.filter(workspace_id=workspace_id, source_type='TAX_GROUP', destination_type='TAX_DETAIL').count()
        
        assert mappings_count == 59

        tax_group.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type = 'TAX_GROUP').count()

        assert expense_attributes_count == 69+2

        mappings_count = Mapping.objects.filter(workspace_id=workspace_id, source_type='TAX_GROUP', destination_type='TAX_DETAIL').count()
        
        assert mappings_count == 59+2


def test_construct_fyle_payload(db):
    tax_group = TaxGroup(1, 'TAX_DETAIL', None)
    tax_group.sync_after = None

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='TAX_DETAIL')
    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = tax_group.get_auto_sync_permission()

    fyle_payload = tax_group.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed
    )

    assert fyle_payload == tax_groups_data['create_fyle_tax_details_payload_create_new_case']
