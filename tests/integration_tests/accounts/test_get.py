import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestAccountsGet(BaseTestGet):
    """
    Test accounts GET operations.
    """
    REST_MODULE_NAME = 'accounts'
    SOAP_MODULE_NAME = 'accounts'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['id', 'name', 'accountType', 'status']
    SOAP_FIELDS = ['ACCOUNTNO', 'TITLE', 'ACCOUNTTYPE', 'STATUS']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'ACCOUNTNO'
        },
        {
            'rest': 'name',
            'soap': 'TITLE'
        },
        {
            'rest': 'status',
            'soap': 'STATUS'
        },
        {
            'rest': 'accountType',
            'soap': 'ACCOUNTTYPE'
        }
    ]
