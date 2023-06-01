from apps.fyle.models import ExpenseGroup
from apps.workspaces.models import FyleCredential, Workspace
from fyle_accounting_mappings.models import MappingSetting
import pytest
import json
from .fixtures import data
from tests.helper import dict_compare_keys
from apps.tasks.models import TaskLog
from django.urls import reverse


def test_expense_group_view(api_client, test_connection):
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/expense_groups/'
    
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code==200

    response = json.loads(response.content)
    assert response['count'] == 3

    response = api_client.get(url, {
        'state': 'ALL'
    })
    assert response.status_code==200

    response = json.loads(response.content)
    assert response['count'] == 3

    response = api_client.get(url, {
        'state': 'COMPLETE',
        'start_date': '2022-05-23 13:03:06',
        'end_date': '2022-05-23 13:03:48',
        'exported_at': '2022-05-23 13:03:06'
    })
    assert response.status_code==200

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
    assert response.status_code==200


def test_expense_group_settings_view(api_client, test_connection):
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
    assert response.status_code==200
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['expense_group_setting_response']) == [], 'expense group api return diffs in keys'
    assert response['expense_state'] == 'PAYMENT_PROCESSING'
    assert response['reimbursable_export_date_type'] == 'spent_at'
    assert response['ccc_expense_state'] == 'PAID'


def test_expense_attributes_view(api_client, test_connection):
    
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/expense_attributes/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response == []


def test_fyle_fields_view(api_client, test_connection):
    
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/fyle_fields/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response[0] == {'attribute_type': 'COST_CENTER', 'display_name': 'Cost Center'}


def test_expense_group_schedule_view(api_client, test_connection):
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/expense_groups/trigger/'
    
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))
    response = api_client.post(url)

    assert response.status_code==200


def test_expense_group_id_view(api_client, test_connection):
    
    access_token = test_connection.access_token

    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()

    url = '/api/workspaces/1/fyle/expense_groups/{}/'.format(expense_group.id)
    
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response, data['expense_group_id_response']) == [], 'expense group api return diffs in keys'


def test_expense_group_by_id_expenses_view(api_client, test_connection):
    
    access_token = test_connection.access_token

    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()

    url = '/api/workspaces/1/fyle/expense_groups/{}/expenses/'.format(expense_group.id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response, data['expense_group_by_id_expenses_response']) == [], 'expense group api return diffs in keys'

    url = '/api/workspaces/1/fyle/expense_groups/{}/expenses/'.format(3000)

    response = api_client.get(url)
    assert response.status_code == 400
    assert response.data['message'] == 'Expense group not found'


def test_expense_view(api_client, test_connection):

    access_token = test_connection.access_token

    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()

    url = '/api/workspaces/1/fyle/expense_groups/{}/expenses/'.format(expense_group.id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response, data['expense_group_by_id_expenses_response']) == [], 'expense group api return diffs in keys'

    url = '/api/workspaces/1/fyle/expense_groups/{}/expenses/'.format(3000)

    response = api_client.get(url)
    assert response.status_code == 400
    assert response.data['message'] == 'Expense group not found'


def test_employees_view(api_client, test_connection):
    
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/employees/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response[0], data['employee_view'][0]) == [], 'employee_view api return diffs in keys'


def test_categories_view(api_client, test_connection):
    
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/categories/' 

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response[0], data['categories_view'][0]) == [], 'categories_view api return diffs in keys'


def test_cost_centers_view(api_client, test_connection):
    
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/cost_centers/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response[0], data['cost_centers_view'][0]) == [], 'cost_centers_view api return diffs in keys'


def test_projects_view(api_client, test_connection):
    
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/projects/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response[0] == data['project_view'][0]


@pytest.mark.django_db(databases=['default'])
def test_fyle_sync_dimension(api_client, test_connection, mocker):
    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Employees.list_all',
        return_value=data['get_all_employees']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Categories.list_all',
        return_value=data['get_all_categories']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Projects.list_all',
        return_value=data['get_all_projects']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.CostCenters.list_all',
        return_value=data['get_all_cost_centers']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.ExpenseFields.list_all',
        return_value=data['get_all_expense_fields']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.CorporateCards.list_all',
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


def test_fyle_sync_dimension_fail(api_client, test_connection):
    access_token = test_connection.access_token

    url = '/api/workspaces/1/fyle/sync_dimensions/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    workspace = Workspace.objects.get(id=1)
    workspace.source_synced_at = None
    workspace.save()

    fyle_credentials = FyleCredential.objects.get(workspace_id=1)
    fyle_credentials.delete()

    new_response = api_client.post(url)
    assert new_response.status_code == 400
    assert new_response.data['message'] == 'Fyle credentials not found in workspace'


def test_fyle_refresh_dimension(api_client, test_connection, mocker):
    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Employees.list_all',
        return_value=data['get_all_employees']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Categories.list_all',
        return_value=data['get_all_categories']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Projects.list_all',
        return_value=data['get_all_projects']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.CostCenters.list_all',
        return_value=data['get_all_cost_centers']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.ExpenseFields.list_all',
        return_value=data['get_all_expense_fields']
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.CorporateCards.list_all',
        return_value=data['get_all_corporate_cards']
    )

    mocker.patch(
        'fyle_integrations_platform_connector.fyle_integrations_platform_connector.PlatformConnector.import_fyle_dimensions',
        return_value=[]
    )

    mocker.patch(
        'apps.mappings.signals.upload_attributes_to_fyle',
        return_value = []
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
    fyle_credentials.delete()

    response = api_client.post(url)

    assert response.status_code == 400
    assert response.data['message'] == 'Fyle credentials not found in workspace'


def test_expense_filters(api_client, test_connection):
   access_token=test_connection.access_token

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
   access_token=test_connection.access_token

   url = reverse('custom-field', 
      kwargs={
         'workspace_id': 1,
      }
   )

   mocker.patch(
      'fyle.platform.apis.v1beta.admin.expense_fields.list_all',
      return_value=data['get_all_custom_fields']
   )

   api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

   response = api_client.get(url)
   assert response.status_code == 200
   response = json.loads(response.content)

   assert dict_compare_keys(response, data['custom_fields_response']) == [], 'expense group api return diffs in keys'


@pytest.mark.django_db(databases=['default'])
def test_expenses(mocker, api_client, test_connection):
   access_token=test_connection.access_token

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