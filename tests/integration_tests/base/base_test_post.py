import logging
from typing import Any

from tests.integration_tests.base.rest_client import RestClient
from tests.integration_tests.base.soap_client import SoapClient

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class BaseTestPost:
    """
    Base class for all POST tests.
    """
    REST_FIELDS = []
    SOAP_FIELDS = []
    KEY_MAPPINGS = []
    SOAP_MODULE_NAME = None
    REST_MODULE_NAME = None
    REST_PAYLOAD = None
    SOAP_PAYLOAD = None

    def get_module(self, client: RestClient | SoapClient, module_name: str) -> Any:
        """
        Get the module.
        :param client: Client
        :param module_name: Module name
        :return: Module
        """
        return getattr(client.sdk, module_name)

    def test_post(self, rest_client: RestClient, soap_client: SoapClient) -> None:
        """
        Test create object via POST, verify with GET, and delete.
        :param rest_client: REST client
        :param soap_client: SOAP client
        :return: None
        """
        rest_module = self.get_module(rest_client, self.REST_MODULE_NAME)
        soap_module = self.get_module(soap_client, self.SOAP_MODULE_NAME)
        try:
            rest_response = rest_module.post(self.REST_PAYLOAD)
            soap_response = soap_module.post(self.SOAP_PAYLOAD)
        except Exception as e:
            print(f"Error in test_post: {e.response}")
            assert 1==2

        rest_object_id = self.get_rest_object_id(rest_response)
        soap_object_id = self.get_soap_object_id(soap_response)

        try:
            rest_get_response = self.get_rest_get_response(rest_module, rest_object_id)
            soap_get_response = self.get_soap_get_response(soap_module, soap_object_id)

            self.assert_post_response(rest_get_response, soap_get_response)

        finally:
            rest_module.delete(key=rest_object_id)
            rest_module.delete(key=soap_object_id)

    def get_rest_get_response(self, rest_module: RestClient, object_id: str) -> dict:
        """
        Get REST GET response.
        :param rest_module: REST module
        :param object_id: Object ID
        :return: REST GET response
        """
        return rest_module.get_all_generator(
            fields=self.REST_FIELDS,
            filters=[{
                "$eq": {
                    "key": object_id
                }
            }]
        )

    def get_soap_get_response(self, soap_module: SoapClient, object_id: str) -> dict:
        """
        Get SOAP GET response.
        :param soap_module: SOAP module
        :param object_id: Object ID
        :return: SOAP GET response
        """
        return soap_module.get_all_generator(
            fields=self.SOAP_FIELDS,
            **self.get_soap_get_parameters(object_id)
        )

    def assert_post_response(self, rest_response, soap_response) -> None:
        """
        Assert the POST response.
        :param rest_response: REST response
        :param soap_response: SOAP response
        :return: None
        """
        # Convert generators to lists first to avoid exhaustion
        rest_items = list[Any](rest_response)
        soap_items = list(soap_response)

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

    def get_rest_object_id(self, response: dict) -> str:
        """
        Get REST object ID from POST response.
        :param response: REST POST response
        :return: Object ID
        """
        return response['ia::result']['key']

    def get_soap_object_id(self, response: dict) -> str:
        """
        Get SOAP object ID from POST response.
        Override in child class if needed.
        :param response: SOAP POST response
        :return: Object ID
        """
        raise NotImplementedError("Child class must implement get_soap_object_id")

    def get_soap_get_parameters(self, object_id: str) -> dict:
        """
        Get SOAP GET parameters.
        Override in child class if needed.
        :param object_id: Object ID
        :return: SOAP GET parameters
        """
        raise NotImplementedError("Child class must implement get_soap_get_parameters")

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
