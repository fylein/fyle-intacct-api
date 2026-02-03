import pytest

from apps.internal.actions import delete_integration_record, get_accounting_fields, get_exported_entry
from apps.sage_intacct.connector import SageIntacctObjectCreationManager
from tests.test_sageintacct.fixtures import data


def test_get_accounting_fields(db, mocker):
    """
    Test get_accounting_fields function with SOAP API
    """
    query_params = {
        'org_id': 'or79Cob97KSh',
        'resource_type': 'employees',
    }
    mocker.patch(
        'sageintacctsdk.apis.Employees.get_all_generator',
        return_value=data['get_employees']
    )

    fields = get_accounting_fields(query_params)
    assert fields is not None


def test_get_accounting_fields_rest_api(db, mocker):
    """
    Test get_accounting_fields function with REST API when migrated_to_rest_api is True
    """
    query_params = {
        'org_id': 'or79Cob97KSh',
        'resource_type': 'employees',
    }

    mocker.patch(
        'apps.sage_intacct.helpers.FeatureConfig.get_feature_config',
        return_value=True
    )

    mock_rest_sdk = mocker.Mock()
    mock_rest_sdk.access_token = 'mock_token'
    mock_rest_sdk.access_token_expires_in = 21600
    mock_employees_module = mocker.Mock()
    mock_rest_sdk.employees = mock_employees_module
    mock_employees_module.get_all_generator.return_value = iter([
        [{'id': 'EMP001', 'name': 'Employee One', 'status': 'active'}],
        [{'id': 'EMP002', 'name': 'Employee Two', 'status': 'active'}]
    ])

    mocker.patch(
        'apps.sage_intacct.connector.IntacctRESTSDK',
        return_value=mock_rest_sdk
    )

    mock_rest_sdk.sessions.get_session_id.return_value = {'sessionId': 'mock_session'}

    fields = get_accounting_fields(query_params)
    assert fields is not None
    assert len(fields) == 2
    assert fields[0]['id'] == 'EMP001'


def test_get_exported_entry(db, mocker):
    """
    Test get_exported_entry function with SOAP API
    """
    query_params = {
        'org_id': 'or79Cob97KSh',
        'resource_type': 'bill',
        'internal_id': '1'
    }
    mocker.patch(
        'sageintacctsdk.apis.Bills.get',
        return_value={'summa': 'hehe'}
    )

    entry = get_exported_entry(query_params)
    assert entry is not None


def test_get_exported_entry_rest_api(db, mocker):
    """
    Test get_exported_entry function with REST API when migrated_to_rest_api is True
    """
    query_params = {
        'org_id': 'or79Cob97KSh',
        'resource_type': 'bill',
        'internal_id': 'BILL001'
    }

    mocker.patch(
        'apps.sage_intacct.helpers.FeatureConfig.get_feature_config',
        return_value=True
    )

    mock_rest_sdk = mocker.Mock()
    mock_rest_sdk.access_token = 'mock_token'
    mock_rest_sdk.access_token_expires_in = 21600
    mock_bills_module = mocker.Mock()
    mock_rest_sdk.bills = mock_bills_module
    mock_bills_module.get_all_generator.return_value = iter([
        [{'id': 'BILL001', 'key': 'BILL001', 'state': 'paid', 'amount': 100.0}]
    ])

    mocker.patch(
        'apps.sage_intacct.connector.IntacctRESTSDK',
        return_value=mock_rest_sdk
    )

    mock_rest_sdk.sessions.get_session_id.return_value = {'sessionId': 'mock_session'}

    mocker.patch(
        'apps.sage_intacct.connector.SageIntacctObjectCreationManager.get_bill',
        return_value={'id': 'BILL001', 'key': 'BILL001', 'state': 'paid', 'amount': 100.0}
    )

    entry = get_exported_entry(query_params)
    assert entry is not None
    assert entry['id'] == 'BILL001'
    assert entry['amount'] == 100.0


