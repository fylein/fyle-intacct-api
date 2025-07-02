from unittest.mock import Mock

import pytest

from apps.internal.helpers import delete_request, is_safe_environment


def test_delete_request(mocker):
    """
    Test delete_request function with various scenarios
    """
    # Test successful request with refresh token and response text
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"result": "success"}'

    mocker.patch('apps.internal.helpers.requests.delete', return_value=mock_response)
    mocker.patch('apps.internal.helpers.get_access_token', return_value='mock_access_token')

    url = 'http://some.url/delete'
    body = {'tpa_name': 'Test Integration'}
    refresh_token = 'test_refresh_token'

    result = delete_request(url, body, refresh_token)

    assert result == {"result": "success"}

    # Test successful request without refresh token
    mock_response.status_code = 204
    mock_response.text = ''

    result = delete_request(url, body)

    assert result is None

    # Test error case - non-success status code
    mock_response.status_code = 400
    mock_response.text = 'Bad Request'

    with pytest.raises(Exception) as exc_info:
        delete_request(url, body, refresh_token)

    assert str(exc_info.value) == 'Bad Request'


def test_is_safe_environment(mocker):
    """
    Test is_safe_environment function with different settings
    """
    # Test when ALLOW_E2E_SETUP is True
    mock_settings = Mock()
    mock_settings.ALLOW_E2E_SETUP = True
    mocker.patch('apps.internal.helpers.settings', mock_settings)
    assert is_safe_environment() is True

    # Test when ALLOW_E2E_SETUP is not set in env
    mock_settings.ALLOW_E2E_SETUP = None
    assert is_safe_environment() is None
