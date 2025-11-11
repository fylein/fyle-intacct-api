import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestVendorsGet(BaseTestGet):
    """
    Test vendors GET operations.
    """
    REST_MODULE_NAME = 'vendors'
    SOAP_MODULE_NAME = 'vendors'
    ALLOWED_METHODS = ['get_all_generator', 'get_single_record', 'get_count']
    REST_FIELDS = ['id', 'name', 'status', 'contacts.default.email1']
    SOAP_FIELDS = ['VENDORID', 'NAME', 'STATUS', 'DISPLAYCONTACT.EMAIL1']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'VENDORID'
        },
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

    def get_single_record_rest_parameters(self) -> dict:
        """
        Get REST single record parameters.
        :return: REST filters
        """
        return {
            'fields': self.REST_FIELDS,
            'filters': [{
                "$eq": {
                    "id": "Ashwin"
                }
            }]
        }

    def get_single_record_soap_parameters(self) -> dict:
        """
        Get SOAP single record parameters.
        :return: SOAP filters
        """
        return {
            'fields': self.SOAP_FIELDS,
            'field': 'VENDORID',
            'value': 'Ashwin'
        }
