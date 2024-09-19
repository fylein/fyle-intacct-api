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
        return_value=merchants_data['create_new_auto_create_merchants_expense_attributes_0']
    )

    merchant.sync_expense_attributes(platform)

    merchants_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='MERCHANT').count()
    # NOTE : we are not using cost_center_data['..'][0]['count'] because some duplicates where present in the data
    assert merchants_count == 72

def test_sync_destination_atrributes(mocker, db):
    mocker.patch(
        'sageintacctsdk.apis.Vendors.get_all_generator',
        return_value=merchants_data['get_vendors_destination_attributes']
    )
    workspace_id = 1

    vendors_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    assert vendors_count == 68

    tax_group = Merchant(workspace_id, 'VENDOR', None)
    tax_group.sync_destination_attributes('VENDOR')

    vendors_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    assert vendors_count == 75

def test_auto_create_destination_attributes(mocker, db):
    workspace_id = 1
    merchant = Merchant(workspace_id, 'VENDOR', None)
    merchant.sync_after = None

    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(workspace_id=1, source_type='MERCHANT', destination_type='VENDOR').delete()
    # DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR').delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='MERCHANT').delete()

    # create new case for tax-groups import
    with mock.patch('fyle.platform.apis.v1beta.admin.expense_fields.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Merchants.post',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.Vendors.get_all_generator',
            return_value=merchants_data['get_vendors_destination_attributes']
        )

        mock_call.side_effect = [
            merchants_data['create_new_auto_create_merchants_expense_attributes_0'],
            merchants_data['create_new_auto_create_merchants_expense_attributes_1'] 
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'MERCHANT').count()

        assert expense_attributes_count == 0

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='MERCHANT', destination_type='VENDOR').count()
        
        assert mappings_count == 0

        merchant.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'MERCHANT').count()

        assert expense_attributes_count == 73

        # We dont create any mapping for VENDOR and MERCHANT, so this should be 0
        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='MERCHANT', destination_type='VENDOR').count()
        
        assert mappings_count == 0

    # create new tax-groups sub-sequent run (we will be adding 2 new tax-details)
    with mock.patch('fyle.platform.apis.v1beta.admin.expense_fields.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Merchants.post',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.Vendors.get_all_generator',
            return_value=merchants_data['get_vendors_destination_attributes_subsequent_run']
        )

        mock_call.side_effect = [
            merchants_data['create_new_auto_create_merchants_expense_attributes_1'],
            merchants_data['create_new_auto_create_merchants_expense_attributes_2'] 
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'MERCHANT').count()

        assert expense_attributes_count == 73

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='MERCHANT', destination_type='VENDOR').count()
        
        assert mappings_count == 0

        merchant.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'MERCHANT').count()

        assert expense_attributes_count == 73+2

        # We dont create any mapping for VENDOR and MERCHANT, so this should be 0
        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='MERCHANT', destination_type='VENDOR').count()
        
        assert mappings_count == 0


def test_construct_fyle_payload(db):
    workspace_id = 1
    merchant = Merchant(workspace_id, 'VENDOR', None)
    merchant.sync_after = None

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR')
    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = merchant.get_auto_sync_permission()

    fyle_payload = merchant.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed
    )

    assert fyle_payload == merchants_data['create_fyle_merchants_payload_create_new_case']
