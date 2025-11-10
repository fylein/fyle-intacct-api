from datetime import datetime
import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestCostCodesGet(BaseTestGet):
    """
    Test cost codes GET operations.
    """
    REST_MODULE_NAME = 'tasks'
    SOAP_MODULE_NAME = 'tasks'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['key', 'name', 'project.key', 'project.name']
    SOAP_FIELDS = ['TASKID', 'NAME', 'PROJECTID', 'PROJECTNAME']
    LAST_UPDATED_AT = '2022-01-01T00:00:00Z'
    KEY_MAPPINGS = [
        {
            'rest': 'key',
            'soap': 'TASKID'
        },
        {
            'rest': 'name',
            'soap': 'NAME'
        },
        {
            'rest': 'project.key',
            'soap': 'PROJECTID'
        },
        {
            'rest': 'project.name',
            'soap': 'PROJECTNAME'
        }
    ]

    def get_all_generator_rest_parameters(self) -> dict:
        """
        Get REST all generator parameters.
        :return: REST filters
        """
        print(self.LAST_UPDATED_AT)
        return {
            'fields': self.REST_FIELDS,
            'filters': [{
                "$gte": {
                    "audit.modifiedDateTime": self.LAST_UPDATED_AT
                }
            }]
        }

    def get_all_generator_soap_parameters(self) -> dict:
        """
        Get SOAP all generator parameters.
        :return: SOAP filters
        """
        return {
            'fields': self.SOAP_FIELDS,
            'updated_at': datetime.strptime(self.LAST_UPDATED_AT, '%Y-%m-%dT%H:%M:%S%z').strftime('%m/%d/%Y')
        }

    def get_count_rest_parameters(self) -> dict:
        """
        Get REST count parameters.
        :return: REST filters
        """
        return {}

    def get_count_soap_parameters(self) -> dict:
        """
        Get SOAP count parameters.
        :return: SOAP filters
        """
        return {
            'field': None,
            'value': None
        }
