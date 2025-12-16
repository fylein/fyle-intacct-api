from apps.sage_intacct.helpers import (
    check_interval_and_sync_dimension,
    is_dependent_field_import_enabled,
    schedule_payment_sync,
)
from apps.sage_intacct.exports.helpers import get_source_entity_id
from apps.sage_intacct.exports.journal_entries import construct_journal_entry_payload
from apps.fyle.models import ExpenseGroup
from apps.mappings.models import GeneralMapping, LocationEntityMapping
from apps.workspaces.models import Configuration, FyleCredential, Workspace
from apps.workspaces.tasks import patch_integration_settings


def test_schedule_payment_sync(db):
    """
    Test schedule_payment_sync
    """
    workspace_id = 1
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    schedule_payment_sync(configuration)


def test_check_interval_and_sync_dimension(db):
    """
    Test check_interval_and_sync_dimension
    """
    workspace_id = 1

    workspace = Workspace.objects.get(id=workspace_id)

    check_interval_and_sync_dimension(workspace_id)

    workspace.destination_synced_at = None
    workspace.save()

    check_interval_and_sync_dimension(workspace_id)


def test_check_interval_and_sync_dimension_exception(db, mocker):
    """
    Test check_interval_and_sync_dimension exception handling
    """
    workspace_id = 1
    workspace = Workspace.objects.get(id=workspace_id)
    workspace.destination_synced_at = None
    workspace.save()

    mocker.patch('apps.sage_intacct.helpers.sync_dimensions', side_effect=Exception('Test exception'))
    logger_mock = mocker.patch('apps.sage_intacct.helpers.logger')

    check_interval_and_sync_dimension(workspace_id)

    logger_mock.error.assert_called_once()


def test_is_dependent_field_import_enabled(db, create_dependent_field_setting):
    """
    Test is_dependent_field_import_enabled
    """
    assert is_dependent_field_import_enabled(1) == True


def test_patch_integration_settings(db, mocker):
    """
    Test patch_integration_settings
    """
    workspace_id = 1

    # Setup a dummy refresh token
    refresh_token = 'dummy_refresh_token'
    fyle_credential = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credential.refresh_token = refresh_token
    fyle_credential.save()
    patch_request_mock = mocker.patch('apps.workspaces.tasks.patch_request')

    patch_integration_settings(workspace_id, errors=5)
    patch_request_mock.assert_not_called()

    workspace = Workspace.objects.get(id=workspace_id)
    workspace.onboarding_state = 'COMPLETE'
    workspace.save()

    patch_request_mock.reset_mock()
    patch_integration_settings(workspace_id, errors=5)
    patch_request_mock.assert_called_with(
        mocker.ANY,  # URL
        {
            'tpa_name': 'Fyle Sage Intacct Integration',
            'errors_count': 5
        },
        refresh_token
    )

    # Testing with is_token_expired parameter
    patch_request_mock.reset_mock()
    patch_integration_settings(workspace_id, is_token_expired=True)

    patch_request_mock.assert_called_with(
        mocker.ANY,  # URL
        {
            'tpa_name': 'Fyle Sage Intacct Integration',
            'is_token_expired': True
        },
        refresh_token
    )

    # Testing with both parameters
    patch_request_mock.reset_mock()
    patch_integration_settings(workspace_id, errors=10, is_token_expired=False)

    patch_request_mock.assert_called_with(
        mocker.ANY,  # URL
        {
            'tpa_name': 'Fyle Sage Intacct Integration',
            'errors_count': 10,
            'is_token_expired': False
        },
        refresh_token
    )

    # Test exception handling
    patch_request_mock.reset_mock()
    patch_request_mock.side_effect = Exception('Test exception')

    logger_mock = mocker.patch('apps.workspaces.tasks.logger.error')

    patch_integration_settings(workspace_id, errors=15)

    # Verify patch_request was called
    patch_request_mock.assert_called_once()

    # Verify logger.error was called
    logger_mock.assert_called_once()


def test_get_source_entity_id_returns_location(db):
    """
    Test get_source_entity_id returns default_location_id when all conditions are met
    """
    workspace_id = 1

    LocationEntityMapping.objects.filter(workspace_id=workspace_id).update(destination_id='top_level')

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.je_single_credit_line = True
    configuration.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_location_id = 'LOC123'
    general_mappings.save()

    expense_group = ExpenseGroup.objects.get(id=1)

    result = get_source_entity_id(workspace_id, configuration, general_mappings, expense_group)

    assert result == 'LOC123'


def test_get_source_entity_id_returns_none(db):
    """
    Test get_source_entity_id returns None when conditions are not met
    """
    workspace_id = 1

    LocationEntityMapping.objects.filter(workspace_id=workspace_id).update(destination_id='600')

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    expense_group = ExpenseGroup.objects.get(id=1)

    result = get_source_entity_id(workspace_id, configuration, general_mappings, expense_group)

    assert result is None


def test_construct_journal_entry_payload_with_source_entity(db, mocker, create_journal_entry):
    """
    Test construct_journal_entry_payload includes baseLocation when conditions are met
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    LocationEntityMapping.objects.filter(workspace_id=workspace_id).update(destination_id='top_level')

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.je_single_credit_line = True
    configuration.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_location_id = 'LOC123'
    general_mappings.save()

    payload = construct_journal_entry_payload(workspace_id, journal_entry, journal_entry_lineitems)

    assert 'baseLocation' in payload
    assert payload['baseLocation']['id'] == 'LOC123'
