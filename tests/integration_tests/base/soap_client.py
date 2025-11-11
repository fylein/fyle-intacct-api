import os

from sageintacctsdk import SageIntacctSDK


class SoapClient:
    """
    Wrapper for Intacct SOAP SDK
    """
    def __init__(self):
        """
        Initialize the SOAP client.
        """
        self.sdk = None
        self._init_sdk()

    def _init_sdk(self):
        """
        Initialize the SDK.
        :return: None
        """
        credentials = self.get_credentials()
        self.sdk = SageIntacctSDK(**credentials)

    def get_credentials(self):
        """
        Get SOAP credentials.
        :return: Dictionary with SOAP credentials
        """
        return {
            'user_id': os.environ.get('INTEGRATION_TEST_INTACCT_USER_ID'),
            'sender_id': os.environ.get('INTEGRATION_TEST_INTACCT_SENDER_ID'),
            'entity_id': os.environ.get('INTEGRATION_TEST_INTACCT_ENTITY_ID'),
            'company_id': os.environ.get('INTEGRATION_TEST_INTACCT_COMPANY_ID'),
            'user_password': os.environ.get('INTEGRATION_TEST_INTACCT_USER_PASSWORD'),
            'sender_password': os.environ.get('INTEGRATION_TEST_INTACCT_SENDER_PASSWORD')
        }
