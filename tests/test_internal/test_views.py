from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.workspaces.models import Workspace
from apps.workspaces.permissions import IsAuthenticatedForInternalAPI
from tests.test_internal.fixtures import data as internal_data
from tests.test_sageintacct.fixtures import data


@pytest.mark.django_db(databases=['default'])
@patch.object(IsAuthenticatedForInternalAPI, 'has_permission', return_value=True)
def test_qbo_fields_view(db, api_client, mocker):
    """
    Test qbo_fields_view
    """
    url = reverse('accounting-fields')

    response = api_client.get(url)
    assert response.status_code == 400

    response = api_client.get(url, {'org_id': 'or79Cob97KSh'})
    assert response.status_code == 400

    mocker.patch(
        'sageintacctsdk.apis.Employees.get_all_generator',
        return_value=data['get_employees']
    )

    response = api_client.get(url, {'org_id': 'or79Cob97KSh', 'resource_type': 'employees'})
    assert response.status_code == 200


@pytest.mark.django_db(databases=['default'])
@patch.object(IsAuthenticatedForInternalAPI, 'has_permission', return_value=True)
def test_exported_entry_view(db, api_client, mocker):
    """
    Test exported_entry_view
    """
    url = reverse('exported-entry')

    response = api_client.get(url)
    assert response.status_code == 400

    response = api_client.get(url, {'org_id': 'or79Cob97KSh'})
    assert response.status_code == 400

    response = api_client.get(url, {'org_id': 'or79Cob97KSh', 'resource_type': 'bill'})
    assert response.status_code == 400

    mocker.patch(
        'sageintacctsdk.apis.Bills.get',
        return_value={'summa': 'hehe'}
    )

    response = api_client.get(url, {'org_id': 'or79Cob97KSh', 'resource_type': 'bill', 'internal_id': '1'})
    assert response.status_code == 200


