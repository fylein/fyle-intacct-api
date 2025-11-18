def test_get_profile_view(api_client, test_connection):
    """
    Test get profile view
    """
    access_token = test_connection.access_token

    url = '/api/user/profile/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200
