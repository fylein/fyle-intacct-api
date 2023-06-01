import json
from tests.helper import dict_compare_keys
from apps.workspaces.models import Workspace, Configuration
from .fixtures import data


def test_export_settings(api_client, test_connection):

    workspace = Workspace.objects.get(id=1)
    workspace.onboarding_state = 'EXPORT_SETTINGS'
    workspace.save()

    url = '/api/v2/workspaces/1/export_settings/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.put(
        url,
        data=data['export_settings'],
        format='json'
    )

    assert response.status_code == 200

    response = json.loads(response.content)
    workspace = Workspace.objects.get(id=1)

    assert dict_compare_keys(response, data['response']) == [], 'workspaces api returns a diff in the keys'
    assert workspace.onboarding_state == 'IMPORT_SETTINGS'

    invalid_workspace_general_settings = data['export_settings_missing_values']
    invalid_workspace_general_settings['workspace_general_settings'] = {}
    response = api_client.put(
        url,
        data=invalid_workspace_general_settings,
        format='json'
    )

    assert response.status_code == 400

    invalid_expense_group_settings = data['export_settings']
    invalid_expense_group_settings['expense_group_settings'] = {}
    invalid_expense_group_settings['workspace_general_settings'] = {'reimbursable_expenses_object': 'EXPENSE',
        'corporate_credit_card_expenses_object': 'BILL'
    }

    response = api_client.put(
        url,
        data=invalid_expense_group_settings,
        format='json'
    )

    assert response.status_code == 400