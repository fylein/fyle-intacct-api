import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestCustomersGet(BaseTestGet):
    """
    Test customers GET operations.
    """
    REST_MODULE_NAME = 'customers'
    SOAP_MODULE_NAME = 'customers'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['id', 'name', 'status']
    SOAP_FIELDS = ['NAME', 'CUSTOMERID', 'STATUS']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'CUSTOMERID'
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
