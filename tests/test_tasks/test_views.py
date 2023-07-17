def test_get_queryset(api_client, test_connection):
    workspace_id = 1

    access_token = test_connection.access_token
    url = '/api/workspaces/{}/tasks/all/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url, {
        'expense_group_ids': '4',
        'task_type': 'CREATING_EXPENSE',
        'status': 'ALL'
    })
    assert response.status_code==200


def test_new_task_get_queryset(api_client, test_connection):
    workspace_id = 1

    access_token = test_connection.access_token
    url = '/api/workspaces/{}/tasks/v2/all/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url, {
        'expense_group_ids': '4',
        'task_type': 'CREATING_EXPENSE',
        'status': 'ALL'
    })
    assert response.status_code==200

def test_get_task_by_id(api_client, test_connection):
    workspace_id = 1
    
    access_token = test_connection.access_token
    url = '/api/workspaces/{}/tasks/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url, {
        'id': '1'
    })
    assert response.status_code==200


def test_get_task_by_expense_group_id(api_client, test_connection):
    workspace_id = 1
    
    access_token = test_connection.access_token
    url = '/api/workspaces/{}/tasks/expense_group/3/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code==200
