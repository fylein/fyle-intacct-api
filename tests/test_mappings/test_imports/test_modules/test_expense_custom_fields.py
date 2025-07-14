from unittest import mock

from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, Mapping, MappingSetting
from fyle_integrations_platform_connector import PlatformConnector

from apps.mappings.constants import SYNC_METHODS
from apps.sage_intacct.utils import SageIntacctConnector
from apps.workspaces.models import FyleCredential, SageIntacctCredential, Workspace
from fyle_integrations_imports.modules.expense_custom_fields import ExpenseCustomField, disable_expense_custom_fields
from tests.test_mappings.test_imports.test_modules.fixtures import expense_custom_field_data
from tests.test_mappings.test_imports.test_modules.helpers import get_platform_connection


def test_sync_expense_atrributes(mocker, db):
    """
    Test sync expense attributes
    """
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.workspace.fyle_org_id = 'orqjgyJ21uge'
    fyle_credentials.workspace.save()
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    expense_attribute_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='LUKE').count()
    assert expense_attribute_count == 0

    mocker.patch(
        'fyle.platform.apis.v1.admin.expense_fields.list_all',
        return_value=[]
    )

    expense_custom_field = ExpenseCustomField(workspace_id, 'LUKE', 'CLASS', None, mock.Mock(), [SYNC_METHODS['CLASS']], False, False, True)
    expense_custom_field.sync_expense_attributes(platform)

    expense_attribute_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='LUKE').count()
    assert expense_attribute_count == 0

    mocker.patch(
        'fyle.platform.apis.v1.admin.expense_fields.list_all',
        return_value=expense_custom_field_data['create_new_auto_create_expense_custom_fields_expense_attributes_0']
    )

    expense_custom_field.sync_expense_attributes(platform)

    expense_attribute_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='LUKE').count()
    assert expense_attribute_count == 21


def test_auto_create_destination_attributes(mocker, db):
    """
    Test auto create destination attributes
    """
    sage_creds = SageIntacctCredential.objects.get(workspace_id=1)
    sage_connection = SageIntacctConnector(sage_creds, 1)

    expense_custom_field = ExpenseCustomField(1, 'LUKE', 'LOCATION', None, sage_connection, [SYNC_METHODS['LOCATION']])
    expense_custom_field.sync_after = None

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='LOCATION').delete()

    Workspace.objects.filter(id=1).update(fyle_org_id='orqjgyJ21uge')

    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(workspace_id=1, source_type='LUKE', destination_type='LOCATION').delete()
    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='LOCATION').delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='LUKE').delete()

    # create new case for projects import
    with mock.patch('fyle.platform.apis.v1.admin.expense_fields.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
            return_value=[]
        )
        mocker.patch(
            'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
            return_value=expense_custom_field_data['create_new_auto_create_expense_custom_fields_get_by_id']
        )
        mocker.patch(
            'sageintacctsdk.apis.Locations.count',
            return_value=21
        )
        mocker.patch(
            'sageintacctsdk.apis.Locations.get_all_generator',
            return_value=expense_custom_field_data['create_new_auto_create_expense_custom_fields_destination_attributes']
        )
        mock_call.return_value = expense_custom_field_data['create_new_auto_create_expense_custom_fields_expense_attributes_0']

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'LUKE').count()

        assert expense_attributes_count == 0

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='LUKE', destination_type='LOCATION').count()

        assert mappings_count == 0

        expense_custom_field.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'LUKE').count()

        assert expense_attributes_count == 21

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='LUKE', destination_type='LOCATION').count()

        assert mappings_count == 21

    # create new expense_custom_field mapping for sub-sequent run (we will be adding 2 new LOCATION)
    with mock.patch('fyle.platform.apis.v1.admin.expense_fields.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
            return_value=[]
        )
        mocker.patch(
            'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
            return_value=expense_custom_field_data['create_new_auto_create_expense_custom_fields_get_by_id']
        )
        mocker.patch(
            'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
            return_value=expense_custom_field_data['create_new_auto_create_expense_custom_fields_get_by_id']
        )
        mocker.patch(
            'sageintacctsdk.apis.Locations.get_all_generator',
            return_value=expense_custom_field_data['create_new_auto_create_expense_custom_fields_destination_attributes_subsequent_run']
        )
        mock_call.return_value = expense_custom_field_data['create_new_auto_create_expense_custom_fields_expense_attributes_1']

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'LUKE').count()

        assert expense_attributes_count == 21

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='LUKE', destination_type='LOCATION').count()

        assert mappings_count == 21

        expense_custom_field.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'LUKE').count()

        assert expense_attributes_count == 21 + 2

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='LUKE', destination_type='LOCATION').count()

        assert mappings_count == 21 + 2


def test_construct_fyle_expense_custom_field_payload(db):
    """
    Test construct fyle expense custom field payload
    """
    expense_custom_field = ExpenseCustomField(1, 'LUKE', 'LOCATION', None, mock.Mock(), [SYNC_METHODS['LOCATION']], False, False, True)
    expense_custom_field.sync_after = None
    platform = get_platform_connection(1)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='LOCATION')

    fyle_payload = expense_custom_field.construct_fyle_expense_custom_field_payload(
        paginated_destination_attributes,
        platform
    )

    assert fyle_payload['options'] == []


def test_disable_expense_custom_fields(db, mocker):
    """
    Test disable_expense_custom_fields
    """
    workspace_id = 1
    attribute_type = 'CLASS'  # destination_field in MappingSetting

    # Create the ExpenseAttribute to be disabled
    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='LUKE',  # source_field in MappingSetting
        display_name='Custom Field',
        value='old_custom_field',
        source_id='source_id',
        active=True
    )

    DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CLASS',
        value='old_custom_field',
        active=True,
        destination_id='old_custom_field_code',
        code='old_custom_field_code'
    )

    # Create the MappingSetting so the filter in disable_expense_custom_fields works
    MappingSetting.objects.create(
        workspace_id=workspace_id,
        source_field='LUKE',
        destination_field=attribute_type
    )

    attributes_to_disable = {
        'destination_id': {
            'value': 'old_custom_field',
            'updated_value': 'new_custom_field',
            'code': 'old_custom_field_code',
            'updated_code': 'old_custom_field_code'
        }
    }

    # Patch prepend_code_to_name to just return the value for simplicity
    mocker.patch('apps.mappings.helpers.prepend_code_to_name', side_effect=lambda prepend_code_in_name, value, code: value if not prepend_code_in_name else f"{code}: {value}")

    # Actually call the function
    disable_expense_custom_fields(workspace_id, attribute_type, attributes_to_disable)

    # Should mark the attribute as inactive
    assert not ExpenseAttribute.objects.get(workspace_id=workspace_id, value='old_custom_field').active
