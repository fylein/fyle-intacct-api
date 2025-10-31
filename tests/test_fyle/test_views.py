import json
from unittest import mock

import pytest
from django.urls import reverse
from fyle.platform.exceptions import PlatformError
from fyle_accounting_mappings.models import MappingSetting

from apps.tasks.models import TaskLog
from apps.workspaces.models import FyleCredential, Workspace
from tests.helper import dict_compare_keys
from tests.test_fyle.fixtures import data


def test_exportable_expense_group_view(api_client, test_connection):
    """
    Test exportable expense group view
    """
    access_token = test_connection.access_token
    url = '/api/workspaces/1/fyle/exportable_expense_groups/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response['exportable_expense_group_ids'] == [1, 2, 3]


def test_expense_group_view(api_client, test_connection):
    """
    Test expense group view
    """
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/expense_groups/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response['count'] == 3

    response = api_client.get(url, {
        'state': 'ALL'
    })
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response['count'] == 3

    response = api_client.get(url, {
        'task_log__status': 'COMPLETE',
        'exported_at__gte': '2022-05-23 13:03:06',
        'exported_at__lte': '2022-05-23 13:03:48',
    })
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response['count'] == 0

    response = api_client.get(url, {
        'state': 'READY'
    })

    response = json.loads(response.content)
    assert response['count'] == 3

    response = api_client.get(url, {
        'state': 'FAILED'
    })
    response = json.loads(response.content)
    assert response['count'] == 3

    response = api_client.get(url, {
        'expense_group_ids': '1,3'
    })
    response = json.loads(response.content)
    assert response['count'] == 3

    task_log, _ = TaskLog.objects.update_or_create(
        workspace_id=1,
        type='FETCHING_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )
    response = api_client.post(
        url,
        data={'task_log_id': task_log.id},
        format='json'
    )
    assert response.status_code == 200


def test_expense_group_settings_view(api_client, test_connection):
    """
    Test expense group settings view
    """
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/expense_group_settings/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))
    response = api_client.get(url)
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['expense_group_setting_response']) == [], 'expense group api return diffs in keys'
    assert response['reimbursable_expense_group_fields'] == ['employee_email', 'report_id', 'claim_number', 'fund_source']
    assert response['expense_state'] == 'PAYMENT_PROCESSING'
    assert response['reimbursable_export_date_type'] == 'current_date'

    response = api_client.post(
        url,
        data=data['expense_group_settings_payload'],
        format='json'
    )
    assert response.status_code == 200
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['expense_group_setting_response']) == [], 'expense group api return diffs in keys'
    assert response['expense_state'] == 'PAYMENT_PROCESSING'
    assert response['reimbursable_export_date_type'] == 'spent_at'
    assert response['ccc_expense_state'] == 'PAID'


def test_expense_attributes_view(api_client, test_connection):
    """
    Test expense attributes view
    """
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/expense_attributes/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response == []


def test_fyle_fields_view(api_client, test_connection):
    """
    Test fyle fields view
    """
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/fyle_fields/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response[0] == {'attribute_type': 'COST_CENTER', 'display_name': 'Cost Center', 'is_dependent': False}


@pytest.mark.django_db(databases=['default'])
def test_fyle_sync_dimension(api_client, test_connection, mocker):
    """
    Test fyle sync dimension
    """
    mocker.patch(
        'fyle.platform.apis.v1.admin.Employees.list_all',
        return_value=data['get_all_employees']
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.Categories.list_all',
        return_value=data['get_all_categories']
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.Projects.list_all',
        return_value=data['get_all_projects']
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.CostCenters.list_all',
        return_value=data['get_all_cost_centers']
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.ExpenseFields.list_all',
        return_value=data['get_all_expense_fields']
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.CorporateCards.list_all',
        return_value=data['get_all_corporate_cards']
    )

    mocker.patch(
        'fyle_integrations_platform_connector.fyle_integrations_platform_connector.PlatformConnector.import_fyle_dimensions',
        return_value=[]
    )

    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/sync_dimensions/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.post(url)
    assert response.status_code == 200

    workspace = Workspace.objects.get(id=1)
    workspace.source_synced_at = None
    workspace.save()
    response = api_client.post(url)
    assert response.status_code == 200


@pytest.mark.django_db(databases=['default'])
def test_fyle_sync_dimension_skip_with_webhook_sync_enabled(api_client, test_connection, mocker):
    """
    Test fyle sync dimension skips when webhook sync is enabled
    """
    from datetime import datetime, timezone

    from apps.workspaces.models import FeatureConfig
    workspace = Workspace.objects.get(id=1)
    feature_config = FeatureConfig.objects.get(workspace=workspace)
    feature_config.fyle_webhook_sync_enabled = True
    feature_config.save()
    workspace.source_synced_at = datetime.now(tz=timezone.utc)
    workspace.save()
    mock_import = mocker.patch(
        'fyle_integrations_platform_connector.fyle_integrations_platform_connector.PlatformConnector.import_fyle_dimensions'
    )
    access_token = test_connection.access_token
    url = '/api/workspaces/1/fyle/sync_dimensions/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))
    response = api_client.post(url)
    assert response.status_code == 200
    mock_import.assert_not_called()
    feature_config.fyle_webhook_sync_enabled = False
    feature_config.save()


