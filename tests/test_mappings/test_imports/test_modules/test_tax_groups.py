import pytest
from unittest import mock
from apps.mappings.imports.modules.tax_groups import TaxGroup
from fyle_accounting_mappings.models import (
    DestinationAttribute,
    ExpenseAttribute,
    Mapping
)
from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential
from .fixtures import tax_groups_date


def test_sync_destination_atrributes(mocker, db):
    mocker.patch(
        'sageintacctsdk.apis.TaxDetails.get_all',
        return_value=tax_groups_date['get_tax_details_destination_attributes']
    )
    workspace_id = 1

    tax_details_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_DETAIL').count()
    assert tax_details_count == 54

    tax_group = TaxGroup(workspace_id, 'TAX_DETAIL', None)
    tax_group.sync_destination_attributes('TAX_DETAIL')

    tax_details_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_DETAIL').count()
    assert tax_details_count == 58


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
        'fyle_integrations_platform_connector.apis.TaxGroups.sync',
        return_value=[]
    )

    tax_group = TaxGroup(workspace_id, 'TAX_DETAIL', None)
    tax_group.sync_expense_attributes(platform)

    tax_group_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_GROUP').count()
    assert tax_group_count == 0

    mocker.patch(
        'fyle_integrations_platform_connector.apis.TaxGroups.sync',
        return_value=tax_groups_date['create_new_auto_create_tax_groups_expense_attributes_1']
    )

    tax_group.sync_expense_attributes(platform)

    tax_group_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='TAX_GROUP').count()
    # NOTE : we are not using tax_groups_data['..'][0]['count'] because some duplicates where present in the data
    assert tax_group_count == 382

# def test_auto_create_destination_attributes(mocker, db):
#     pass

# def test_construct_fyle_payload(db):
#     pass

