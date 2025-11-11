import pytest
from tests.integration_tests.base.base_test_get import BaseTestGet


@pytest.mark.integration
class TestExpensePaymentTypesGet(BaseTestGet):
    """
    Test expense payment types GET operations.
    """
    REST_MODULE_NAME = 'expense_payment_types'
    SOAP_MODULE_NAME = 'expense_payment_types'
    ALLOWED_METHODS = ['get_all_generator', 'get_count']
    REST_FIELDS = ['key', 'id', 'isNonReimbursable']
    SOAP_FIELDS = ['RECORDNO', 'NAME', 'NONREIMBURSABLE']
    KEY_MAPPINGS = [
        {
            'rest': 'key',
            'soap': 'RECORDNO'
        },
        {
            'rest': 'id',
            'soap': 'NAME'
        },
        {
            'rest': 'isNonReimbursable',
            'soap': 'NONREIMBURSABLE'
        }
    ]

    def get_all_generator_rest_parameters(self) -> dict:
        """
        Get REST all generator parameters.
        :return: REST filters
        """
        return {
            'fields': self.REST_FIELDS
        }

    def get_all_generator_soap_parameters(self) -> dict:
        """
        Get SOAP all generator parameters.
        :return: SOAP filters
        """
        return {
            'fields': self.SOAP_FIELDS
        }
