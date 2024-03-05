import re
from .errors import errors_ref
from fyle_accounting_mappings.models import DestinationAttribute


def remove_support_id(message):
    # Define the pattern for matching the Support ID
    pattern = r' \[Support ID: [^\]]+\]'

    # Use re.sub to replace the matched pattern with an empty string
    cleaned_message = re.sub(pattern, '', message)

    return cleaned_message


def error_matcher(error_msg):
    for attribute_type, error in errors_ref.items():
        for pattern in error['patterns']:
            match = re.search(pattern, error_msg)
            if match:
                error_dict = {
                    'attribute_type': attribute_type,
                    'destination_id': match.groups()[0],
                    'article_link': error['article_link']
                }
                return error_dict
    return None

    
def get_entity_values(error_dict, workspace_id):
    """
    Get entity values from error dictionary
    :param error_dict: Error Dictionary
    :return: List of Entity Values
    """

    distinct_destination_attributes = DestinationAttribute.objects.filter(workspace_id=workspace_id).distinct('attribute_type').values_list('attribute_type', flat=True)

    if error_dict['attribute_type'].upper() in distinct_destination_attributes:
        destination_attribute = DestinationAttribute.objects.filter(
            destination_id=error_dict['destination_id'], attribute_type=error_dict['attribute_type'].upper()
        ).first()

        if destination_attribute:
            return {
                'destination_id': error_dict['destination_id'],
                'value': destination_attribute.value
            }
    return {}


def replace_destination_id_with_values(input_string, replacement):
    destination_id = replacement['destination_id']
    value = replacement['value']
    arrowed_string = f"{destination_id} => {value}"
    input_string = input_string.replace(destination_id, arrowed_string)
    return input_string
