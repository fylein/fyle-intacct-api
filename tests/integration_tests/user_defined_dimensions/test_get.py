import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet
from tests.integration_tests.base.rest_client import RestClient
from tests.integration_tests.base.soap_client import SoapClient


@pytest.mark.integration
class TestUDDGet(BaseTestGet):
    """
    Test user defined dimensions GET operations.
    """
    REST_MODULE_NAME = 'dimensions'
    SOAP_MODULE_NAME = 'dimensions'
    ALLOWED_METHODS = ['get_all']
    REST_FIELDS = ['dimensionName', 'dimensionLabel', 'termName', 'isUserDefinedDimension', 'isEnabledInGL']
    SOAP_FIELDS = ['objectName', 'objectLabel', 'termLabel', 'userDefinedDimension', 'enabledInGL']
    KEY_MAPPINGS = [
        {
            'rest': 'dimensionName',
            'soap': 'objectName'
        },
        {
            'rest': 'dimensionLabel',
            'soap': 'objectLabel'
        },
        {
            'rest': 'termName',
            'soap': 'termLabel'
        },
        {
            'rest': 'isUserDefinedDimension',
            'soap': 'userDefinedDimension'
        },
        {
            'rest': 'isEnabledInGL',
            'soap': 'enabledInGL'
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

        rest_response = rest_module.list()
        soap_response = soap_module.get_all()

        self.assert_get_all_response(rest_response, soap_response)

    def assert_get_all_response(self, rest_response: list, soap_response: list) -> None:
        """
        Assert the get all response.
        :param rest_response: REST response
        :param soap_response: SOAP response
        :return: None
        """
        for res in rest_response:
            res.pop('dimensionEndpoint')

        for res in soap_response:
            res['userDefinedDimension'] = res['userDefinedDimension'] == 'true'
            res['enabledInGL'] = res['enabledInGL'] == 'true'

        self.assert_get_all_generator_response(rest_response, soap_response)
