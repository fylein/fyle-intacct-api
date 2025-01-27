from tests.test_sageintacct.fixtures import data
from apps.internal.actions import get_accounting_fields, get_exported_entry


def test_get_accounting_fields(db, mocker):
    """
    Test get_accounting_fields function
    """
    query_params = {
        'org_id': 'or79Cob97KSh',
        'resource_type': 'employees',
    }
    mocker.patch(
        'sageintacctsdk.apis.Employees.get_all_generator',
        return_value=data['get_employees']
    )

    fields = get_accounting_fields(query_params)
    assert fields is not None


def test_get_exported_entry(db, mocker):
    """
    Test get_exported_entry function
    """
    query_params = {
        'org_id': 'or79Cob97KSh',
        'resource_type': 'bill',
        'internal_id': '1'
    }
    mocker.patch(
        'sageintacctsdk.apis.Bills.get',
        return_value={'summa': 'hehe'}
    )

    entry = get_exported_entry(query_params)
    assert entry is not None
