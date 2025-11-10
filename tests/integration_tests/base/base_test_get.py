from datetime import datetime
import logging
from typing import Any, Generator

import pytest

from tests.integration_tests.base.rest_client import RestClient
from tests.integration_tests.base.soap_client import SoapClient

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class BaseTestGet:
    """
    Base class for all GET tests.
    """
    REST_FIELDS = []
    SOAP_FIELDS = []
    KEY_MAPPINGS = []
    ALLOWED_METHODS = []
    SOAP_MODULE_NAME = None
    REST_MODULE_NAME = None
    LAST_UPDATED_AT = '2022-01-01T00:00:00Z'

    def get_module(self, client: RestClient | SoapClient, module_name: str) -> Any:
        """
        Get the module.
        :param client: Client
        :param module_name: Module name
        :return: Module
        """
        return getattr(client.sdk, module_name)

    def test_get_all_generator(self, rest_client: RestClient, soap_client: SoapClient) -> None:
        """
        Test get all generator method.
        :param rest_client: REST client
        :param soap_client: SOAP client
        :return: None
        """
        if 'get_all_generator' not in self.ALLOWED_METHODS:
            pytest.skip(f"Method 'get_all_generator' not allowed for {self.REST_MODULE_NAME}")

        rest_parameters = self.get_all_generator_rest_parameters()
        soap_parameters = self.get_all_generator_soap_parameters()

        rest_module = self.get_module(rest_client, self.REST_MODULE_NAME)
        soap_module = self.get_module(soap_client, self.SOAP_MODULE_NAME)

        rest_response = rest_module.get_all_generator(**rest_parameters)
        soap_response = soap_module.get_all_generator(**soap_parameters)

        self.assert_get_all_generator_response(rest_response, soap_response)

    def test_get_single_record(self, rest_client: RestClient, soap_client: SoapClient) -> None:
        """
        Test get single record method.
        :param rest_client: REST client
        :param soap_client: SOAP client
        :return: None
        """
        if 'get_single_record' not in self.ALLOWED_METHODS:
            pytest.skip(f"Method 'get_single_record' not allowed for {self.REST_MODULE_NAME}")

        rest_parameters = self.get_single_record_rest_parameters()
        soap_parameters = self.get_single_record_soap_parameters()

        rest_module = self.get_module(rest_client, self.REST_MODULE_NAME)
        soap_module = self.get_module(soap_client, self.SOAP_MODULE_NAME)

        rest_response = rest_module.get_all_generator(**rest_parameters)
        soap_response = soap_module.get_all_generator(**soap_parameters)

        self.assert_get_single_record_response(rest_response, soap_response)

    def test_get_count(self, rest_client: RestClient, soap_client: SoapClient) -> None:
        """
        Test get count method.
        :param rest_client: REST client
        :param soap_client: SOAP client
        :return: None
        """
        if 'get_count' not in self.ALLOWED_METHODS:
            pytest.skip(f"Method 'get_count' not allowed for {self.REST_MODULE_NAME}")

        rest_module = self.get_module(rest_client, self.REST_MODULE_NAME)
        soap_module = self.get_module(soap_client, self.SOAP_MODULE_NAME)

        rest_parameters = self.get_count_rest_parameters()
        soap_parameters = self.get_count_soap_parameters()

        rest_response = rest_module.count(**rest_parameters)
        soap_response = soap_module.count(**soap_parameters)

        assert rest_response == soap_response, f"Count mismatch: {rest_response} != {soap_response}"

    def assert_get_all_generator_response(self, rest_response: Generator[dict, None, None], soap_response: Generator[dict, None, None]) -> None:
        """
        Assert the GET generator response.
        :param rest_response: REST response
        :param soap_response: SOAP response
        :return: None
        """
        rest_items = list[dict](rest_response)
        soap_items = list[dict](soap_response)

        assert len(rest_items[0]) == len(soap_items[0]), f"Length of REST and SOAP items do not match: {len(rest_items[0])} != {len(soap_items[0])}"
        assert len(rest_items[0]) > 0, f"REST item is empty: {rest_items[0]}"

        for rest_item in rest_items:
            matched = False

            for soap_item in soap_items:
                all_fields_match = True

                for key_mapping in self.KEY_MAPPINGS:
                    rest_value = self.get_nested_value(rest_item, key_mapping['rest'])
                    soap_value = self.get_nested_value(soap_item, key_mapping['soap'])

                    if rest_value != soap_value:
                        all_fields_match = False
                        break

                if all_fields_match:
                    matched = True
                    break

            assert matched, f"No SOAP match found for REST item: {rest_item}"

    def assert_get_single_record_response(self, rest_response: dict, soap_response: dict) -> None:
        """
        Assert the GET single record response.
        :param rest_response: REST response
        :param soap_response: SOAP response
        :return: None
        """
        all_fields_match = True

        rest_items = list[dict](rest_response)
        soap_items = list[dict](soap_response)

        assert len(rest_items[0]) == len(soap_items[0]), f"Length of REST and SOAP items do not match: {len(rest_items[0])} != {len(soap_items[0])}"
        assert len(rest_items[0]) == 1, f"REST item is empty: {rest_items[0]}"

        for key_mapping in self.KEY_MAPPINGS:
            rest_value = self.get_nested_value(rest_items[0], key_mapping['rest'])
            soap_value = self.get_nested_value(soap_items[0], key_mapping['soap'])

            if rest_value != soap_value:
                all_fields_match = False
                break

        assert all_fields_match, f"No SOAP match found for REST item: {rest_items[0]}"

    def get_all_generator_rest_parameters(self) -> dict:
        """
        Get REST all generator parameters.
        :return: REST filters
        """
        return {
            'fields': self.REST_FIELDS,
            'filters': [{
                "$eq": {
                    "status": "active"
                }
            },{
                "$gte": {
                    "audit.modifiedDateTime": self.LAST_UPDATED_AT
                }
            }]
        }

    def get_all_generator_soap_parameters(self) -> dict:
        """
        Get SOAP all generator parameters.
        :return: SOAP filters
        """
        return {
            'fields': self.SOAP_FIELDS,
            'field': 'STATUS',
            'value': 'active',
            'updated_at': datetime.strptime(self.LAST_UPDATED_AT, '%Y-%m-%dT%H:%M:%S%z').strftime('%m/%d/%Y')
        }

    def get_count_rest_parameters(self) -> dict:
        """
        Get REST count parameters.
        :return: REST filters
        """
        return {
            'filters': [{
                "$eq": {
                    "status": "active"
                }
            }]
        }

    def get_count_soap_parameters(self) -> dict:
        """
        Get SOAP count parameters.
        :return: SOAP filters
        """
        return {
            'field': 'STATUS',
            'value': 'active'
        }

    def get_nested_value(self, obj: dict | list, key_path: str) -> Any:
        """
        Safely get nested dict or list value using dot notation.
        :param obj: Dictionary or list
        :param key_path: Key path
        :return: Value
        """
        keys = key_path.split('.')
        for key in keys:
            if obj is None:
                return None

            # Handle dict
            if isinstance(obj, dict):
                obj = obj.get(key)

            # Handle list (numeric indexes)
            elif isinstance(obj, list):
                try:
                    index = int(key)
                    obj = obj[index]
                except (ValueError, IndexError):
                    # key isn't an integer index or index is out of range
                    return None
            else:
                return None

        return obj
