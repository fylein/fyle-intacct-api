import json

from tests.helper import dict_compare_keys

from apps.workspaces.models import Workspace, FyleCredential

from .fixtures import data


def test_advanced_settings(api_client, test_connection):
    """
    Test case to test advanced settings
    """
    FyleCredential.objects.update_or_create(
        workspace_id=1,
        defaults={
            'refresh_token': 'ey.ey.ey',
            'cluster_domain': 'cluster_domain'
        }
    )
    workspace = Workspace.objects.get(id=1)
    workspace.onboarding_state = 'ADVANCED_CONFIGURATION'
    workspace.save()

    url = '/api/v2/workspaces/1/advanced_settings/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.put(
        url,
        data=data['advanced_settings'],
        format='json'
    )

    assert response.status_code == 200

    response = json.loads(response.content)
    workspace = Workspace.objects.get(id=1)

    assert dict_compare_keys(response, data['response']) == [], 'workspaces api returns a diff in the keys'
    assert workspace.onboarding_state == 'COMPLETE'

    response = api_client.put(
        url,
        data={
            'general_mappings':{}
        },
        format='json'
    )

    assert response.status_code == 400

    response = api_client.put(
        url,
        data={
            'configurations':{}
        },
        format='json'
    )

    assert response.status_code == 400

    response = api_client.put(
        url,
        data={
            'workspace_schedules':{}
        },
        format='json'
    )

    assert response.status_code == 400
