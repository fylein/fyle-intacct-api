import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestEmployeesGet(BaseTestGet):
    """
    Test employees GET operations.
    """
    REST_MODULE_NAME = 'employees'
    SOAP_MODULE_NAME = 'employees'
    ALLOWED_METHODS = ['get_all_generator', 'get_single_record', 'get_count']
    REST_FIELDS = ['id', 'name', 'status', 'primaryContact.email1', 'primaryContact.printAs',  'department.id', 'location.id']
    SOAP_FIELDS = ['EMPLOYEEID', 'CONTACT.CONTACTNAME', 'STATUS', 'CONTACT.EMAIL1', 'CONTACT.PRINTAS', 'DEPARTMENTID', 'LOCATIONID']
    KEY_MAPPINGS = [
        {
            'rest': 'id',
            'soap': 'EMPLOYEEID'
        },
        {
            'rest': 'name',
            'soap': 'CONTACT.CONTACTNAME'
        },
        {
            'rest': 'status',
            'soap': 'STATUS'
        },
        {
            'rest': 'primaryContact.email1',
            'soap': 'CONTACT.EMAIL1'
        },
        {
            'rest': 'primaryContact.printAs',
            'soap': 'CONTACT.PRINTAS'
        },
        {
            'rest': 'department.id',
            'soap': 'DEPARTMENTID'
        },
        {
            'rest': 'location.id',
            'soap': 'LOCATIONID'
        }
    ]

    def get_single_record_rest_parameters(self) -> dict:
        """
        Get REST single record parameters.
        :return: REST filters
        """
        return {
            'fields': self.REST_FIELDS,
            'filters': [{
                "$eq": {
                    "name": "Brian Foster"
                }
            }]
        }

    def get_single_record_soap_parameters(self) -> dict:
        """
        Get SOAP single record parameters.
        :return: SOAP filters
        """
        return {
            'fields': self.SOAP_FIELDS,
            'field': 'CONTACT.CONTACTNAME',
            'value': 'Brian Foster'
        }
