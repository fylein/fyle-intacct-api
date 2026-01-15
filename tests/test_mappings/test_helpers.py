from datetime import datetime, timedelta, timezone
from unittest import mock
from unittest.mock import MagicMock, patch

from fyle_accounting_mappings.models import DestinationAttribute, MappingSetting

from apps.mappings.helpers import (
    get_project_billable_field_detail_key,
    get_project_billable_map,
    is_project_billable_sync_allowed,
    is_project_sync_allowed,
    patch_corporate_card_integration_settings,
    prepend_code_to_name,
    schedule_or_delete_auto_mapping_tasks,
    sync_changed_project_billable_to_fyle_on_intacct_sync,
    sync_project_billable_to_fyle_on_export_settings_change,
)
from apps.workspaces.models import Configuration, FeatureConfig


class DummyConfig:
    """
    Dummy Config class
    """
    def __init__(self, auto_map_employees, workspace_id=1):
        self.auto_map_employees = auto_map_employees
        self.workspace_id = workspace_id


@patch('apps.mappings.helpers.new_schedule_or_delete_fyle_import_tasks')
@patch('apps.mappings.tasks.schedule_auto_map_accounting_fields')
def test_schedule_or_delete_auto_mapping_tasks_calls(auto_map_mock, import_mock):
    """
    Test schedule_or_delete_auto_mapping_tasks_calls
    """
    config = DummyConfig(auto_map_employees=True, workspace_id=1)
    schedule_or_delete_auto_mapping_tasks(config)
    import_mock.assert_called_once_with(config)

    import_mock.reset_mock()
    auto_map_mock.reset_mock()
    config = DummyConfig(auto_map_employees=False, workspace_id=1)
    schedule_or_delete_auto_mapping_tasks(config)
    import_mock.assert_called_once_with(config)


def test_prepend_code_to_name():
    """
    Test prepend_code_to_name
    """
    assert prepend_code_to_name(True, 'Name', 'C123') == 'C123: Name'
    assert prepend_code_to_name(False, 'Name', 'C123') == 'Name'
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


def test_patch_corporate_card_integration_settings(db, test_connection):
    """
    Test patch_corporate_card_integration_settings helper - tests all conditions
    """
    workspace_id = 1
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    workspace_general_settings.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    workspace_general_settings.save()

    with mock.patch('apps.workspaces.tasks.patch_integration_settings_for_unmapped_cards') as mock_patch:
        patch_corporate_card_integration_settings(workspace_id=workspace_id)
        mock_patch.assert_called_once()
        assert mock_patch.call_args[1]['workspace_id'] == workspace_id
        assert 'unmapped_card_count' in mock_patch.call_args[1]

    workspace_general_settings.corporate_credit_card_expenses_object = 'BILL'
    workspace_general_settings.save()

    with mock.patch('apps.workspaces.tasks.patch_integration_settings_for_unmapped_cards') as mock_patch:
        patch_corporate_card_integration_settings(workspace_id=workspace_id)
        mock_patch.assert_not_called()

    workspace_general_settings.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    workspace_general_settings.save()

    with mock.patch('apps.workspaces.tasks.patch_integration_settings_for_unmapped_cards') as mock_patch:
        patch_corporate_card_integration_settings(workspace_id=workspace_id)
        mock_patch.assert_not_called()


def test_get_project_billable_field_detail_key_bill_reimbursable(db, test_connection):
    """
    Test get_project_billable_field_detail_key returns default_bill_billable for BILL reimbursable export
    """
    workspace_id = 1
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'BILL'
    configuration.corporate_credit_card_expenses_object = None
    configuration.save()

    result = get_project_billable_field_detail_key(workspace_id)
    assert result == 'default_bill_billable'


def test_get_project_billable_field_detail_key_bill_ccc(db, test_connection):
    """
    Test get_project_billable_field_detail_key returns default_bill_billable for BILL ccc export
    """
    workspace_id = 1
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = None
    configuration.corporate_credit_card_expenses_object = 'BILL'
    configuration.save()

    result = get_project_billable_field_detail_key(workspace_id)
    assert result == 'default_bill_billable'


def test_get_project_billable_field_detail_key_expense_report(db, test_connection):
    """
    Test get_project_billable_field_detail_key returns default_expense_report_billable for EXPENSE_REPORT
    """
    workspace_id = 1
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.corporate_credit_card_expenses_object = None
    configuration.save()

    result = get_project_billable_field_detail_key(workspace_id)
    assert result == 'default_expense_report_billable'


def test_get_project_billable_field_detail_key_no_configuration(db, test_connection):
    """
    Test get_project_billable_field_detail_key returns None when no configuration exists
    """
    workspace_id = 999
    Configuration.objects.filter(workspace_id=workspace_id).delete()

    result = get_project_billable_field_detail_key(workspace_id)
    assert result is None


