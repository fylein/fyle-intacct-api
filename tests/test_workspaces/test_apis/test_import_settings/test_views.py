import json
from django_q.models import Schedule

from tests.helper import dict_compare_keys

from apps.workspaces.models import Workspace, Configuration
from apps.mappings.models import ImportLog
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


def test_import_settings_validate(db, api_client, test_connection):
    workspace_id = 1

    url = '/api/v2/workspaces/{}/import_settings/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    # with code import PROJECT and DEPARTMENT
    configurations_object = Configuration.objects.get(workspace_id=workspace_id)
    configurations_object.import_categories = False
    configurations_object.import_code_fields = ['PROJECT', 'DEPARTMENT']
    configurations_object.save()

    response = api_client.put(
        url,
        data=data['import_setting_validation_payload'],
        format='json'
    )

    assert response.status_code == 200

    assert dict_compare_keys(json.loads(response.content), data['import_setting_validation_response']) == [], 'import settings api returns a diff in the keys'

    # with removing DEPARTMENT from import_code_fields

    payload_data = data['import_setting_validation_payload']
    payload_data['configurations']['import_code_fields'] = ['PROJECT']

    response = api_client.put(
        url,
        data=payload_data,
        format='json'
    )

    assert response.status_code == 400

    # with importing ACCOUNT
    payload_data = data['import_setting_validation_payload']
    payload_data['configurations']['import_code_fields'] = ['ACCOUNT', 'PROJECT', 'DEPARTMENT']

    response = api_client.put(
        url,
        data=payload_data,
        format='json'
    )

    assert response.status_code == 200

    response_data = data['import_setting_validation_response']
    response_data['configurations']['import_code_fields'] = ['PROJECT', 'DEPARTMENT', 'ACCOUNT']
    assert dict_compare_keys(json.loads(response.content), response_data) == [], 'import settings api returns a diff in the keys'

    # adding _ACCOUNT to import_code_fields even though we have ACCOUNT
    payload_data = data['import_setting_validation_payload']
    payload_data['configurations']['import_code_fields'] = ['_ACCOUNT', 'PROJECT', 'DEPARTMENT']

    response = api_client.put(
        url,
        data=payload_data,
        format='json'
    )

    assert response.status_code == 400

    # importing EXPENSE_TYPE without code
    payload_data = data['import_setting_validation_payload']
    payload_data['configurations']['import_code_fields'] = ['PROJECT', 'DEPARTMENT', 'ACCOUNT']

    response = api_client.put(
        url,
        data=payload_data,
        format='json'
    )

    assert response.status_code == 200

    response_data = data['import_setting_validation_response']
    response_data['configurations']['import_code_fields'] = ['PROJECT', 'DEPARTMENT', 'ACCOUNT', '_EXPENSE_TYPE']
    assert dict_compare_keys(json.loads(response.content), response_data) == [], 'import settings api returns a diff in the keys'