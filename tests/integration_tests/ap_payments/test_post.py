# import pytest
# from tests.integration_tests.base.base_test_post import BaseTestPost
# from tests.integration_tests.ap_payments.fixtures import (
#     get_rest_ap_payment_create_payload,
#     get_soap_ap_payment_create_payload
# )
# from tests.integration_tests.base.rest_client import RestClient
# from tests.integration_tests.base.soap_client import SoapClient
# from tests.integration_tests.bills.fixtures import (
#     REST_BILL_CREATE_PAYLOAD,
#     SOAP_BILL_CREATE_PAYLOAD
# )

# @pytest.mark.integration
# class TestAPPaymentsPost(BaseTestPost):
#     """
#     Test AP Payments POST operations.
#     """
#     REST_MODULE_NAME = 'ap_payments'
#     SOAP_MODULE_NAME = 'ap_payments'
#     REST_FIELDS = ['referenceNumber', 'description']
#     SOAP_FIELDS = ['RECORDID', 'DESCRIPTION']
#     KEY_MAPPINGS = [
#         {
#             'rest': 'referenceNumber',
#             'soap': 'REFERENCENO'
#         },
#         {
#             'rest': 'description',
#             'soap': 'DESCRIPTION'
#         }
#     ]

#     def test_post(self, rest_client: RestClient, soap_client: SoapClient) -> None:
#         """
#         Test create object via POST, verify with GET, and delete.
#         :param rest_client: REST client
#         :param soap_client: SOAP client
#         :return: None
#         """
#         bill_rest_module = self.get_module(rest_client, 'bills')
#         bill_soap_module = self.get_module(soap_client, 'bills')

#         ap_payments_rest_module = self.get_module(rest_client, self.REST_MODULE_NAME)
#         ap_payments_soap_module = self.get_module(soap_client, self.SOAP_MODULE_NAME)


#         bill_rest_response = bill_rest_module.post(REST_BILL_CREATE_PAYLOAD)
#         bill_soap_response = bill_soap_module.post(SOAP_BILL_CREATE_PAYLOAD)

#         bill_rest_object_id = self.get_rest_object_id(bill_rest_response)
#         bill_soap_object_id = self.get_soap_object_id(bill_soap_response)

#         rest_ap_payment_object_id = None
#         soap_ap_payment_object_id = None

#         try:
#             bill_rest_get_response = self.get_rest_get_response(bill_rest_module, bill_rest_object_id)
#             bill_soap_get_response = self.get_soap_get_response(bill_soap_module, bill_soap_object_id)

#             self.assert_post_response(bill_rest_get_response, bill_soap_get_response)

#             rest_ap_payment_create_payload = get_rest_ap_payment_create_payload(bill_rest_object_id)
#             soap_ap_payment_create_payload = get_soap_ap_payment_create_payload(bill_soap_object_id)

#             rest_ap_payment_response = ap_payments_rest_module.post(rest_ap_payment_create_payload)
#             soap_ap_payment_response = ap_payments_soap_module.post(soap_ap_payment_create_payload)

#             rest_ap_payment_object_id = self.get_ap_payments_rest_object_id(rest_ap_payment_response)
#             soap_ap_payment_object_id = self.get_ap_payments_soap_object_id(soap_ap_payment_response)

#         finally:
#             ap_payments_rest_module.delete(key=rest_ap_payment_object_id)
#             ap_payments_rest_module.delete(key=soap_ap_payment_object_id)

#             bill_rest_module.delete(key=bill_rest_object_id)
#             bill_soap_module.delete(key=bill_soap_object_id)


#     def get_soap_object_id(self, response: dict) -> str:
#         """
#         Get SOAP bill ID from POST response.
#         :param response: SOAP POST response
#         :return: Bill ID
#         """
#         return response['data']['apbill']['RECORDNO']

#     def get_soap_get_parameters(self, object_id: str) -> dict:
#         """
#         Get SOAP GET parameters for bill.
#         :param object_id: Bill ID
#         :return: SOAP GET parameters
#         """
#         return {
#             'field': 'RECORDNO',
#             'value': object_id
#         }

#     def get_ap_payments_rest_object_id(self, response: dict) -> str:
#         """
#         Get REST AP Payment ID from POST response.
#         :param response: REST POST response
#         :return: AP Payment ID
#         """
#         return response['ia::result']['key']

#     def get_ap_payments_soap_object_id(self, response: dict) -> str:
#         """
#         Get SOAP AP Payment ID from POST response.
#         :param response: SOAP POST response
#         :return: AP Payment ID
#         """
#         return response['data']['appayment']['RECORDNO']