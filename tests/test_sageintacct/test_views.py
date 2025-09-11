import json

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

    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_credentials.delete()

    response = api_client.post(url)
    assert response.status_code == 400

    response = json.loads(response.content)
    assert response['message'] == 'Sage Intacct credentials not found workspace_id - 1'
