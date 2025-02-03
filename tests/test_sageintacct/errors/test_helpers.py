from apps.sage_intacct.errors.helpers import error_matcher, get_entity_values, replace_destination_id_with_values, remove_support_id
from .fixtures import error_dict, result_dict_list, input_strings, replacements, error_msgs, entity_result_dict_list


def test_remove_support_id():
    assert remove_support_id("The employee '1005' is invalid. [Support ID: 123456]") == "The employee '1005' is invalid."
    assert remove_support_id("The account number '16200' requires a [Support ID: 123456]") == "The account number '16200' requires a"


def test_error_matcher():
    for index in range(len(error_msgs)):
        assert error_matcher(error_msgs[index]) == result_dict_list[index]
       

def test_get_entity_values(db):
    for index in range(len(error_dict)):
        assert get_entity_values(error_dict[index], 1) == entity_result_dict_list[index]


def test_replace_destination_id_with_values():
    for index in range(len(input_strings)):
        assert replace_destination_id_with_values(input_strings[index], replacements[index]) == input_strings[index].replace(replacements[index]['destination_id'], f"{replacements[index]['destination_id']} => {replacements[index]['value']}")