def test_get_project_billable_field_detail_key_no_export_type(db, test_connection):
    """
    Test get_project_billable_field_detail_key returns None when export types are not BILL or EXPENSE_REPORT
    """
    workspace_id = 1
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'JOURNAL_ENTRY'
    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()

    result = get_project_billable_field_detail_key(workspace_id)
    assert result is None


def test_is_project_billable_sync_allowed_feature_disabled(db, test_connection):
    """
    Test is_project_billable_sync_allowed returns False when feature is disabled
    """
    workspace_id = 1
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = False
    feature_config.save()

    result = is_project_billable_sync_allowed(workspace_id)
    assert result is False


def test_is_project_billable_sync_allowed_no_billable_field(db, test_connection):
    """
    Test is_project_billable_sync_allowed returns False when no billable field is configured
    """
    workspace_id = 1
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = True
    feature_config.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'JOURNAL_ENTRY'
    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()

    result = is_project_billable_sync_allowed(workspace_id)
    assert result is False


def test_is_project_billable_sync_allowed_no_mapping_setting(db, test_connection):
    """
    Test is_project_billable_sync_allowed returns False when PROJECT mapping setting doesn't exist
    """
    workspace_id = 1
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = True
    feature_config.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'BILL'
    configuration.save()

    MappingSetting.objects.filter(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='PROJECT'
    ).delete()

    result = is_project_billable_sync_allowed(workspace_id)
    assert result is False


def test_is_project_billable_sync_allowed_success(db, test_connection):
    """
    Test is_project_billable_sync_allowed returns True when all conditions are met
    """
    workspace_id = 1
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = True
    feature_config.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'BILL'
    configuration.save()

    MappingSetting.objects.update_or_create(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='PROJECT',
        defaults={'import_to_fyle': True, 'is_custom': False}
    )

    result = is_project_billable_sync_allowed(workspace_id)
    assert result is True


def test_get_project_billable_map(db, test_connection):
    """
    Test get_project_billable_map returns correct billable map from destination attributes
    """
    workspace_id = 1

    DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').update(
        detail={'default_expense_report_billable': True, 'default_bill_billable': False}
    )

    result = get_project_billable_map(workspace_id)

    project_attrs = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT')
    for attr in project_attrs:
        assert attr.destination_id in result
        assert result[attr.destination_id]['default_expense_report_billable'] is True
        assert result[attr.destination_id]['default_bill_billable'] is False


def test_get_project_billable_map_no_detail(db, test_connection):
    """
    Test get_project_billable_map returns False values when detail is None
    """
    workspace_id = 1

    DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').update(detail=None)

    result = get_project_billable_map(workspace_id)

    project_attrs = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT')
    for attr in project_attrs:
        assert attr.destination_id in result
        assert result[attr.destination_id]['default_expense_report_billable'] is False
        assert result[attr.destination_id]['default_bill_billable'] is False


def test_sync_changed_project_billable_to_fyle_on_intacct_sync_not_allowed(db, test_connection, mocker):
    """
    Test sync_changed_project_billable_to_fyle_on_intacct_sync returns early when sync is not allowed
    """
    workspace_id = 1

    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = False
    feature_config.save()

    mock_project = mocker.patch('apps.mappings.helpers.Project')

    sync_changed_project_billable_to_fyle_on_intacct_sync(
        workspace_id=workspace_id,
        project_attributes=[],
        existing_billable_map={}
    )

    mock_project.assert_not_called()


def test_sync_changed_project_billable_to_fyle_on_intacct_sync_no_changes(db, test_connection, mocker):
    """
    Test sync_changed_project_billable_to_fyle_on_intacct_sync returns when there are no billable changes
    """
    workspace_id = 1

    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = True
    feature_config.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'BILL'
    configuration.save()

    MappingSetting.objects.update_or_create(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='PROJECT',
        defaults={'import_to_fyle': True, 'is_custom': False}
    )

    dest_attr = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').first()
    dest_attr.detail = {'default_bill_billable': True}
    dest_attr.save()

    existing_billable_map = {
        dest_attr.destination_id: {'default_expense_report_billable': False, 'default_bill_billable': True}
    }

    project_attributes = [
        {'destination_id': dest_attr.destination_id, 'detail': {'default_bill_billable': True}}
    ]

    mock_project = mocker.patch('apps.mappings.helpers.Project')

    sync_changed_project_billable_to_fyle_on_intacct_sync(
        workspace_id=workspace_id,
        project_attributes=project_attributes,
        existing_billable_map=existing_billable_map
    )

    mock_project.assert_not_called()


