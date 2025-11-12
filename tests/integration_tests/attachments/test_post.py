import pytest
from tests.integration_tests.base.base_test_post import BaseTestPost
from tests.integration_tests.attachments.fixtures import (
    REST_ATTACHMENT_CREATE_PAYLOAD,
    SOAP_ATTACHMENT_CREATE_PAYLOAD
)
from tests.integration_tests.base.soap_client import SoapClient


@pytest.mark.integration
class TestAttachmentsPost(BaseTestPost):
    """
    Test attachments POST operations.
    """
    REST_MODULE_NAME = 'attachments'
    SOAP_MODULE_NAME = 'attachments'
    REST_FIELDS = ['id']
    SOAP_FIELDS = ['supdoc.supdocid']
    REST_PAYLOAD = REST_ATTACHMENT_CREATE_PAYLOAD
    SOAP_PAYLOAD = SOAP_ATTACHMENT_CREATE_PAYLOAD

    def get_soap_object_id(self, response: dict) -> str:
        """
        Get SOAP attachment ID from POST response.
        :param response: SOAP POST response
        :return: Attachment ID
        """
        return response['key']

    def get_soap_get_parameters(self, object_id: str) -> dict:
        """
        Get SOAP GET parameters for attachment.
        :param object_id: Attachment ID
        :return: SOAP GET parameters
        """
        return {
            'field': 'recordno',
            'value': object_id
        }

    def get_soap_get_response(self, soap_module: SoapClient, object_id: str) -> dict:
        """
        Get SOAP GET response.
        :param soap_module: SOAP module
        :param object_id: Object ID
        :return: SOAP GET response
        """
        return [soap_module.get_attachment(
            **self.get_soap_get_parameters(object_id)
        )['data']]
