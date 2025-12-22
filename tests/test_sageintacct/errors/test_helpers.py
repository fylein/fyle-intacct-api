from unittest import mock

from apps.sage_intacct.errors.helpers import (
    error_matcher,
    get_entity_values,
    remove_support_id,
    replace_destination_id_with_values,
    retry,
)
from .fixtures import (
    error_dict,
    error_msgs,
    replacements,
    input_strings,
    result_dict_list,
    entity_result_dict_list
)


def test_remove_support_id():
    """
    Test remove_support_id function
    """
    assert remove_support_id("The employee '1005' is invalid. [Support ID: 123456]") == "The employee '1005' is invalid."
    assert remove_support_id("The account number '16200' requires a [Support ID: 123456]") == "The account number '16200' requires a"


def test_error_matcher():
    """
    Test error_matcher function
    """
    for index in range(len(error_msgs)):
        assert error_matcher(error_msgs[index]) == result_dict_list[index]


def test_get_entity_values(db):
    """
    Test get_entity_values function
    """
    for index in range(len(error_dict)):
        assert get_entity_values(error_dict[index], 1) == entity_result_dict_list[index]


def test_replace_destination_id_with_values():
    """
    Test replace_destination_id_with_values function
    """
    for index in range(len(input_strings)):
        assert replace_destination_id_with_values(input_strings[index], replacements[index]) == input_strings[index].replace(replacements[index]['destination_id'], f"{replacements[index]['destination_id']} => {replacements[index]['value']}")


def test_retry_decorator_success():
    """
    Test retry decorator with successful function execution
    """
    call_count = 0

    @retry(max_retry=3, backoff=0)
    def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"

    result = successful_function()
    assert result == "success"
    assert call_count == 1


def test_retry_decorator_retry_then_success():
    """
    Test retry decorator when function fails then succeeds
    """
    call_count = 0

    @retry(max_retry=3, backoff=0)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Connection failed")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert call_count == 3


def test_retry_decorator_max_retries_exceeded():
    """
    Test retry decorator when max retries are exceeded
    """
    call_count = 0

    @retry(max_retry=3, backoff=0)
    def always_failing_function():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Connection failed")

    try:
        always_failing_function()
        assert False, "Expected exception to be raised"
    except ConnectionError as e:
        assert str(e) == "Connection failed"
        assert call_count == 3


def test_retry_decorator_preserves_function_metadata():
    """
    Test retry decorator preserves function name and docstring
    """
    @retry(max_retry=3, backoff=0)
    def documented_function():
        """This is a docstring."""
        return "result"

    assert documented_function.__name__ == "documented_function"
    assert documented_function.__doc__ == "This is a docstring."


def test_retry_decorator_with_arguments():
    """
    Test retry decorator with function arguments
    """
    call_count = 0

    @retry(max_retry=3, backoff=0)
    def function_with_args(a, b, c=None):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Error")
        return f"{a}-{b}-{c}"

    result = function_with_args("x", "y", c="z")
    assert result == "x-y-z"
    assert call_count == 2


def test_retry_decorator_default_parameters():
    """
    Test retry decorator with default parameters
    """
    call_count = 0

    @retry()
    def default_retry_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Error")
        return "success"

    with mock.patch('time.sleep'):
        result = default_retry_function()

    assert result == "success"
    assert call_count == 2
