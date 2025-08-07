from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from requests.models import Response

from apps.fyle import helpers


# 2. Test get_request error branch
@patch('apps.fyle.helpers.get_access_token')
@patch('apps.fyle.helpers.requests.get')
def test_get_request_error(mock_get, mock_get_access_token):
    """
    Test get_request error branch
    """
    # Mock get_access_token to return a dummy token
    mock_get_access_token.return_value = 'dummy_access_token'

    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 400
    mock_response.text = 'error!'
    mock_get.return_value = mock_response
    with pytest.raises(Exception) as exc:
        helpers.get_request('http://fake', {}, 'token')
    assert 'error!' in str(exc.value)


# 4. Test add_expense_id_to_expense_group_settings
@patch('apps.fyle.helpers.ExpenseGroupSettings.objects.get')
def test_add_expense_id_to_expense_group_settings(mock_get):
    """
    Test add_expense_id_to_expense_group_settings
    """
    mock_settings = MagicMock()
    mock_settings.corporate_credit_card_expense_group_fields = ['foo']
    mock_get.return_value = mock_settings
    helpers.add_expense_id_to_expense_group_settings(1)
    assert 'expense_id' in mock_settings.corporate_credit_card_expense_group_fields
    mock_settings.save.assert_called_once()


# 5. Test check_interval_and_sync_dimension with/without source_synced_at
@patch('apps.fyle.helpers.sync_dimensions')
@patch('apps.fyle.helpers.Workspace.objects.get')
def test_check_interval_and_sync_dimension(mock_get, mock_sync):
    """
    Test check_interval_and_sync_dimension with/without source_synced_at
    """
    # No source_synced_at
    mock_workspace = MagicMock()
    mock_workspace.source_synced_at = None
    mock_get.return_value = mock_workspace
    helpers.check_interval_and_sync_dimension(1)
    mock_sync.assert_called_once_with(1)
    mock_workspace.save.assert_called_once()

    # With source_synced_at, but > 0 days
    mock_sync.reset_mock()
    mock_workspace.save.reset_mock()
    mock_workspace.source_synced_at = datetime.now(timezone.utc) - timedelta(days=1)
    helpers.check_interval_and_sync_dimension(1)
    mock_sync.assert_called_once_with(1)
    mock_workspace.save.assert_called_once()


# 6. Test sync_dimensions with/without dependent_field_settings
@patch('apps.fyle.helpers.update_dimension_details')
@patch('apps.fyle.helpers.import_string')
@patch('apps.fyle.helpers.PlatformConnector')
@patch('apps.fyle.helpers.DependentFieldSetting.objects.filter')
@patch('apps.fyle.helpers.Configuration.objects.filter')
@patch('apps.fyle.helpers.ExpenseAttribute.objects.filter')
@patch('apps.fyle.helpers.FyleCredential.objects.get')
def test_sync_dimensions(mock_get, mock_expense_attr_filter, mock_config_filter, mock_filter, mock_platform, mock_import_string, mock_update):
    """
    Test sync_dimensions with/without dependent_field_settings
    """
    mock_cred = MagicMock()
    mock_cred.workspace_id = 1
    mock_cred.workspace.id = 1
    mock_get.return_value = mock_cred

    # Mock Configuration.objects.filter().first()
    mock_config = MagicMock()
    mock_config.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'  # Set to avoid the import_string call
    mock_config_filter.return_value.first.return_value = mock_config

    # Mock ExpenseAttribute.objects.filter().count()
    mock_expense_attr_filter.return_value.count.return_value = 5

    # Mock import_string call
    mock_import_func = MagicMock()
    mock_import_string.return_value = mock_import_func

    mock_dep = MagicMock()
    mock_dep.cost_code_field_id = 1
    mock_dep.cost_type_field_id = 2
    mock_filter.return_value.first.return_value = mock_dep
    mock_platform_instance = MagicMock()
    mock_platform.return_value = mock_platform_instance
    helpers.sync_dimensions(1)
    mock_platform_instance.import_fyle_dimensions.assert_called_once()
    mock_update.assert_called_once()

    # No dependent_field_settings
    mock_filter.return_value.first.return_value = None
    helpers.sync_dimensions(1)
    mock_platform_instance.import_fyle_dimensions.assert_called()
    mock_update.assert_called()


@patch('apps.fyle.helpers.update_dimension_details')
@patch('apps.fyle.helpers.import_string')
@patch('apps.fyle.helpers.PlatformConnector')
@patch('apps.fyle.helpers.DependentFieldSetting.objects.filter')
@patch('apps.fyle.helpers.Configuration.objects.filter')
@patch('apps.fyle.helpers.ExpenseAttribute.objects.filter')
@patch('apps.fyle.helpers.FyleCredential.objects.get')
def test_sync_dimensions_with_charge_card_transaction(mock_get, mock_expense_attr_filter, mock_config_filter, mock_filter, mock_platform, mock_import_string, mock_update):
    """
    Test sync_dimensions when corporate_credit_card_expenses_object is 'CHARGE_CARD_TRANSACTION'
    """
    mock_cred = MagicMock()
    mock_cred.workspace_id = 1
    mock_cred.workspace.id = 1
    mock_get.return_value = mock_cred

    mock_config = MagicMock()
    mock_config.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    mock_config_filter.return_value.first.return_value = mock_config

    mock_expense_attr_filter.return_value.count.return_value = 3

    mock_patch_function = MagicMock()
    mock_import_string.return_value = mock_patch_function

    mock_filter.return_value.first.return_value = None

    mock_platform_instance = MagicMock()
    mock_platform.return_value = mock_platform_instance

    helpers.sync_dimensions(1)

    mock_import_string.assert_called_with('apps.workspaces.tasks.patch_integration_settings_for_unmapped_cards')

    mock_patch_function.assert_called_once_with(workspace_id=1, unmapped_card_count=3)

    mock_platform_instance.import_fyle_dimensions.assert_called_once()
    mock_update.assert_called_once()


@patch('apps.fyle.helpers.update_dimension_details')
@patch('apps.fyle.helpers.import_string')
@patch('apps.fyle.helpers.PlatformConnector')
@patch('apps.fyle.helpers.DependentFieldSetting.objects.filter')
@patch('apps.fyle.helpers.Configuration.objects.filter')
@patch('apps.fyle.helpers.ExpenseAttribute.objects.filter')
@patch('apps.fyle.helpers.FyleCredential.objects.get')
def test_sync_dimensions_with_no_configuration(mock_get, mock_expense_attr_filter, mock_config_filter, mock_filter, mock_platform, mock_import_string, mock_update):
    """
    Test sync_dimensions when configuration is None
    """
    mock_cred = MagicMock()
    mock_cred.workspace_id = 1
    mock_cred.workspace.id = 1
    mock_get.return_value = mock_cred

    mock_config_filter.return_value.first.return_value = None

    mock_expense_attr_filter.return_value.count.return_value = 2

    mock_patch_function = MagicMock()
    mock_import_string.return_value = mock_patch_function

    mock_filter.return_value.first.return_value = None

    mock_platform_instance = MagicMock()
    mock_platform.return_value = mock_platform_instance

    helpers.sync_dimensions(1)

    mock_import_string.assert_not_called()
    mock_patch_function.assert_not_called()

    mock_platform_instance.import_fyle_dimensions.assert_called_once()
    mock_update.assert_called_once()
