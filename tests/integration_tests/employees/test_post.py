import pytest
from tests.integration_tests.base.base_test_post import BaseTestPost
from tests.integration_tests.employees.fixtures import (
    REST_CONTACT_CREATE_PAYLOAD,
    SOAP_CONTACT_CREATE_PAYLOAD,
    REST_EMPLOYEE_CREATE_PAYLOAD,
    SOAP_EMPLOYEE_CREATE_PAYLOAD
)


@pytest.mark.integration
class TestEmployeesPost(BaseTestPost):
    """
    Test employees POST operations.
    """
    REST_MODULE_NAME = 'employees'
    SOAP_MODULE_NAME = 'employees'
    REST_FIELDS = ['id', 'name', 'status', 'primaryContact.email1', 'primaryContact.printAs']
    SOAP_FIELDS = ['EMPLOYEEID', 'CONTACT.CONTACTNAME', 'STATUS', 'CONTACT.EMAIL1', 'CONTACT.PRINTAS']
    REST_PAYLOAD = REST_EMPLOYEE_CREATE_PAYLOAD
    SOAP_PAYLOAD = SOAP_EMPLOYEE_CREATE_PAYLOAD
    KEY_MAPPINGS = [
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
        }
    ]

    def test_post(self, rest_client, soap_client) -> None:
        """
        Test create employee via POST, verify with GET, and delete.
        First creates contact, then creates employee.
        :param rest_client: REST client
        :param soap_client: SOAP client
        :return: None
        """
        rest_module = self.get_module(rest_client, self.REST_MODULE_NAME)
        soap_module = self.get_module(soap_client, self.SOAP_MODULE_NAME)
        rest_contacts = self.get_module(rest_client, 'contacts')
        soap_contacts = self.get_module(soap_client, 'contacts')

        # Create contacts first
        rest_contact_response = rest_contacts.post(REST_CONTACT_CREATE_PAYLOAD)
        soap_contact_response = soap_contacts.post(SOAP_CONTACT_CREATE_PAYLOAD)

        rest_contact_key = rest_contact_response['ia::result']['key']
        soap_contact_key = soap_contact_response['data']['contact']['RECORDNO']

        try:
            # Create employees
            rest_response = rest_module.post(self.REST_PAYLOAD)
            soap_response = soap_module.post(self.SOAP_PAYLOAD)

            rest_object_id = self.get_rest_object_id(rest_response)
            soap_object_id = self.get_soap_object_id(soap_response)

            try:
                rest_get_response = self.get_rest_get_response(rest_module, rest_object_id)
                soap_get_response = self.get_soap_get_response(soap_module, soap_object_id)

                self.assert_post_response(rest_get_response, soap_get_response)

            finally:
                # Delete employees
                rest_module.delete(key=rest_object_id)
                soap_module.delete(key=soap_object_id)

        finally:
            # Delete contacts
            rest_contacts.delete(key=rest_contact_key)
            soap_contacts.delete(key=soap_contact_key)

    def get_soap_object_id(self, response: dict) -> str:
        """
        Get SOAP employee ID from POST response.
        :param response: SOAP POST response
        :return: Employee ID
        """
        return response['data']['employee']['RECORDNO']

    def get_soap_get_parameters(self, object_id: str) -> dict:
        """
        Get SOAP GET parameters for employee.
        :param object_id: Employee ID
        :return: SOAP GET parameters
        """
        return {
            'field': 'RECORDNO',
            'value': object_id
        }
