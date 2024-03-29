import json
from django_q.models import Schedule

from tests.helper import dict_compare_keys

from apps.workspaces.models import Workspace
from fyle_accounting_mappings.models import MappingSetting
from .fixtures import data


def test_import_settings(mocker, api_client, test_connection):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
        return_value={
            'options': ['samp'], 
            'updated_at': '2020-06-11T13:14:55.201598+00:00',
            'is_mandatory': False
        }
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value = {
            "data": {"id": 12}
        }
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.sync',
        return_value=None
    )
    
    mocker.patch(
        'fyle_integrations_platform_connector.apis.DependentFields.get_project_field_id',
        return_value=12
    )

    workspace = Workspace.objects.get(id=1)
    workspace.onboarding_state = 'IMPORT_SETTINGS'
    workspace.save()

    url = '/api/v2/workspaces/1/import_settings/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.put(
        url,
        data=data['import_settings'],
        format='json'
    )

    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response, data['response']) == [], 'workspaces api returns a diff in the keys'

    response = api_client.put(
        url,
        data=data['import_settings_without_mapping'],
        format='json'
    )
    assert response.status_code == 200

    # Test if import_projects add schedule or not
    url = '/api/v2/workspaces/1/import_settings/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.put(
        url,
        data=data['import_settings_schedule_check'],
        format='json'
    )

    assert response.status_code == 200

    mapping = MappingSetting.objects.filter(workspace_id=1, source_field='PROJECT').first()

    assert mapping.import_to_fyle  == True

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(1),
    ).first()

    assert schedule.func == 'apps.mappings.imports.queues.chain_import_fields_to_fyle'
    assert schedule.args == '1'

    invalid_configurations = data['import_settings']
    invalid_configurations['configurations'] = {}
    response = api_client.put(
        url,
        data=invalid_configurations,
        format='json'
    )
    assert response.status_code == 400

    response = json.loads(response.content)
    assert response['non_field_errors'] == ['Workspace general settings are required']

    response = api_client.put(
        url,
        data=data['invalid_general_mappings'],
        format='json'
    )
    assert response.status_code == 400

    response = api_client.put(
        url,
        data=data['invalid_mapping_settings'],
        format='json'
    )
    assert response.status_code == 400