def test_fyle_sync_dimension_fail(api_client, test_connection):
    """
    Test fyle sync dimension fail
    """
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/sync_dimensions/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    workspace = Workspace.objects.get(id=1)
    workspace.source_synced_at = None
    workspace.save()

    fyle_credentials = FyleCredential.objects.get(workspace_id=1)
    with mock.patch('fyle_integrations_platform_connector.fyle_integrations_platform_connector.PlatformConnector.import_fyle_dimensions') as mock_call:
        mock_call.side_effect = PlatformError(msg='Something wrong with PlatformConnector', response='Something wrong with PlatformConnector')
        _ = api_client.post(url)
    fyle_credentials.delete()

    new_response = api_client.post(url)
    assert new_response.status_code == 400
    assert new_response.data['message'] == 'Fyle credentials not found in workspace'


def test_fyle_refresh_dimension(api_client, test_connection, mocker):
    """
    Test fyle refresh dimension
    """
    mocker.patch(
        'fyle.platform.apis.v1.admin.Employees.list_all',
        return_value=data['get_all_employees']
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.Categories.list_all',
        return_value=data['get_all_categories']
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.Projects.list_all',
        return_value=data['get_all_projects']
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.CostCenters.list_all',
        return_value=data['get_all_cost_centers']
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.ExpenseFields.list_all',
        return_value=data['get_all_expense_fields']
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.CorporateCards.list_all',
        return_value=data['get_all_corporate_cards']
    )

    mocker.patch(
        'fyle_integrations_platform_connector.fyle_integrations_platform_connector.PlatformConnector.import_fyle_dimensions',
        return_value=[]
    )

    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )

    workspace_id = 1

    MappingSetting.objects.update_or_create(
        workspace_id=workspace_id,
        source_field = 'PROJECT',
        defaults={
            'destination_field': 'CUSTOMER',
            'import_to_fyle': True

        }
    )

    MappingSetting.objects.update_or_create(
        workspace_id=workspace_id,
        source_field = 'COST_CENTER',
        defaults={
            'destination_field': 'ACCOUNT',
            'import_to_fyle': True

        }
    )

    with mocker.patch('apps.fyle.helpers.DimensionDetail.bulk_create_or_update_dimension_details', return_value=None):
        MappingSetting.objects.update_or_create(
            workspace_id = workspace_id,
            source_field = 'Ashutosh Field',
            defaults={
                'destination_field': 'CLASS',
                'import_to_fyle': True,
                'is_custom': True
            }
        )

    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/refresh_dimensions/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.post(url)
    assert response.status_code == 200

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    with mock.patch('fyle_integrations_platform_connector.fyle_integrations_platform_connector.PlatformConnector.import_fyle_dimensions') as mock_call:
        mock_call.side_effect = PlatformError(msg='Something wrong with PlatformConnector', response='Something wrong with PlatformConnector')
        response = api_client.post(url)

    fyle_credentials.delete()

    response = api_client.post(url)

    assert response.status_code == 400
    assert response.data['message'] == 'Fyle credentials not found in workspace'


def test_expense_filters(api_client, test_connection):
    """
    Test expense filters
    """
    access_token = test_connection.access_token

    url = reverse('expense-filters',
        kwargs={
            'workspace_id': 1,
        }
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.post(url,data=data['expense_filter_1'])
    assert response.status_code == 201
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['expense_filter_1_response']) == [], 'expense group api return diffs in keys'

    response = api_client.post(url,data=data['expense_filter_2'])
    assert response.status_code == 201
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['expense_filter_2_response']) == [], 'expense group api return diffs in keys'

    response = api_client.get(url)
    assert response.status_code == 200
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['expense_filters_response']) == [], 'expense group api return diffs in keys'


@pytest.mark.django_db(databases=['default'])
def test_custom_fields(mocker, api_client, test_connection):
    """
    Test custom fields
    """
    access_token = test_connection.access_token

    url = reverse('custom-field',
        kwargs={
            'workspace_id': 1,
        }
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.expense_fields.list_all',
        return_value=data['get_all_custom_fields']
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['custom_fields_response']) == [], 'expense group api return diffs in keys'


@pytest.mark.django_db(databases=['default'])
def test_expenses(mocker, api_client, test_connection):
    """
    Test expenses
    """
    access_token = test_connection.access_token

    url = reverse('expenses',
        kwargs={
            'workspace_id': 1,
        }
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['skipped_expenses']) == [], 'expense group api return diffs in keys'
