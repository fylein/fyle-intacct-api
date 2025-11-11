import pytest
from tests.integration_tests.base.base_test_post import BaseTestPost
from tests.integration_tests.expense_reports.fixtures import (
    REST_EXPENSE_REPORT_CREATE_PAYLOAD,
    SOAP_EXPENSE_REPORT_CREATE_PAYLOAD
)


@pytest.mark.integration
class TestExpenseReportsPost(BaseTestPost):
    """
    Test expense reports POST operations.
    """
    REST_MODULE_NAME = 'expense_reports'
    SOAP_MODULE_NAME = 'expense_reports'
    REST_FIELDS = ['employee.id', 'description']
    SOAP_FIELDS = ['EMPLOYEEID', 'DESCRIPTION']
    REST_PAYLOAD = REST_EXPENSE_REPORT_CREATE_PAYLOAD
    SOAP_PAYLOAD = SOAP_EXPENSE_REPORT_CREATE_PAYLOAD
    KEY_MAPPINGS = [
        {
            'rest': 'employee.id',
            'soap': 'EMPLOYEEID'
        },
        {
            'rest': 'description',
            'soap': 'DESCRIPTION'
        }
    ]

    def get_soap_object_id(self, response: dict) -> str:
        """
        Get SOAP expense report ID from POST response.
        :param response: SOAP POST response
        :return: Expense Report ID
        """
        return response['key']

    def get_soap_get_parameters(self, object_id: str) -> dict:
        """
        Get SOAP GET parameters for expense report.
        :param object_id: Expense Report ID
        :return: SOAP GET parameters
        """
        return {
            'field': 'RECORDNO',
            'value': object_id
        }
