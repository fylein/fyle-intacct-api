from fyle_accounting_mappings.models import DestinationAttribute
import re


def get_entity_values(values_list, workspace_id):
    """
    Get entity values from error dictionary
    :param error_dict: Error Dictionary
    :return: List of Entity Values
    """
    entity_values = []

    distinct_destination_attributes = DestinationAttribute.objects.filter(workspace_id=workspace_id).distinct('attribute_type').values_list('attribute_type', flat=True)

    for value in values_list:
        if value['attribute_type'].upper() in distinct_destination_attributes:
            destination_attribute = DestinationAttribute.objects.filter(
                destination_id=value['destination_id'], attribute_type=value['attribute_type'].upper(), active=True
            ).first()

            if destination_attribute:
                entity_values.append({'destination_id': value['destination_id'], 'value': destination_attribute.value})
    return entity_values


def extract_destination_ids_from_error(error_msg):
    """
    Extract destination ids from error dictionary
    :param error_dict: Error Dictionary
    :return: List of Destination Ids
    """
    pattern = r"(\w+)\s*'([^']*)'"

    matches = re.findall(pattern, error_msg)

    result_list = []

    for match in matches:
        result_dict = {
            "attribute_type": match[0],
            "destination_id": match[1]
        }
        # this is a hack to handle this type of error => ' The account number '16200' requires a Class '
        if result_dict['attribute_type'] == 'number': result_dict['attribute_type'] = 'account'
        result_list.append(result_dict)
    return result_list

def replace_destination_id_with_values(input_string, replacements):
    for replacement in replacements:
        destination_id = replacement['destination_id']
        value = replacement['value']
        arrowed_string = f"{destination_id} => {value}"
        input_string = input_string.replace(destination_id, arrowed_string)
    return input_string