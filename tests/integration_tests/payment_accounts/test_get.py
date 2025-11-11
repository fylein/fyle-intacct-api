import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestPaymentAccountsGet(BaseTestGet):
    """
    Test payment accounts GET operations.
    """
    REST_MODULE_NAME = 'checking_accounts'
    SOAP_MODULE_NAME = 'checking_accounts'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['id', 'bankAccountDetails.bankName']
    SOAP_FIELDS = ['BANKNAME', 'BANKACCOUNTID']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'BANKACCOUNTID'
        },
        {
            'rest': 'bankAccountDetails.bankName',
            'soap': 'BANKNAME'
        }
    ]

    def get_all_generator_rest_parameters(self) -> dict:
        """
        Get REST all generator parameters.
        :return: REST filters
        """
        return {
            'fields': self.REST_FIELDS
        }

    def get_all_generator_soap_parameters(self) -> dict:
        """
        Get SOAP all generator parameters.
        :return: SOAP filters
        """
        return {
            'fields': self.SOAP_FIELDS
        }
