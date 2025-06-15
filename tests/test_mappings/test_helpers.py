from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from apps.mappings.helpers import (
    schedule_or_delete_auto_mapping_tasks,
    prepend_code_to_name,
    is_project_sync_allowed
)


class DummyConfig:
    """
    Dummy Config class
    """
    def __init__(self, auto_map_employees, workspace_id=1):
        self.auto_map_employees = auto_map_employees
        self.workspace_id = workspace_id


@patch('apps.mappings.helpers.new_schedule_or_delete_fyle_import_tasks')
@patch('apps.mappings.helpers.schedule_auto_map_employees')
@patch('apps.mappings.helpers.schedule_auto_map_charge_card_employees')
def test_schedule_or_delete_auto_mapping_tasks_calls(charge_card_mock, auto_map_mock, import_mock):
    """
    Test schedule_or_delete_auto_mapping_tasks_calls
    """
    # auto_map_employees True: should not call charge_card
    config = DummyConfig(auto_map_employees=True)
    schedule_or_delete_auto_mapping_tasks(config)
    import_mock.assert_called_once_with(config)
    auto_map_mock.assert_called_once_with(employee_mapping_preference=True, workspace_id=1)
    charge_card_mock.assert_not_called()

    # auto_map_employees False: should call charge_card
    import_mock.reset_mock()
    auto_map_mock.reset_mock()
    charge_card_mock.reset_mock()
    config = DummyConfig(auto_map_employees=False)
    schedule_or_delete_auto_mapping_tasks(config)
    import_mock.assert_called_once_with(config)
    auto_map_mock.assert_called_once_with(employee_mapping_preference=False, workspace_id=1)
    charge_card_mock.assert_called_once_with(workspace_id=1)


def test_prepend_code_to_name():
    """
    Test prepend_code_to_name
    """
    # prepend_code_in_name True and code present
    assert prepend_code_to_name(True, 'Name', 'C123') == 'C123: Name'
    # prepend_code_in_name False
    assert prepend_code_to_name(False, 'Name', 'C123') == 'Name'
    # prepend_code_in_name True but code missing
    assert prepend_code_to_name(True, 'Name', None) == 'Name'


def test_is_project_sync_allowed_none():
    """
    Test is_project_sync_allowed_none
    """
    assert is_project_sync_allowed(None) is True


def test_is_project_sync_allowed_no_last_success():
    """
    Test is_project_sync_allowed_no_last_success
    """
    dummy = MagicMock()
    dummy.last_successful_run_at = None
    assert is_project_sync_allowed(dummy) is True


def test_is_project_sync_allowed_old():
    """
    Test is_project_sync_allowed_old
    """
    dummy = MagicMock()
    dummy.last_successful_run_at = datetime.now(timezone.utc) - timedelta(hours=1)
    assert is_project_sync_allowed(dummy) is True


def test_is_project_sync_allowed_recent():
    """
    Test is_project_sync_allowed_recent
    """
    dummy = MagicMock()
    dummy.last_successful_run_at = datetime.now(timezone.utc)
    assert is_project_sync_allowed(dummy) is False
