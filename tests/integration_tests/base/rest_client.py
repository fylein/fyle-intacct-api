import os
import requests

from intacctsdk import IntacctRESTSDK


class RestClient:
    """
    Wrapper for Intacct REST SDK
    """
    def __init__(self):
        """
        Initialize the REST client.
        """
        self.sdk = None
        self.access_token = None
        self.refresh_token = None
        self._init_sdk()

    def _init_sdk(self):
        """
        Initialize the SDK.
        :return: None
        """
        credentials = self.get_credentials()
        self.sdk = IntacctRESTSDK(**credentials)
        self.update_refresh_token(refresh_token=self.sdk.refresh_token)

    def get_credentials(self):
        """
        Get REST credentials.
        :return: Dictionary with REST credentials
        """
        return {
            'entity_id': os.environ.get('INTEGRATION_TEST_INTACCT_ENTITY_ID'),
            'client_id': os.environ.get('INTEGRATION_TEST_INTACCT_CLIENT_ID'),
            'client_secret': os.environ.get('INTEGRATION_TEST_INTACCT_CLIENT_SECRET'),
            'refresh_token': self.get_refresh_token()
        }

    def get_refresh_token(self):
        """
        Get refresh token.
        :return: Refresh token
        """
        INTERNAL_API_URL = os.environ.get('INTEGRATION_TEST_INTERNAL_API_URL')
        INTERNAL_API_TOKEN = os.environ.get('INTEGRATION_TEST_INTERNAL_API_TOKEN')
        INTERNAL_API_WORKSPACE_ID = os.environ.get('INTEGRATION_TEST_INTERNAL_API_WORKSPACE_ID')

        response = requests.get(
            f'{INTERNAL_API_URL}/integration_tests/refresh_token/',
            headers={'X-Internal-API-Client-ID': INTERNAL_API_TOKEN},
            params={'workspace_id': INTERNAL_API_WORKSPACE_ID}
        )

        if response.status_code != 200:
            raise Exception(response.json()['error'])

        return response.json().get('refresh_token')

    def update_refresh_token(self, refresh_token: str):
        """
        Update refresh token.
        :return: None
        """
        INTERNAL_API_URL = os.environ.get('INTEGRATION_TEST_INTERNAL_API_URL')
        INTERNAL_API_TOKEN = os.environ.get('INTEGRATION_TEST_INTERNAL_API_TOKEN')
        INTERNAL_API_WORKSPACE_ID = os.environ.get('INTEGRATION_TEST_INTERNAL_API_WORKSPACE_ID')

        response = requests.post(
            f'{INTERNAL_API_URL}/integration_tests/refresh_token/',
            headers={'X-Internal-API-Client-ID': INTERNAL_API_TOKEN},
            data={'workspace_id': INTERNAL_API_WORKSPACE_ID, 'refresh_token': refresh_token}
        )

        if response.status_code != 200:
            raise Exception(response.json()['error'])
