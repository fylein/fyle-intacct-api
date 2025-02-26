from tests.test_fyle.fixtures import data as fyle_data


def test_get_profile_view(api_client, test_connection):
    """
    Test get profile view
    """
    access_token = test_connection.access_token

    url = '/api/user/profile/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200


def test_get_fyle_orgs_view(api_client, test_connection, mocker):
    """
    Test get fyle orgs view
    """
    access_token = test_connection.access_token
    mocker.patch(
        'apps.users.views.get_fyle_orgs',
        return_value=fyle_data['get_all_orgs']
    )

    url = '/api/user/orgs/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200
