import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet
from tests.integration_tests.base.rest_client import RestClient
from tests.integration_tests.base.soap_client import SoapClient


@pytest.mark.integration
class TestCCAccountsGet(BaseTestGet):
    """
    Test charge card accounts GET operations.
    """
    REST_MODULE_NAME = 'charge_card_accounts'
    SOAP_MODULE_NAME = 'charge_card_accounts'
    ALLOWED_METHODS = ['get_by_query']
    REST_FIELDS = ['id', 'status']
    SOAP_FIELDS = ['CARDID', 'STATUS']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'CARDID'
        },
        {
            'rest': 'status',
            'soap': 'STATUS'
        }
    ]

    def test_get_by_query(self, rest_client: RestClient, soap_client: SoapClient) -> None:
        """
        Get by query parameters.
        """
        rest_module = self.get_module(rest_client, self.REST_MODULE_NAME)
        soap_module = self.get_module(soap_client, self.SOAP_MODULE_NAME)

        rest_parameters = {
            'fields': self.REST_FIELDS,
            'filters': [{
                '$eq': {
                    'status': 'active'
                }
            },{
                '$eq': {
                    'accountDetails.accountType': 'credit'
                }
            }]
        }

        soap_parameters = {
            'and_filter': [('equalto', 'LIABILITYTYPE', 'Credit'), ('equalto', 'STATUS', 'active')],
            'fields': self.SOAP_FIELDS
        }

        rest_response = list(rest_module.get_all_generator(**rest_parameters))
        soap_response = soap_module.get_by_query(**soap_parameters)

        self.assert_get_all_generator_response(rest_response[0], soap_response)