@pytest.mark.django_db(databases=['default'])
@patch.object(IsAuthenticatedForInternalAPI, 'has_permission', return_value=True)
def test_e2e_setup_view_success(db, api_client, mocker):
    """
    Test E2ESetupView successful setup
    """
    url = reverse('e2e-setup-org')

    # Mock environment safety check
    mocker.patch('apps.internal.serializers.is_safe_environment', return_value=True)

    # Mock E2ESetupService
    mock_service = mocker.patch('apps.internal.views.E2ESetupService')
    mock_service.return_value.setup_organization.return_value = {
        'workspace_id': 1,
        'org_name': 'E2E Integration Tests'
    }

    payload = internal_data['e2e_setup_payload']

    response = api_client.post(url, payload, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['success'] is True
    assert 'Test organization setup completed successfully' in response.data['message']
    assert response.data['data']['workspace_id'] == 1


@pytest.mark.django_db(databases=['default'])
@patch.object(IsAuthenticatedForInternalAPI, 'has_permission', return_value=True)
def test_e2e_setup_view_failures(db, api_client, mocker):
    """
    Test E2ESetupView failure scenarios
    """
    url = reverse('e2e-setup-org')

    # Test 1: Unsafe environment
    mocker.patch('apps.internal.serializers.is_safe_environment', return_value=False)

    payload = internal_data['e2e_setup_payload']

    response = api_client.post(url, payload, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'only available in development/staging environments' in str(response.data)

    # Test 2: Invalid workspace ID
    mocker.patch('apps.internal.serializers.is_safe_environment', return_value=True)

    response = api_client.post(url, internal_data['e2e_setup_invalid_workspace_id_payload'], format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'workspace_id' in response.data

    # Test 3: Service exception
    mocker.patch('apps.internal.serializers.is_safe_environment', return_value=True)

    mock_service = mocker.patch('apps.internal.views.E2ESetupService')
    mock_service.return_value.setup_organization.side_effect = Exception('Setup failed')

    response = api_client.post(url, payload, format='json')

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert 'Setup failed: Setup failed' in response.data['error']


@pytest.mark.django_db(databases=['default'])
@patch.object(IsAuthenticatedForInternalAPI, 'has_permission', return_value=True)
def test_e2e_destroy_view_success(db, api_client, mocker):
    """
    Test E2EDestroyView successful cleanup
    """
    url = reverse('e2e-destroy')

    # Mock environment safety check
    mocker.patch('apps.internal.serializers.is_safe_environment', return_value=True)

    # Mock workspace lookup
    mock_workspace = mocker.Mock()
    mock_workspace.id = 2
    mock_workspace.name = 'E2E Integration Tests'
    mock_workspace.fyle_org_id = 'test_org_123'

    mocker.patch('apps.internal.views.Workspace.objects.get', return_value=mock_workspace)

    # Mock cleanup functions
    mocker.patch('apps.internal.views.delete_integration_record', return_value={'success': True})

    # Mock database cursor
    mock_cursor = mocker.Mock()
    mock_cursor.execute.return_value = None
    mock_cursor.fetchone.return_value = ['Workspace deleted successfully']
    mock_connection = mocker.patch('apps.internal.views.connection')
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    payload = internal_data['e2e_destroy_payload']

    response = api_client.post(url, payload, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['success'] is True
    assert 'Test workspace deleted successfully' in response.data['message']
    assert response.data['data']['workspace_id'] == 2
    assert response.data['data']['org_id'] == 'test_org_123'


@pytest.mark.django_db(databases=['default'])
@patch.object(IsAuthenticatedForInternalAPI, 'has_permission', return_value=True)
def test_e2e_destroy_view_failures(db, api_client, mocker):
    """
    Test E2EDestroyView failure scenarios
    """

    mock_workspace = mocker.Mock()
    mock_workspace.id = 2
    mock_workspace.name = 'E2E Integration Tests'

    url = reverse('e2e-destroy')

    # Test 1: Unsafe environment
    mocker.patch('apps.internal.serializers.is_safe_environment', return_value=False)
    mocker.patch('apps.internal.views.Workspace.objects.get', return_value=mock_workspace)

    payload = internal_data['e2e_destroy_payload']

    response = api_client.post(url, payload, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'only available in development/staging environments' in str(response.data)

    # Test 2a: Empty org_id (Org ID is required)
    mocker.patch('apps.internal.serializers.is_safe_environment', return_value=True)

    response = api_client.post(url, internal_data['e2e_destroy_empty_org_id_payload'], format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'org_id' in response.data

    # Test 2b: Safety check failed (workspace name not in allowed list)
    mock_unsafe_workspace = mocker.Mock()
    mock_unsafe_workspace.name = 'Production Workspace'  # Not in allowed list
    mocker.patch('apps.internal.views.Workspace.objects.get', return_value=mock_unsafe_workspace)

    response = api_client.post(url, internal_data['e2e_destroy_payload'], format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    org_id_errors = response.data.get('org_id')
    assert org_id_errors and len(org_id_errors) > 0 and 'Safety check failed' in org_id_errors[0]

    # Test 3: Workspace not found
    mocker.patch('apps.internal.serializers.is_safe_environment', return_value=True)

    mocker.patch('apps.internal.serializers.Workspace.objects.get',
                 side_effect=Workspace.DoesNotExist('Workspace not found'))

    response = api_client.post(url, internal_data['e2e_destroy_nonexistent_payload'], format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    org_id_errors = response.data.get('org_id')
    assert org_id_errors and len(org_id_errors) > 0 and 'No workspace found' in org_id_errors[0]

    # Test 4: Integration deletion exception
    mocker.patch('apps.internal.serializers.is_safe_environment', return_value=True)

    mocker.patch('apps.internal.views.Workspace.objects.get', return_value=mock_workspace)

    mocker.patch('apps.internal.views.delete_integration_record',
                 side_effect=Exception('Integration deletion failed'))

    response = api_client.post(url, internal_data['e2e_destroy_payload'], format='json')

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert 'Cleanup failed: Integration deletion failed' in response.data['error']
