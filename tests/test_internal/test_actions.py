from apps.internal.actions import delete_integration_record, get_accounting_fields, get_exported_entry
from tests.test_sageintacct.fixtures import data


def test_get_accounting_fields(db, mocker):
    """
    Test get_accounting_fields function
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


def test_get_exported_entry(db, mocker):
    """
    Test get_exported_entry function
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


def test_delete_integration_record(db, mocker):
    """
    Test delete_integration_record function
    """
    workspace_id = 1

    # Mock FyleCredential.objects.get to return a mock object with refresh_token
    mock_credential = mocker.Mock()
    mock_credential.refresh_token = 'test_refresh_token'
    mocker.patch('apps.internal.actions.FyleCredential.objects.get', return_value=mock_credential)

    # Mock delete_request to not raise any exception
    mocker.patch('apps.internal.actions.delete_request')

    result = delete_integration_record(workspace_id)
    assert result == "SUCCESS"

    # Mock delete_request to raise an exception
    mocker.patch('apps.internal.actions.delete_request', side_effect=Exception('Test error'))

    result = delete_integration_record(workspace_id)
    assert result == "FAILED"
