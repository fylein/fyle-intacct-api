from time import sleep
import pytest
from tests.integration_tests.base.base_test_post import BaseTestPost
from tests.integration_tests.base.rest_client import RestClient
from tests.integration_tests.base.soap_client import SoapClient
from tests.integration_tests.charge_card_transactions.fixtures import (
    REST_CHARGE_CARD_TRANSACTION_CREATE_PAYLOAD,
    SOAP_CHARGE_CARD_TRANSACTION_CREATE_PAYLOAD
)


@pytest.mark.integration
class TestChargeCardTransactionsPatch(BaseTestPost):
    """
    Test charge card transactions PATCH operations.
    """
    REST_MODULE_NAME = 'charge_card_transactions'
    SOAP_MODULE_NAME = 'charge_card_transactions'
    REST_FIELDS = ['referenceNumber', 'description', 'attachment.id']
    SOAP_FIELDS = ['RECORDID', 'DESCRIPTION', 'SUPDOCID']
    ATTACHMENT_ID = 'Random 1234'
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
        },
        {
            'rest': 'attachment.id',
            'soap': 'SUPDOCID'
        }
    ]

    def test_post(self, rest_client: RestClient, soap_client: SoapClient) -> None:
        """
        Test create object via POST, verify with GET, and delete.
        :param rest_client: REST client
        :param soap_client: SOAP client
        :return: None
        """
        pytest.skip("Skipping test_post for charge card transactions attachment creation")

    def test_patch(self, rest_client: RestClient, soap_client: SoapClient) -> None:
        """
        Test update object via PATCH, verify with GET, and delete.
        :param rest_client: REST client
        :param soap_client: SOAP client
        :return: None
        """
        rest_module = self.get_module(rest_client, self.REST_MODULE_NAME)
        soap_module = self.get_module(soap_client, self.SOAP_MODULE_NAME)

        rest_response = rest_module.post(self.REST_PAYLOAD)
        soap_response = soap_module.post(self.SOAP_PAYLOAD)

        rest_object_id = self.get_rest_object_id(rest_response)
        soap_object_id = self.get_soap_object_id(soap_response)

        try:
            rest_get_response = self.get_rest_get_response(rest_module, rest_object_id)
            soap_get_response = self.get_soap_get_response(soap_module, soap_object_id)

            self.assert_post_response(rest_get_response, soap_get_response)

            rest_module.update_attachment(object_id=rest_object_id, attachment_id=self.ATTACHMENT_ID)
            soap_module.update_attachment(key=soap_object_id, supdocid=self.ATTACHMENT_ID)

            rest_get_response = self.get_rest_get_response(rest_module, rest_object_id)
            soap_get_response = self.get_soap_get_response(soap_module, soap_object_id)
            self.assert_post_response(rest_get_response, soap_get_response)


        finally:
            rest_module.delete(key=rest_object_id)
            rest_module.delete(key=soap_object_id)

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

    def get_rest_attachment_id(self, response: dict) -> str:
        """
        Get REST attachment ID from POST response.
        :param response: REST POST response
        :return: Attachment ID
        """
        return response['ia::result']['id']

    def get_rest_attachment_key(self, response: dict) -> str:
        """
        Get REST attachment key from POST response.
        :param response: REST POST response
        :return: Attachment key
        """
        return response['ia::result']['key']