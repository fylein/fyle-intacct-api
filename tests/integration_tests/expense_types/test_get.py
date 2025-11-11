import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestExpenseTypesGet(BaseTestGet):
    """
    Test expense types GET operations.
    """
    REST_MODULE_NAME = 'expense_types'
    SOAP_MODULE_NAME = 'expense_types'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['key', 'description', 'glAccount.id', 'glAccount.name', 'status']
    SOAP_FIELDS = ['ACCOUNTLABEL', 'DESCRIPTION', 'GLACCOUNTNO', 'GLACCOUNTTITLE', 'STATUS']
    KEY_MAPPINGS = [
        {
            'rest': 'key',
            'soap': 'ACCOUNTLABEL'
        },
        {
            'rest': 'description',
            'soap': 'DESCRIPTION'
        },
        {
            'rest': 'glAccount.id',
            'soap': 'GLACCOUNTNO'
        },
        {
            'rest': 'glAccount.name',
            'soap': 'GLACCOUNTTITLE'
        },
        {
            'rest': 'status',
            'soap': 'STATUS'
        }
    ]
