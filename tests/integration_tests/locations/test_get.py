import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestLocationsGet(BaseTestGet):
    """
    Test locations GET operations.
    """
    REST_MODULE_NAME = 'locations'
    SOAP_MODULE_NAME = 'locations'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['id', 'name', 'status']
    SOAP_FIELDS = ['LOCATIONID', 'NAME', 'STATUS']
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
            'rest': 'status',
            'soap': 'STATUS'
        }
    ]
