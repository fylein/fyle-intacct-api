import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestLocationEntitiesGet(BaseTestGet):
    """
    Test location entities GET operations.
    """
    REST_MODULE_NAME = 'location_entities'
    SOAP_MODULE_NAME = 'location_entities'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['id', 'name', 'operatingCountry']
    SOAP_FIELDS = ['NAME', 'LOCATIONID', 'OPCOUNTRY']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'LOCATIONID'
        },
        {
            'rest': 'name',
            'soap': 'NAME'
        },
        {
            'rest': 'operatingCountry',
            'soap': 'OPCOUNTRY'
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