def test_sync_changed_project_billable_to_fyle_on_intacct_sync_with_changes(db, test_connection, mocker):
    """
    Test sync_changed_project_billable_to_fyle_on_intacct_sync detects and syncs billable changes
    """
    workspace_id = 1

    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = True
    feature_config.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'BILL'
    configuration.save()

    MappingSetting.objects.update_or_create(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='PROJECT',
        defaults={'import_to_fyle': True, 'is_custom': False}
    )

    dest_attr = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').first()
    dest_attr.detail = {'default_bill_billable': True}
    dest_attr.save()

    existing_billable_map = {
        dest_attr.destination_id: {'default_expense_report_billable': False, 'default_bill_billable': False}
    }

    project_attributes = [
        {'destination_id': dest_attr.destination_id, 'detail': {'default_bill_billable': True}}
    ]

    mock_project_instance = MagicMock()
    mock_project = mocker.patch('apps.mappings.helpers.Project', return_value=mock_project_instance)

    sync_changed_project_billable_to_fyle_on_intacct_sync(
        workspace_id=workspace_id,
        project_attributes=project_attributes,
        existing_billable_map=existing_billable_map
    )

    mock_project.assert_called_once()
    mock_project_instance.sync_project_billable_to_fyle.assert_called_once_with(
        destination_attribute_pks=[dest_attr.id]
    )


def test_sync_changed_project_billable_to_fyle_on_intacct_sync_expense_report_field(db, test_connection, mocker):
    """
    Test sync_changed_project_billable_to_fyle_on_intacct_sync uses expense_report billable field correctly
    """
    workspace_id = 1

    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.import_billable_field_for_projects = True
    feature_config.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.corporate_credit_card_expenses_object = None
    configuration.save()

    MappingSetting.objects.update_or_create(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='PROJECT',
        defaults={'import_to_fyle': True, 'is_custom': False}
    )

    dest_attr = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').first()
    dest_attr.detail = {'default_expense_report_billable': True}
    dest_attr.save()

    existing_billable_map = {
        dest_attr.destination_id: {'default_expense_report_billable': False, 'default_bill_billable': False}
    }

    project_attributes = [
        {'destination_id': dest_attr.destination_id, 'detail': {'default_expense_report_billable': True}}
    ]

    mock_project_instance = MagicMock()
    mock_project = mocker.patch('apps.mappings.helpers.Project', return_value=mock_project_instance)

    sync_changed_project_billable_to_fyle_on_intacct_sync(
        workspace_id=workspace_id,
        project_attributes=project_attributes,
        existing_billable_map=existing_billable_map
    )

    mock_project.assert_called_once()
    call_kwargs = mock_project.call_args.kwargs
    assert call_kwargs['project_billable_field_detail_key'] == 'default_expense_report_billable'


def test_sync_project_billable_to_fyle_on_export_settings_change_no_billable_field(db, test_connection, mocker):
    """
    Test sync_project_billable_to_fyle_on_export_settings_change returns early when no billable field
    """
    workspace_id = 1

    mock_project = mocker.patch('apps.mappings.helpers.Project')

    sync_project_billable_to_fyle_on_export_settings_change(
        workspace_id=workspace_id,
        billable_field=None
    )

    mock_project.assert_not_called()


def test_sync_project_billable_to_fyle_on_export_settings_change_success(db, test_connection, mocker):
    """
    Test sync_project_billable_to_fyle_on_export_settings_change syncs billable for all projects
    """
    workspace_id = 1

    mock_project_instance = MagicMock()
    mock_project = mocker.patch('apps.mappings.helpers.Project', return_value=mock_project_instance)

    sync_project_billable_to_fyle_on_export_settings_change(
        workspace_id=workspace_id,
        billable_field='default_bill_billable'
    )

    mock_project.assert_called_once()
    call_kwargs = mock_project.call_args.kwargs
    assert call_kwargs['workspace_id'] == workspace_id
    assert call_kwargs['destination_field'] == 'PROJECT'
    assert call_kwargs['is_auto_sync_enabled'] is True
    assert call_kwargs['project_billable_field_detail_key'] == 'default_bill_billable'

    mock_project_instance.sync_project_billable_to_fyle.assert_called_once_with()


def test_sync_project_billable_to_fyle_on_export_settings_change_with_prepend_code(db, test_connection, mocker):
    """
    Test sync_project_billable_to_fyle_on_export_settings_change uses prepend_code_to_name correctly
    """
    workspace_id = 1

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.import_code_fields = ['PROJECT']
    configuration.save()

    mock_project_instance = MagicMock()
    mock_project = mocker.patch('apps.mappings.helpers.Project', return_value=mock_project_instance)

    sync_project_billable_to_fyle_on_export_settings_change(
        workspace_id=workspace_id,
        billable_field='default_expense_report_billable'
    )

    mock_project.assert_called_once()
    call_kwargs = mock_project.call_args.kwargs
    assert call_kwargs['prepend_code_to_name'] is True
