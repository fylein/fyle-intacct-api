import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestClassesGet(BaseTestGet):
    """
    Test classes GET operations.
    """
    REST_MODULE_NAME = 'classes'
    SOAP_MODULE_NAME = 'classes'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['id', 'name', 'status']
    SOAP_FIELDS = ['CLASSID', 'NAME', 'STATUS']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'CLASSID'
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
