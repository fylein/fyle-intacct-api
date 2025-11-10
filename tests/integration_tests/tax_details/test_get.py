# import pytest
# from tests.integration_tests.base.base_test_get import BaseTestGet


# @pytest.mark.integration
# class TestTaxDetailsGet(BaseTestGet):
#     """
#     Test tax details GET operations.
#     """
#     REST_MODULE_NAME = 'tax_details'
#     SOAP_MODULE_NAME = 'tax_details'
#     ALLOWED_METHODS = ['get_all_generator', 'get_count']
#     REST_FIELDS = ['id', 'taxPercent', 'description', 'taxSolution.id', 'status', 'taxType']
#     SOAP_FIELDS = ['DETAILID', 'VALUE', 'TAXSOLUTIONID', 'STATUS', 'TAXTYPE']
#     KEY_MAPPINGS = [
#         {
#             'rest': 'description',
#             'soap': 'DETAILID'
#         },
#         {
#             'rest': 'taxPercent',
#             'soap': 'VALUE'
#         },
#         {
#             'rest': 'taxSolution.id',
#             'soap': 'TAXSOLUTIONID'
#         },
#         {
#             'rest': 'status',
#             'soap': 'STATUS'
#         },
#         {
#             'rest': 'taxType',
#             'soap': 'TAXTYPE'
#         }
#     ]

#     def get_all_generator_rest_parameters(self) -> dict:
#         """
#         Get REST all generator parameters.
#         :return: REST filters
#         """
#         return {
#             'fields': self.REST_FIELDS,
#             'filters': [{
#                 "$eq": {
#                     "status": "active"
#                 }
#             }]
#         }

#     def get_all_generator_soap_parameters(self) -> dict:
#         """
#         Get SOAP all generator parameters.
#         :return: SOAP filters
#         """
#         return {
#             'fields': self.SOAP_FIELDS,
#             'field': 'STATUS',
#             'value': 'active',
#         }
