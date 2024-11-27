import pytest
from unittest.mock import patch
from django.urls import reverse

from apps.workspaces.permissions import IsAuthenticatedForInternalAPI

from tests.test_sageintacct.fixtures import data


@pytest.mark.django_db(databases=['default'])
@patch.object(IsAuthenticatedForInternalAPI, 'has_permission', return_value=True)
def test_qbo_fields_view(db, api_client, mocker):
    url = reverse('accounting-fields')

    response = api_client.get(url)
    assert response.status_code == 400

    response = api_client.get(url, {'org_id': 'or79Cob97KSh'})
    assert response.status_code == 400

    mocker.patch(
        'sageintacctsdk.apis.Employees.get_all_generator',
        return_value=data['get_employees']
    )

    response = api_client.get(url, {'org_id': 'or79Cob97KSh', 'resource_type': 'employees'})
    assert response.status_code == 200


@pytest.mark.django_db(databases=['default'])
@patch.object(IsAuthenticatedForInternalAPI, 'has_permission', return_value=True)
def test_exported_entry_view(db, api_client, mocker):
    url = reverse('exported-entry')

    response = api_client.get(url)
    assert response.status_code == 400

    response = api_client.get(url, {'org_id': 'or79Cob97KSh'})
    assert response.status_code == 400

    response = api_client.get(url, {'org_id': 'or79Cob97KSh', 'resource_type': 'bill'})
    assert response.status_code == 400

    mocker.patch(
        'sageintacctsdk.apis.Bills.get',
        return_value={'summa': 'hehe'}
    )

    response = api_client.get(url, {'org_id': 'or79Cob97KSh', 'resource_type': 'bill', 'internal_id': '1'})
    assert response.status_code == 200
