import pytest
from unittest import mock
from apps.mappings.imports.modules.merchants import Merchant
from fyle_accounting_mappings.models import (
    DestinationAttribute,
    ExpenseAttribute,
    Mapping
)
from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential
from .fixtures import merchants_data


def test_sync_expense_atrributes(mocker, db):
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)
    ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='MERCHANT').delete()

    merchants_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='MERCHANT').count()
    assert merchants_count == 0

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.expense_fields.list_all',
        return_value=[]
    )

    merchant = Merchant(workspace_id, 'VENDOR', None)
    merchant.sync_expense_attributes(platform)

    merchants_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='MERCHANT').count()
    assert merchants_count == 0

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.expense_fields.list_all',   
        return_value=merchants_data['create_new_auto_create_merchants_expense_attributes_1']
    )

    merchant.sync_expense_attributes(platform)

    merchants_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='MERCHANT').count()
    # NOTE : we are not using cost_center_data['..'][0]['count'] because some duplicates where present in the data
    assert merchants_count == 72

def test_sync_destination_atrributes(mocker, db):
    mocker.patch(
        'sageintacctsdk.apis.Vendors.get_all',
        return_value=merchants_data['get_vendors_destination_attributes']
    )
    workspace_id = 1

    vendors_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    assert vendors_count == 68

    tax_group = Merchant(workspace_id, 'VENDOR', None)
    tax_group.sync_destination_attributes('VENDOR')

    vendors_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    assert vendors_count == 75