import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestDepartmentsGet(BaseTestGet):
    """
    Test departments GET operations.
    """
    REST_MODULE_NAME = 'departments'
    SOAP_MODULE_NAME = 'departments'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['id', 'name', 'status']
    SOAP_FIELDS = ['DEPARTMENTID', 'TITLE', 'STATUS']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'DEPARTMENTID'
        },
        {
            'rest': 'name',
            'soap': 'TITLE'
        },
        {
            'rest': 'status',
            'soap': 'STATUS'
        }
    ]
