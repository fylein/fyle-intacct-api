import re
import time
import logging
from functools import wraps

from apps.sage_intacct.errors.errors import errors_ref

from fyle_accounting_mappings.models import DestinationAttribute

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def remove_support_id(message: str) -> str:
    """
    Remove the Support ID from the given message
    :param message: Original message containing the Support ID
    :return: Message with the Support ID removed
    """
    # Define the pattern for matching the Support ID
    pattern = r' \[Support ID: [^\]]+\]'

    # Use re.sub to replace the matched pattern with an empty string
    cleaned_message = re.sub(pattern, '', message)

    return cleaned_message


def error_matcher(error_msg: str) -> dict:
    """
    Match the given error message with predefined errors in the reference dictionary
    :param error_msg: Error message to be matched
    :return: Dictionary with 'attribute_type', 'destination_id' and 'article_link' if found, otherwise None
    """
    # Loop through each predefined error in the reference dictionary
    for attribute_type, error in errors_ref.items():
        # Check each pattern associated with the current error
        for pattern in error['patterns']:
            # Use regular expression to search for a match in the given error message
            match = re.search(pattern, error_msg)

            # If a match is found
            if match:
                # Create a dictionary to store information about the error
                error_dict = {
                    'attribute_type': attribute_type,
                    'destination_id': match.groups()[0],  # Extract specific information from the match
                    'article_link': error['article_link']
                }

                # Return the error dictionary
                return error_dict

    # If no match is found, return None
    return None


def get_entity_values(error_dict: dict, workspace_id: int) -> dict:
    """
    Get entity values from error dictionary
    :param error_dict: Error Dictionary containing information about the error
    :param workspace_id: ID of the workspace
    :return: Dictionary with 'destination_id' and 'value' if found, otherwise an empty dictionary
    """
    # Fetch the destination attribute based on destination ID and attribute type
    destination_attribute = DestinationAttribute.objects.filter(
        destination_id=error_dict['destination_id'],
        attribute_type=error_dict['attribute_type'].upper(),
        workspace_id=workspace_id
    ).first()

    # If the destination attribute is found, return a dictionary with 'destination_id' and 'value'
    if destination_attribute:
        return {
            'destination_id': error_dict['destination_id'],
            'value': destination_attribute.value
        }

    # If no match is found or destination attribute is not active, return an empty dictionary
    return {}


def replace_destination_id_with_values(input_string: str, replacement: str) -> str:
    """
    Replace destination ID with corresponding values in the input string
    :param input_string: Original string containing destination ID placeholders
    :param replacement: Dictionary with 'destination_id' and 'value' to replace in the string
    :return: String with destination ID replaced by formatted 'destination_id => value'
    """
    # Extract destination ID and value from the replacement dictionary
    destination_id = replacement['destination_id']
    value = replacement['value']

    # Create a formatted string in the form of 'destination_id => value'
    arrowed_string = f"{destination_id} => {value}"

    # Replace occurrences of destination ID in the input string with the formatted string
    input_string = input_string.replace(destination_id, arrowed_string)

    # Return the modified input string
    return input_string


def retry(max_retry: int = 3, backoff: int = 2) -> callable:
    """
    Retry Decorator
    :param max_retry: Number of retries (default: 3)
    :param backoff: Backoff time (default: 2)
    :return: Decorator
    """
    def decorator(func: callable) -> callable:
        @wraps(func)
        def new_fn(*args, **kwargs) -> object:  # pylint: disable=missing-return-type
            last_exception = None
            for _ in range(max_retry):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.exception('Error while executing function %s: %s', func.__name__, str(e))
                    time.sleep(backoff)
            logger.exception('Failed to execute function %s despite retrying: %s', func.__name__, last_exception)
            raise last_exception
        return new_fn
    return decorator
