import os

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

    def get_credentials(self):
        """
        Get REST credentials.
        :return: Dictionary with REST credentials
        """
        return {
            'entity_id': os.environ.get('INTACCT_ENTITY_ID'),
            'client_id': os.environ.get('INTACCT_CLIENT_ID'),
            'client_secret': os.environ.get('INTACCT_CLIENT_SECRET'),
            'refresh_token': os.environ.get('INTACCT_REFRESH_TOKEN'),
            'access_token': os.environ.get('INTACCT_ACCESS_TOKEN')
        }
