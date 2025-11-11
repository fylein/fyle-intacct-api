import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet
from tests.integration_tests.base.rest_client import RestClient
from tests.integration_tests.base.soap_client import SoapClient


@pytest.mark.integration
class TestAllocationEntriesGet(BaseTestGet):
    """
    Test allocation entries GET operations.
    """
    REST_MODULE_NAME = 'allocations'
    SOAP_MODULE_NAME = 'allocation_entry'
    ALLOWED_METHODS = ['get_all']
    REST_FIELDS = ['id', 'key', 'status']
    SOAP_FIELDS = ['ALLOCATIONID', 'ALLOCATIONKEY', 'STATUS']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'id'
        },
        {
            'rest': 'name',
            'soap': 'name'
        }
    ]

    def test_get_all(self, rest_client: RestClient, soap_client: SoapClient) -> None:
        """
        Test get all method.
        :param rest_client: REST client
        :param soap_client: SOAP client
        :return: None
        """
        if 'get_all' not in self.ALLOWED_METHODS:
            pytest.skip(f"Method 'get_all' not allowed for {self.REST_MODULE_NAME}")

        rest_module = self.get_module(rest_client, self.REST_MODULE_NAME)
        soap_module = self.get_module(soap_client, self.SOAP_MODULE_NAME)

        rest_response = rest_module.get_by_key(key='1')['ia::result']
        soap_response = soap_module.get_all_generator(field='allocation.ALLOCATIONID', value='RENT')

        self.assert_get_all_response(rest_response, soap_response)

    def assert_get_all_response(self, rest_response: list, soap_response: list) -> None:
        """
        Assert the get all response.
        :param rest_response: REST response
        :param soap_response: SOAP response
        :return: None
        """
        soap_response = list(soap_response)
        assert len(rest_response['lines']) == len(soap_response[0]), f"Length of REST and SOAP lines do not match: {len(rest_response['lines'])} != {len(list(soap_response)[0])}"
