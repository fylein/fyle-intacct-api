import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestAllocationsGet(BaseTestGet):
    """
    Test allocations GET operations.
    """
    REST_MODULE_NAME = 'allocations'
    SOAP_MODULE_NAME = 'allocations'
    ALLOWED_METHODS = ['get_all_generator']
    REST_FIELDS = ['id', 'status', 'key']
    SOAP_FIELDS = ['ALLOCATIONID', 'STATUS', 'RECORDNO']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'ALLOCATIONID'
        },
        {
            'rest': 'status',
            'soap': 'STATUS'
        },
        {
            'rest': 'key',
            'soap': 'RECORDNO'
        }
    ]
