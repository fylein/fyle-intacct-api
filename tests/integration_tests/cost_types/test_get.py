import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestCostTypesGet(BaseTestGet):
    """
    Test cost types GET operations.
    """
    REST_MODULE_NAME = 'cost_types'
    SOAP_MODULE_NAME = 'cost_types'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['id', 'key', 'name', 'status',  'project.id', 'project.name', 'project.key', 'task.id', 'task.name', 'task.key', 'audit.createdDateTime', 'audit.modifiedDateTime']
    SOAP_FIELDS = ['COSTTYPEID', 'RECORDNO', 'NAME', 'STATUS', 'PROJECTID', 'PROJECTNAME', 'PROJECTKEY', 'TASKID', 'TASKNAME', 'TASKKEY', 'WHENCREATED', 'WHENMODIFIED']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'COSTTYPEID'
        },
        {
            'rest': 'key',
            'soap': 'RECORDNO'
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
            'rest': 'project.id',
            'soap': 'PROJECTID'
        },
        {
            'rest': 'project.name',
            'soap': 'PROJECTNAME'
        },
        {
            'rest': 'project.key',
            'soap': 'PROJECTKEY'
        },
        {
            'rest': 'task.id',
            'soap': 'TASKID'
        },
        {
            'rest': 'task.name',
            'soap': 'TASKNAME'
        },
        {
            'rest': 'task.key',
            'soap': 'TASKKEY'
        },
        {
            'rest': 'audit.createdDateTime',
            'soap': 'WHENCREATED'
        },
        {
            'rest': 'audit.modifiedDateTime',
            'soap': 'WHENMODIFIED'
        }
    ]
