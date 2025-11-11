import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestProjectsGet(BaseTestGet):
    """
    Test projects GET operations.
    """
    REST_MODULE_NAME = 'projects'
    SOAP_MODULE_NAME = 'projects'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['id', 'name', 'status', 'customer.id', 'customer.name']
    SOAP_FIELDS = ['CUSTOMERID', 'CUSTOMERNAME', 'NAME', 'PROJECTID', 'STATUS']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'PROJECTID'
        },
        {
            'rest': 'customer.id',
            'soap': 'CUSTOMERID'
        },
        {
            'rest': 'customer.name',
            'soap': 'CUSTOMERNAME'
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
