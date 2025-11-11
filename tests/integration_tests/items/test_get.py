import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestItemsGet(BaseTestGet):
    """
    Test items GET operations.
    """
    REST_MODULE_NAME = 'items'
    SOAP_MODULE_NAME = 'items'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['id', 'name', 'status', 'itemType']
    SOAP_FIELDS = ['NAME', 'ITEMID', 'ITEMTYPE', 'STATUS']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'ITEMID'
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
            'rest': 'itemType',
            'soap': 'ITEMTYPE'
        }
    ]
