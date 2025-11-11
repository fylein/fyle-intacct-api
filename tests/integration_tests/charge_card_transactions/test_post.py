import pytest
from tests.integration_tests.base.base_test_post import BaseTestPost
from tests.integration_tests.charge_card_transactions.fixtures import (
    REST_CHARGE_CARD_TRANSACTION_CREATE_PAYLOAD,
    SOAP_CHARGE_CARD_TRANSACTION_CREATE_PAYLOAD
)


@pytest.mark.integration
class TestChargeCardTransactionsPost(BaseTestPost):
    """
    Test charge card transactions POST operations.
    """
    REST_MODULE_NAME = 'charge_card_transactions'
    SOAP_MODULE_NAME = 'charge_card_transactions'
    REST_FIELDS = ['referenceNumber', 'description']
    SOAP_FIELDS = ['RECORDID', 'DESCRIPTION']
    REST_PAYLOAD = REST_CHARGE_CARD_TRANSACTION_CREATE_PAYLOAD
    SOAP_PAYLOAD = SOAP_CHARGE_CARD_TRANSACTION_CREATE_PAYLOAD
    KEY_MAPPINGS = [
        {
            'rest': 'referenceNumber',
            'soap': 'REFERENCENO'
        },
        {
            'rest': 'description',
            'soap': 'DESCRIPTION'
        }
    ]

    def get_soap_object_id(self, response: dict) -> str:
        """
        Get SOAP charge card transaction ID from POST response.
        :param response: SOAP POST response
        :return: Transaction ID
        """
        return response['key']

    def get_soap_get_parameters(self, object_id: str) -> dict:
        """
        Get SOAP GET parameters for charge card transaction.
        :param object_id: Transaction ID
        :return: SOAP GET parameters
        """
        return {
            'field': 'RECORDNO',
            'value': object_id
        }
