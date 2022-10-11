import pytest
import json
from apps.mappings.models import GeneralMapping, LocationEntityMapping
from apps.workspaces.models import Configuration
from .fixtures import data

    
@pytest.mark.django_db(databases=['default'])
def test_get_general_mappings(api_client, test_connection):
    '''
    Test get of general mappings
    '''
    workspace_id = 1
    url = '/api/workspaces/{}/mappings/general/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200
    response = json.loads(response.content)

    general_mapping = GeneralMapping.objects.get(workspace_id=1)
    general_mapping.default_ccc_vendor_name = ''
    general_mapping.use_employee_department = True
    general_mapping.save()
    response = api_client.get(url)

    GeneralMapping.objects.get(workspace_id=1).delete()

    response = api_client.get(url)

    assert response.status_code == 400
    assert response.data['message'] == 'General mappings do not exist for the workspace'


@pytest.mark.django_db(databases=['default'])
def test_post_general_mappings(api_client, test_connection):
    '''
    Test post of general mappings
    '''
    workspace_id = 1
    url = '/api/workspaces/{}/mappings/general/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    payload = data['general_mapping_payload']

    response = api_client.post(
        url,
        data=payload,
    )
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response['default_department_name'] == 'Admin'

    general_settings = Configuration.objects.get(workspace_id=workspace_id)

    general_settings.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    general_settings.save()

    response = api_client.post(
        url,
        data=payload
    )
    assert response.status_code == 200

    general_settings.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    general_settings.save()

    response = api_client.post(
        url,
        data=payload
    )
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response['default_tax_code_id'] == 'INPUT'


def test_auto_map_employee(api_client, test_connection):
    workspace_id = 1

    url = '/api/workspaces/{}/mappings/auto_map_employees/trigger/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_charge_card_name = 'sdfgh'
    general_mappings.save()

    response = api_client.post(url)
    assert response.status_code == 200

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.auto_map_employees = ''
    configuration.save()

    response = api_client.post(url)
    assert response.status_code == 400

    general_mappings.delete()
    configuration.auto_map_employees = 'EMAIL'
    configuration.save()

    response = api_client.post(url)
    assert response.status_code == 400

    response = json.loads(response.content)
    assert response['message'] == 'General mappings do not exist for this workspace'


def test_location_entity_mappings(api_client, test_connection):
    workspace_id = 1

    url = '/api/workspaces/{}/mappings/location_entity/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    location_entity_mappings = LocationEntityMapping.objects.get(workspace_id=workspace_id)
    location_entity_mappings.delete()

    response = api_client.get(url)
    assert response.status_code == 400