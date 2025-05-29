import pytest
from unittest.mock import patch, MagicMock
from apps.fyle import helpers
from requests.models import Response
from datetime import datetime, timedelta, timezone


# 2. Test get_request error branch
@patch('apps.fyle.helpers.requests.get')
def test_get_request_error(mock_get):
    """
    Test get_request error branch
    """
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 400
    mock_response.text = 'error!'
    mock_get.return_value = mock_response
    with pytest.raises(Exception) as exc:
        helpers.get_request('http://fake', {}, 'token')
    assert 'error!' in str(exc.value)


# 3. Test patch_request error branch
@patch('apps.fyle.helpers.requests.patch')
def test_patch_request_error(mock_patch):
    """
    Test patch_request error branch
    """
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 400
    mock_response.text = 'error!'
    mock_patch.return_value = mock_response
    with pytest.raises(Exception) as exc:
        helpers.patch_request('http://fake', {})
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
@patch('apps.fyle.helpers.PlatformConnector')
@patch('apps.fyle.helpers.DependentFieldSetting.objects.filter')
@patch('apps.fyle.helpers.FyleCredential.objects.get')
def test_sync_dimensions(mock_get, mock_filter, mock_platform, mock_update):
    """
    Test sync_dimensions with/without dependent_field_settings
    """
    mock_cred = MagicMock()
    mock_cred.workspace_id = 1
    mock_cred.workspace.id = 1
    mock_get.return_value = mock_cred
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


# 7. Test handle_refresh_dimensions with all branches
@patch('apps.fyle.helpers.sync_dimensions')
@patch('apps.fyle.helpers.Chain')
@patch('apps.fyle.helpers.MappingSetting.objects.filter')
@patch('apps.fyle.helpers.Configuration.objects.filter')
@patch('apps.fyle.helpers.Workspace.objects.get')
def test_handle_refresh_dimensions(mock_get, mock_config_filter, mock_mapping_filter, mock_chain, mock_sync):
    """
    Test handle_refresh_dimensions with all branches
    """
    mock_workspace = MagicMock()
    mock_get.return_value = mock_workspace
    mock_config = MagicMock()
    mock_config.import_code_fields = ['EXPENSE_TYPE']
    mock_config.import_vendors_as_merchants = True
    mock_config.import_categories = True
    mock_config.reimbursable_expenses_object = 'EXPENSE_REPORT'
    mock_config.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    mock_config_filter.return_value.first.return_value = mock_config
    mock_mapping = MagicMock()
    mock_mapping.source_field = 'PROJECT'
    mock_mapping.destination_field = 'PROJECT'
    mock_mapping.is_custom = False
    mock_mapping_filter.return_value = [mock_mapping]
    mock_chain_instance = MagicMock()
    mock_chain.return_value = mock_chain_instance
    mock_chain_instance.length.return_value = 1
    helpers.handle_refresh_dimensions(1)
    mock_chain_instance.run.assert_called_once()
    mock_sync.assert_called_once_with(1)
    mock_workspace.save.assert_called()
