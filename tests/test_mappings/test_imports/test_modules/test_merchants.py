from unittest import mock

from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, Mapping
from fyle_integrations_platform_connector import PlatformConnector

from apps.mappings.constants import SYNC_METHODS
from apps.workspaces.models import Configuration, FyleCredential
from fyle_integrations_imports.modules.merchants import Merchant, disable_merchants
from tests.helper import dict_compare_keys
from tests.test_mappings.test_imports.test_modules.fixtures import merchants_data


def test_sync_expense_atrributes(mocker, db):
    """
    Test sync expense attributes
    """
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)
    ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='MERCHANT').delete()

    merchants_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='MERCHANT').count()
    assert merchants_count == 0

    mocker.patch(
        'fyle.platform.apis.v1.admin.expense_fields.list_all',
        return_value=[]
    )

    merchant = Merchant(workspace_id, 'VENDOR', None, mock.Mock(), [SYNC_METHODS['VENDOR']], False, True)
    merchant.sync_expense_attributes(platform)

    merchants_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='MERCHANT').count()
    assert merchants_count == 0

    mocker.patch(
        'fyle.platform.apis.v1.admin.expense_fields.list_all',
        return_value=merchants_data['create_new_auto_create_merchants_expense_attributes_0']
    )

    merchant.sync_expense_attributes(platform)

    merchants_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='MERCHANT').count()
    # NOTE : we are not using cost_center_data['..'][0]['count'] because some duplicates where present in the data
    assert merchants_count == 72


def test_sync_destination_atrributes(mocker, db):
    """
    Test sync destination attributes
    """
    mocker.patch(
        'sageintacctsdk.apis.Vendors.get_all_generator',
        return_value=merchants_data['get_vendors_destination_attributes']
    )
    workspace_id = 1

    vendors_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    assert vendors_count == 68

    tax_group = Merchant(workspace_id, 'VENDOR', None, mock.Mock(), [SYNC_METHODS['VENDOR']], False, True)
    tax_group.sync_destination_attributes()

    vendors_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='VENDOR').count()
    assert vendors_count == 68


def test_auto_create_destination_attributes(mocker, db):
    """
    Test auto create destination attributes
    """
    workspace_id = 1
    merchant = Merchant(workspace_id, 'VENDOR', None, mock.Mock(), [SYNC_METHODS['VENDOR']], False, True)
    merchant.sync_after = None

    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(workspace_id=1, source_type='MERCHANT', destination_type='VENDOR').delete()
    # DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR').delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='MERCHANT').delete()

    # create new case for tax-groups import
    with mock.patch('fyle.platform.apis.v1.admin.expense_fields.list_all') as mock_call:
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
    with mock.patch('fyle.platform.apis.v1.admin.expense_fields.list_all') as mock_call:
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

        assert expense_attributes_count == 73 + 2

        # We dont create any mapping for VENDOR and MERCHANT, so this should be 0
        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='MERCHANT', destination_type='VENDOR').count()

        assert mappings_count == 0


def test_construct_fyle_payload(db):
    """
    Test construct fyle payload
    """
    workspace_id = 1
    merchant = Merchant(workspace_id, 'VENDOR', None, mock.Mock(), [SYNC_METHODS['VENDOR']], False, True)
    merchant.sync_after = None

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR')
    existing_fyle_attributes_map = {}

    fyle_payload = merchant.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map
    )

    assert dict_compare_keys(fyle_payload, merchants_data['create_fyle_merchants_payload_create_new_case']) == [], 'Keys mismatch for merchant payload'


def test_disable_merchants(db, mocker):
    """
    Test disable merchants
    """
    workspace_id = 1

    # Setup: create a merchant to disable
    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='MERCHANT',
        display_name='Merchant',
        value='old_merchant',
        source_id='source_id',
        active=True
    )

    DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='VENDOR',
        value='old_merchant',
        active=True,
        destination_id='old_merchant_code',
        code='old_merchant_code'
    )

    merchants_to_disable = {
        'destination_id': {
            'value': 'old_merchant',
            'updated_value': 'new_merchant',
            'code': 'old_merchant_code',
            'updated_code': 'old_merchant_code'
        }
    }

    # Patch PlatformConnector and the post method
    mock_platform = mocker.patch('fyle_integrations_imports.modules.merchants.PlatformConnector')
    post_call = mocker.patch.object(mock_platform.return_value.merchants, 'post')

    # Patch prepend_code_to_name to just return the value for simplicity
    mocker.patch('apps.mappings.helpers.prepend_code_to_name', side_effect=lambda prepend_code_in_name, value, code: value if not prepend_code_in_name else f"{code}: {value}")

    # Patch import_string for configuration model path and Configuration
    def import_string_side_effect(path):
        if path == 'apps.workspaces.helpers.get_import_configuration_model_path':
            return lambda: 'apps.workspaces.models.Configuration'
        elif path == 'apps.workspaces.models.Configuration':
            return Configuration
        elif path == 'apps.mappings.helpers.prepend_code_to_name':
            return lambda prepend_code_in_name, value, code: value if not prepend_code_in_name else f"{code}: {value}"
        return None

    mocker.patch('fyle_integrations_imports.modules.merchants.import_string', side_effect=import_string_side_effect)

    # Actually call the function
    bulk_payload = disable_merchants(workspace_id, merchants_to_disable, is_import_to_fyle_enabled=True, attribute_type='VENDOR')

    # Should call the post method
    assert post_call.call_count == 1
    # Should return a queryset of values (flat=True)
    assert list(bulk_payload) == ['old_merchant']

    # Test with code in naming
    import_settings = Configuration.objects.get(workspace_id=workspace_id)
    import_settings.import_code_fields = ['VENDOR']
    import_settings.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='MERCHANT',
        display_name='Merchant',
        value='old_merchant_code: old_merchant',
        source_id='source_id_123',
        active=True
    )

    merchants_to_disable = {
        'destination_id': {
            'value': 'old_merchant',
            'updated_value': 'new_merchant',
            'code': 'old_merchant_code',
            'updated_code': 'old_merchant_code'
        }
    }

    bulk_payload = disable_merchants(workspace_id, merchants_to_disable, is_import_to_fyle_enabled=True, attribute_type='VENDOR')
    # Should return the value with code in naming
    assert 'old_merchant_code: old_merchant' in list(bulk_payload)