def test_get_exported_entry_rest_api_with_key_field(db, mocker):
    """
    Test get_exported_entry function with REST API using 'key' field when 'id' doesn't match
    """
    query_params = {
        'org_id': 'or79Cob97KSh',
        'resource_type': 'employees',
        'internal_id': 'EMP001'
    }

    mocker.patch(
        'apps.sage_intacct.helpers.FeatureConfig.get_feature_config',
        return_value=True
    )

    mock_rest_sdk = mocker.Mock()
    mock_rest_sdk.access_token = 'mock_token'
    mock_rest_sdk.access_token_expires_in = 21600
    mock_employees_module = mocker.Mock()
    mock_rest_sdk.employees = mock_employees_module

    employee_data = [{'id': 'EMP001', 'key': 'EMP001', 'name': 'Employee One', 'status': 'active'}]
    mock_employees_module.get_all_generator.side_effect = [
        iter([]),
        iter([employee_data])
    ]

    mocker.patch(
        'apps.sage_intacct.connector.IntacctRESTSDK',
        return_value=mock_rest_sdk
    )

    mock_rest_sdk.sessions.get_session_id.return_value = {'sessionId': 'mock_session'}

    mocker.patch.object(
        SageIntacctObjectCreationManager,
        'get_employees',
        return_value={'id': 'EMP001', 'key': 'EMP001', 'name': 'Employee One', 'status': 'active'},
        create=True
    )

    entry = get_exported_entry(query_params)
    assert entry is not None
    assert entry['id'] == 'EMP001'
    assert entry['name'] == 'Employee One'


def test_get_accounting_fields_rest_api_unsupported_resource(db, mocker):
    """
    Test get_accounting_fields function with REST API when unsupported resource type is provided
    """
    query_params = {
        'org_id': 'or79Cob97KSh',
        'resource_type': 'unsupported_resource',
    }

    mocker.patch(
        'apps.sage_intacct.helpers.FeatureConfig.get_feature_config',
        return_value=True
    )

    mock_sessions = mocker.Mock()
    mock_sessions.get_session_id.return_value = {'sessionId': 'mock_session'}

    mock_rest_sdk = mocker.Mock(spec=['access_token', 'access_token_expires_in', 'sessions', 'employees', 'bills'])
    mock_rest_sdk.access_token = 'mock_token'
    mock_rest_sdk.access_token_expires_in = 21600
    mock_rest_sdk.sessions = mock_sessions

    mocker.patch(
        'apps.sage_intacct.connector.IntacctRESTSDK',
        return_value=mock_rest_sdk
    )

    with pytest.raises(ValueError, match="Resource type 'unsupported_resource' is not supported"):
        get_accounting_fields(query_params)


def test_get_exported_entry_rest_api_unsupported_resource(db, mocker):
    """
    Test get_exported_entry function with REST API when unsupported resource type is provided
    """
    query_params = {
        'org_id': 'or79Cob97KSh',
        'resource_type': 'unsupported_resource',
        'internal_id': 'ID001'
    }

    mocker.patch(
        'apps.sage_intacct.helpers.FeatureConfig.get_feature_config',
        return_value=True
    )

    mock_sessions = mocker.Mock()
    mock_sessions.get_session_id.return_value = {'sessionId': 'mock_session'}

    mock_rest_sdk = mocker.Mock(spec=['access_token', 'access_token_expires_in', 'sessions', 'employees', 'bills'])
    mock_rest_sdk.access_token = 'mock_token'
    mock_rest_sdk.access_token_expires_in = 21600
    mock_rest_sdk.sessions = mock_sessions

    mocker.patch(
        'apps.sage_intacct.connector.IntacctRESTSDK',
        return_value=mock_rest_sdk
    )

    with pytest.raises(ValueError, match="Resource type 'unsupported_resource' is not supported"):
        get_exported_entry(query_params)


def test_delete_integration_record(db, mocker):
    """
    Test delete_integration_record function
    """
    workspace_id = 1

    mock_credential = mocker.Mock()
    mock_credential.refresh_token = 'test_refresh_token'
    mocker.patch('apps.internal.actions.FyleCredential.objects.get', return_value=mock_credential)

    mocker.patch('apps.internal.actions.delete_request')

    result = delete_integration_record(workspace_id)
    assert result == "SUCCESS"

    mocker.patch('apps.internal.actions.delete_request', side_effect=Exception('Test error'))

    result = delete_integration_record(workspace_id)
    assert result == "FAILED"
