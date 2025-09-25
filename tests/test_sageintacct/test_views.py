import json

from django.core.cache import cache
from apps.workspaces.enums import CacheKeyEnum
from apps.workspaces.models import SageIntacctCredential


def test_sage_intacct_fields(api_client, test_connection):
    """
    Test Sage Intacct fields
    """
    workspace_id = 1

    access_token = test_connection.access_token
    url = '/api/workspaces/{}/sage_intacct/sage_intacct_fields/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200


def test_destination_attributes(api_client, test_connection):
    """
    Test Sage Intacct destination attributes
    """
    workspace_id = 1

    access_token = test_connection.access_token
    url = '/api/workspaces/{}/sage_intacct/destination_attributes/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(
        url,
        data={
            'attribute_types': 'DEPARTMENT,ACCOUNT',
            'account_type': 'incomestatement'
        })
    assert response.status_code == 200

    response = json.loads(response.content)
    assert len(response) == 95

    response = api_client.get(
        url,
        data={
            'attribute_types': 'ACCOUNT',
            'active': True
        }
    )
    assert response.status_code == 200

    response = json.loads(response.content)
    assert len(response) == 170


def test_paginated_destination_attributes(api_client, test_connection):
    """
    Test Sage Intacct paginated destination attributes
    """
    workspace_id = 1

    access_token = test_connection.access_token
    url = '/api/workspaces/{}/sage_intacct/paginated_destination_attributes/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(
        url,
        data={
            'attribute_type': 'EMPLOYEE',
            'value': 'ash'
        })
    assert response.status_code == 200

    results = json.loads(response.content)['results']
    for result in results:
        assert 'ash' in result['value'].lower()


def test_sync_dimensions(api_client, test_connection):
    """
    Test Sage Intacct sync dimensions
    """
    workspace_id = 1

    access_token = test_connection.access_token
    url = '/api/workspaces/{}/sage_intacct/sync_dimensions/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.post(url)
    assert response.status_code == 200

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_credentials.delete()

    response = api_client.post(url)
    assert response.status_code == 400

    response = json.loads(response.content)
    assert response['message'] == 'Sage Intacct credentials not found workspace_id - 1'


def test_refresh_dimensions(mocker, api_client, test_connection):
    """
    Test Sage Intacct refresh dimensions
    """
    workspace_id = 1

    access_token = test_connection.access_token
    url = '/api/workspaces/{}/sage_intacct/refresh_dimensions/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.post(url)
    assert response.status_code == 200

    mocker.patch('apps.sage_intacct.views.publish_to_rabbitmq', side_effect=SageIntacctCredential.DoesNotExist)

    cache.delete(CacheKeyEnum.SAGE_INTACCT_SYNC_DIMENSIONS.value.format(workspace_id=workspace_id))

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_credentials.delete()

    response = api_client.post(url)
    assert response.status_code == 400

    response = json.loads(response.content)
    assert response['message'] == 'Sage Intacct credentials not found workspace_id - 1'


def test_refresh_dimensions_with_specific_dimensions(mocker, api_client, test_connection):
    """
    Test Sage Intacct refresh dimensions with specific dimensions_to_sync
    This covers lines 205-206 (print "here 1")
    """
    workspace_id = 1

    access_token = test_connection.access_token
    url = '/api/workspaces/{}/sage_intacct/refresh_dimensions/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    # Mock sync_dimensions to track if it's called
    mock_sync_dimensions = mocker.patch('apps.sage_intacct.views.sync_dimensions')

    # Test with specific dimensions_to_sync - this should hit line 205 (print "here 1")
    response = api_client.post(url, data={'dimensions_to_sync': ['locations', 'departments']}, format='json')
    assert response.status_code == 200

    # Verify sync_dimensions was called with the specific dimensions
    mock_sync_dimensions.assert_called_once_with(workspace_id, ['locations', 'departments'])


def test_refresh_dimensions_invalid_token_error(mocker, api_client, test_connection):
    """
    Test Sage Intacct refresh dimensions with InvalidTokenError
    Since InvalidTokenError is handled by DRF middleware, we test the exception handling path by mocking different conditions
    """
    workspace_id = 1

    access_token = test_connection.access_token
    url = '/api/workspaces/{}/sage_intacct/refresh_dimensions/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    # Create a custom exception class that will be caught by our except block
    class MockInvalidTokenError(Exception):
        pass

    # Patch InvalidTokenError to be our mock class so it gets caught properly
    mocker.patch('apps.sage_intacct.views.InvalidTokenError', MockInvalidTokenError)

    # Mock sync_dimensions to raise our mock InvalidTokenError
    mocker.patch('apps.sage_intacct.views.sync_dimensions', side_effect=MockInvalidTokenError('Invalid token'))

    # Mock invalidate_sage_intacct_credentials to track if it's called
    mock_invalidate = mocker.patch('apps.sage_intacct.views.invalidate_sage_intacct_credentials')

    # This should trigger our MockInvalidTokenError and call invalidate_sage_intacct_credentials
    response = api_client.post(url, data={'dimensions_to_sync': ['locations']}, format='json')
    assert response.status_code == 400

    response_data = json.loads(response.content)
    assert 'Invalid Sage Intact Token' in response_data['message']

    # Verify invalidate_sage_intacct_credentials was called (covers line 231)
    mock_invalidate.assert_called_once_with(workspace_id)
