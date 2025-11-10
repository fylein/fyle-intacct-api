import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet
from tests.integration_tests.base.rest_client import RestClient
from tests.integration_tests.base.soap_client import SoapClient


@pytest.mark.integration
class TestUDDValuesGet(BaseTestGet):
    """
    Test user defined dimensions values GET operations.
    """
    REST_MODULE_NAME = 'dimensions'
    SOAP_MODULE_NAME = 'dimension_values'
    ALLOWED_METHODS = ['get_all', 'get_count']
    REST_FIELDS = ['id', 'name']
    SOAP_FIELDS = ['id', 'name']
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

        rest_response = list(rest_module.get_all_generator(fields=self.REST_FIELDS, dimension_name='udd_test'))
        soap_response = soap_module.get_all(dimension_name='UDD_TEST')

        self.assert_get_all_response(rest_response, soap_response)

    def get_count_rest_parameters(self) -> dict:
        """
        Get REST count parameters.
        :return: REST filters
        """
        return {
            'dimension_name': 'udd_test'
        }

    def get_count_soap_parameters(self) -> dict:
        """
        Get SOAP count parameters.
        :return: SOAP filters
        """
        return {
            'dimension_name': 'UDD_TEST'
        }

    def assert_get_all_response(self, rest_response: list, soap_response: list) -> None:
        """
        Assert the get all response.
        :param rest_response: REST response
        :param soap_response: SOAP response
        :return: None
        """
        for res in soap_response:
            res.pop('createdBy')
            res.pop('updatedBy')

        self.assert_get_all_generator_response(rest_response[0], soap_response)
