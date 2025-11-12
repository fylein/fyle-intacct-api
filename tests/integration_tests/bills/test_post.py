import pytest
from tests.integration_tests.base.base_test_post import BaseTestPost
from tests.integration_tests.bills.fixtures import (
    REST_BILL_CREATE_PAYLOAD,
    SOAP_BILL_CREATE_PAYLOAD,
    REST_BILL_CREATE_PAYLOAD_WITH_ALLOCATION,
    SOAP_BILL_CREATE_PAYLOAD_WITH_ALLOCATION
)


@pytest.mark.integration
class TestBillsPost(BaseTestPost):
    """
    Test bills POST operations.
    """
    REST_MODULE_NAME = 'bills'
    SOAP_MODULE_NAME = 'bills'
    REST_FIELDS = ['referenceNumber', 'description']
    SOAP_FIELDS = ['RECORDID', 'DESCRIPTION']
    REST_PAYLOAD = REST_BILL_CREATE_PAYLOAD
    SOAP_PAYLOAD = SOAP_BILL_CREATE_PAYLOAD
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
        Get SOAP bill ID from POST response.
        :param response: SOAP POST response
        :return: Bill ID
        """
        return response['data']['apbill']['RECORDNO']

    def get_soap_get_parameters(self, object_id: str) -> dict:
        """
        Get SOAP GET parameters for bill.
        :param object_id: Bill ID
        :return: SOAP GET parameters
        """
        return {
            'field': 'RECORDNO',
            'value': object_id
        }



@pytest.mark.integration
class TestBillsPostWithAllocation(BaseTestPost):
    """
    Test bills POST operations.
    """
    REST_MODULE_NAME = 'bills'
    SOAP_MODULE_NAME = 'bills'
    REST_FIELDS = ['referenceNumber', 'description']
    SOAP_FIELDS = ['RECORDID', 'DESCRIPTION']
    REST_PAYLOAD = REST_BILL_CREATE_PAYLOAD_WITH_ALLOCATION
    SOAP_PAYLOAD = SOAP_BILL_CREATE_PAYLOAD_WITH_ALLOCATION
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
        Get SOAP bill ID from POST response.
        :param response: SOAP POST response
        :return: Bill ID
        """
        return response['data']['apbill']['RECORDNO']

    def get_soap_get_parameters(self, object_id: str) -> dict:
        """
        Get SOAP GET parameters for bill.
        :param object_id: Bill ID
        :return: SOAP GET parameters
        """
        return {
            'field': 'RECORDNO',
            'value': object_id
        }
