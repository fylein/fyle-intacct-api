import pytest
from tests.integration_tests.base.base_test_post import BaseTestPost
from tests.integration_tests.vendors.fixtures import REST_VENDOR_CREATE_PAYLOAD, SOAP_VENDOR_CREATE_PAYLOAD


@pytest.mark.integration
class TestVendorsPost(BaseTestPost):
    """
    Test vendors POST operations.
    """
    REST_MODULE_NAME = 'vendors'
    SOAP_MODULE_NAME = 'vendors'
    REST_FIELDS = ['id', 'name', 'status', 'contacts.default.email1']
    SOAP_FIELDS = ['VENDORID', 'NAME', 'STATUS', 'DISPLAYCONTACT.EMAIL1']
    REST_PAYLOAD = REST_VENDOR_CREATE_PAYLOAD
    SOAP_PAYLOAD = SOAP_VENDOR_CREATE_PAYLOAD
    KEY_MAPPINGS = [
        {
            'rest': 'name',
            'soap': 'NAME'
        },
        {
            'rest': 'status',
            'soap': 'STATUS'
        },
        {
            'rest': 'contacts.default.email1',
            'soap': 'DISPLAYCONTACT.EMAIL1'
        }
    ]

    def get_soap_object_id(self, response: dict) -> str:
        """
        Get SOAP vendor ID from POST response.
        :param response: SOAP POST response
        :return: Vendor ID
        """
        return response['data']['vendor']['RECORDNO']

    def get_soap_get_parameters(self, object_id: str) -> dict:
        """
        Get SOAP GET parameters for vendor.
        :param object_id: Vendor ID
        :return: SOAP GET parameters
        """
        return {
            'field': 'RECORDNO',
            'value': object_id
        }
