import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from fyle.platform import exceptions as fyle_exc
from fyle_accounting_mappings.models import MappingSetting
from fyle_rest_auth.utils import AuthUtils
from sageintacctsdk import exceptions as sage_intacct_exc
from intacctsdk.exceptions import (
    BadRequestError as SageIntacctRESTBadRequestError,
    InvalidTokenError as SageIntacctRestInvalidTokenError,
    InternalServerError as SageIntacctRESTInternalServerError
)

from apps.sage_intacct.models import SageIntacctAttributesCount
from apps.tasks.models import TaskLog
from apps.workspaces.models import Configuration, FeatureConfig, LastExportDetail, SageIntacctCredential, Workspace
from apps.workspaces.enums import SystemCommentIntentEnum, SystemCommentSourceEnum
from fyle_accounting_library.system_comments.models import SystemComment
from fyle_integrations_imports.models import ImportLog
from tests.helper import dict_compare_keys
from tests.test_fyle.fixtures import data as fyle_data
from tests.test_workspaces.fixtures import data

User = get_user_model()
auth_utils = AuthUtils()


def test_ready_view(api_client, test_connection):
    """
    Test Ready View
    """
    url = '/api/workspaces/ready/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    response['message'] == 'Ready'


def test_token_health_view(api_client, test_connection, mocker):
    """
    Test Token Health View for Sage Intacct connectivity
    """
    workspace_id = 1

    url = f"/api/workspaces/{workspace_id}/token_health/"
    api_client.credentials(HTTP_AUTHORIZATION="Bearer {}".format(test_connection.access_token))

    # Clean cache before test
    cache_key = f'HEALTH_CHECK_CACHE_{workspace_id}'
    cache.delete(cache_key)

    SageIntacctCredential.objects.filter(workspace=workspace_id).delete()
    response = api_client.get(url)

    assert response.status_code == 400
    assert response.data["message"] == "Intacct credentials not found"

    workspace = Workspace.objects.get(id=workspace_id)
    SageIntacctCredential.objects.all().delete()
    SageIntacctCredential.objects.create(
        workspace=workspace,
        si_user_id="test_user",
        si_company_id="test_company",
        si_user_password="test_password",
        is_expired=True
    )
    response = api_client.get(url)

    assert response.status_code == 400
    assert response.data["message"] == "Intacct connection expired"

    SageIntacctCredential.objects.all().delete()
    SageIntacctCredential.objects.create(
        workspace=workspace,
        si_user_id="test_user",
        si_company_id="test_company",
        si_user_password="test_password",
        is_expired=False
    )

    mock_connector = mocker.patch('apps.workspaces.views.get_sage_intacct_connection')
    mock_instance = mocker.MagicMock()
    mock_connector.return_value = mock_instance
    mock_instance.connection.locations.count.side_effect = Exception("Invalid")

    # Mock invalidate function
    mocker.patch('apps.workspaces.views.invalidate_sage_intacct_credentials', return_value=None)

    response = api_client.get(url)

    assert response.status_code == 400
    assert response.data["message"] == "Something went wrong"

    mocker.resetall()
    mock_connector = mocker.patch('apps.workspaces.views.get_sage_intacct_connection')
    mock_instance = mocker.MagicMock()
    mock_connector.return_value = mock_instance
    mock_instance.connection.locations.count.side_effect = sage_intacct_exc.InvalidTokenError("Invalid token")

    mocker.patch('apps.workspaces.views.invalidate_sage_intacct_credentials', return_value=None)

    response = api_client.get(url)
    assert response.status_code == 400
    assert response.data["message"] == "Intacct connection expired"

    # Testing successful connection
    mocker.resetall()
    mock_connector = mocker.patch('apps.workspaces.views.get_sage_intacct_connection')
    mock_instance = mocker.MagicMock()
    mock_connector.return_value = mock_instance
    mock_instance.connection.locations.count.return_value = 1

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data["message"] == "Intacct connection is active"

    # Testing with cache
    cache.set(cache_key, True, timeout=timedelta(hours=24).total_seconds())

    assert cache.get(cache_key) == True

    # Reset mock to verify it's not called when cache is present
    mock_connector.reset_mock()
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data["message"] == "Intacct connection is active"
    mock_connector.assert_not_called()


def test_get_workspace(api_client, test_connection):
    """
    Test Get Workspace
    """
    url = '/api/workspaces/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response == []


def test_get_workspace_by_id(api_client, test_connection):
    """
    Test Get Workspace By Id
    """
    workspace_id = 1

    url = '/api/workspaces/{}/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response, data['workspace']) == [], 'workspaces api returns a diff in the keys'

    workspace_id = 5

    url = '/api/workspaces/{}/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 400


def test_post_and_patch_of_workspace(api_client, test_connection, mocker):
    """
    Test Post and Patch of Workspace
    """
    url = '/api/workspaces/'

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    mocker.patch(
        'apps.workspaces.views.get_fyle_admin',
        return_value=fyle_data['get_my_profile']
    )

    mocker.patch(
        'apps.workspaces.views.get_cluster_domain',
        return_value={
            'cluster_domain': 'https://staging.fyle.tech/'
        }
    )

    response = api_client.post(url)
    assert response.status_code == 200
    response = json.loads(response.content)
    assert dict_compare_keys(response, data['workspace']) == [], 'workspaces api returns a diff in the keys'

    workspace_id = 1
    url = '/api/workspaces/{}/'.format(workspace_id)
    workspace = Workspace.objects.get(id=data['workspace']['id'])

    assert workspace.app_version == 'v1'
    data['workspace']['app_version'] = 'v2'
    response = api_client.patch(url,
        data={
            'app_version': 'v2'
        }
    )

    workspace = Workspace.objects.get(id=data['workspace']['id'])
    assert workspace.app_version == 'v2'


def test_workspace_creation_creates_attributes_count(api_client, test_connection, mocker):
    """
    Test Workspace Creation Creates Attributes Count
    """
    url = '/api/workspaces/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    mocker.patch('apps.workspaces.views.get_fyle_admin', return_value=fyle_data['get_my_profile'])
    mocker.patch('apps.workspaces.views.get_cluster_domain', return_value={'cluster_domain': 'https://staging.fyle.tech/'})
    response = api_client.post(url)
    assert response.status_code == 200
    response_data = json.loads(response.content)
    workspace_id = response_data['id']
    attributes_count = SageIntacctAttributesCount.objects.filter(workspace_id=workspace_id).first()
    assert attributes_count is not None
    assert attributes_count.accounts_count == 0
    assert attributes_count.vendors_count == 0
    assert attributes_count.employees_count == 0


def test_connect_fyle_view(api_client, test_connection):
    """
    Test Connect Fyle View
    """
    workspace_id = 1

    url = '/api/workspaces/{}/credentials/fyle/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    url = '/api/workspaces/{}/credentials/fyle/delete/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.delete(url)
    assert response.status_code == 200

    url = '/api/workspaces/{}/credentials/fyle/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 400


def test_connect_fyle_view_post(mocker, api_client, test_connection):
    """
    Test Connect Fyle View Post
    """
    mocker.patch(
        'fyle_rest_auth.utils.AuthUtils.generate_fyle_refresh_token',
        return_value={'refresh_token': 'asdfghjk', 'access_token': 'qwertyuio'}
    )
    mocker.patch(
        'apps.workspaces.views.get_fyle_admin',
        return_value={'data': {'org': {'name': 'Fyle For Arkham Asylum', 'id': 'or79Cob97KSh'}}}
    )
    mocker.patch(
        'apps.workspaces.views.get_cluster_domain',
        return_value='https://staging.fyle.tech'
    )
    workspace_id = 1

    code = 'sdfghj'
    url = '/api/workspaces/{}/connect_fyle/authorization_code/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.post(
        url,
        data={'code': code}
    )
    assert response.status_code == 200


def test_connect_fyle_view_exceptions(api_client, test_connection):
    """
    Test Connect Fyle View Exceptions
    """
    workspace_id = 1

    code = 'qwertyu'
    url = '/api/workspaces/{}/connect_fyle/authorization_code/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    with mock.patch('fyle_rest_auth.utils.AuthUtils.generate_fyle_refresh_token') as mock_call:
        mock_call.side_effect = fyle_exc.UnauthorizedClientError(msg='Invalid Authorization Code', response='Invalid Authorization Code')

        response = api_client.post(
            url,
            data={'code': code}
        )
        assert response.status_code == 403

        mock_call.side_effect = fyle_exc.NotFoundClientError(msg='Fyle Application not found', response='Fyle Application not found')

        response = api_client.post(
            url,
            data={'code': code}
        )
        assert response.status_code == 404

        mock_call.side_effect = fyle_exc.WrongParamsError(msg='Some of the parameters are wrong', response='Some of the parameters are wrong')

        response = api_client.post(
            url,
            data={'code': code}
        )
        assert response.status_code == 400

        mock_call.side_effect = fyle_exc.InternalServerError(msg='Wrong/Expired Authorization code', response='Wrong/Expired Authorization code')

        response = api_client.post(
            url,
            data={'code': code}
        )
        assert response.status_code == 401


def test_connect_sageintacct_view(api_client, test_connection):
    """
    Test Connect Sage Intacct View
    """
    workspace_id = 1

    url = '/api/workspaces/{}/credentials/sage_intacct/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)

    url = '/api/workspaces/{}/credentials/sage_intacct/delete/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.delete(url)
    assert response.status_code == 200

    url = '/api/workspaces/{}/credentials/sage_intacct/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 400


def test_connect_sageintacct_view_post(mocker, api_client, test_connection):
    """
    Test Connect Sage Intacct View Post
    """
    mocker.patch(
        'sageintacctsdk.apis.Attachments.create_attachments_folder',
        return_value={}
    )

    mocker.patch(
        'sageintacctsdk.apis.Attachments.get_folder',
        return_value={'listtype': 'supdocfolder'}
    )

    workspace_id = 1

    code = 'asdfghj'
    url = '/api/workspaces/{}/credentials/sage_intacct/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.post(
        url,
        data={
            'code': code,
            'si_user_password': 'sample',
            'si_user_id': 'sdfghj',
            'si_company_id': 'kjhgfz',
            'si_company_name': 'fghjk'
        }
    )

    assert response.status_code == 200

    sage_intacct_credentials = SageIntacctCredential.objects.filter(workspace_id=workspace_id).first()
    sage_intacct_credentials.delete()

    response = api_client.post(
        url,
        data={
            'code': code,
            'si_user_password': 'sample',
            'si_user_id': 'sdfghj',
            'si_company_id': 'kjhgfz',
            'si_company_name': 'fghjk'
        }
    )
    assert response.status_code == 200


def test_connect_sageintacct_view_exceptions(api_client, test_connection):
    """
    Test Connect Sage Intacct View Exceptions
    """
    workspace_id = 1

    code = 'qwertyu'
    url = '/api/workspaces/{}/credentials/sage_intacct/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    with mock.patch('apps.workspaces.models.SageIntacctCredential.objects.filter') as mock_call:
        mock_call.side_effect = sage_intacct_exc.NotFoundItemError(msg='Application not found', response=json.dumps({'message': 'Application not found'}))

        response = api_client.post(
            url,
            data={
                'code': code,
                'si_user_password': 'sample',
                'si_user_id': 'sdfghj',
                'si_company_id': 'kjhgfz',
                'si_company_name': 'fghjk'
            }
        )
        assert response.status_code == 404

        mock_call.side_effect = sage_intacct_exc.WrongParamsError(msg='invalid grant', response=json.dumps({'message': 'invalid grant'}))

        response = api_client.post(
            url,
            data={
                'code': code,
                'si_user_password': 'sample',
                'si_user_id': 'sdfghj',
                'si_company_id': 'kjhgfz',
                'si_company_name': 'fghjk'
            }
        )
        assert response.status_code == 400

        mock_call.side_effect = sage_intacct_exc.InvalidTokenError(msg='Invalid token', response='Invalid token')

        response = api_client.post(
            url,
            data={
                'code': code,
                'si_user_password': 'sample',
                'si_user_id': 'sdfghj',
                'si_company_id': 'kjhgfz',
                'si_company_name': 'fghjk'
            }
        )
        assert response.status_code == 401

        mock_call.side_effect = sage_intacct_exc.InternalServerError(msg='Wrong/Expired Authorization code', response='Wrong/Expired Authorization code')

        response = api_client.post(
            url,
            data={
                'code': code,
                'si_user_password': 'sample',
                'si_user_id': 'sdfghj',
                'si_company_id': 'kjhgfz',
                'si_company_name': 'fghjk'
            }
        )
        assert response.status_code == 401


def test_general_settings_detail(api_client, test_connection):
    """
    Test General Settings Detail
    """
    workspace_id = 1

    url = '/api/workspaces/{}/configuration/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response, data['workspace_general_settings_payload']) == [], 'general_setting api returns a diff in keys'

    configurations_object = Configuration.objects.get(workspace_id=workspace_id)
    configurations_object.delete()

    response = api_client.post(
        url,
        data=data['workspace_general_settings_payload'],
        format='json'
    )

    assert response.status_code == 201

    response = api_client.patch(
        url,
        data = {
            'import_projects': False
        }
    )
    assert response.status_code == 200

    configurations_object = Configuration.objects.get(workspace_id=workspace_id)
    configurations_object.delete()

    test_data = data['workspace_general_settings_payload']
    test_data['auto_map_employees'] = 'EMPLOYEE_CODE'

    response = api_client.post(
        url,
        data=test_data,
        format='json'
    )

    assert response.status_code == 400


def test_workspace_admin_view(mocker, api_client, test_connection):
    """
    Test Workspace Admin View
    """
    workspace_id = 1

    url = '/api/workspaces/{}/admins/'.format(workspace_id)

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200


def test_export_to_intacct(mocker, api_client, test_connection):
    """
    Test Export To Intacct
    """
    mocker.patch(
        'apps.workspaces.views.export_to_intacct',
        return_value=None
    )

    workspace_id = 1
    url = '/api/workspaces/{}/exports/trigger/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.post(url)
    assert response.status_code == 200


def test_export_to_intacct_with_rabbitmq(mocker, api_client, test_connection):
    """
    Test Export To Intacct with RabbitMQ enabled (covers lines 586, 595)
    """
    workspace_id = 1

    # Enable export_via_rabbitmq in FeatureConfig
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.export_via_rabbitmq = True
    feature_config.save()

    # Mock the RabbitMQ publish function to track if it's called
    mock_publish_to_rabbitmq = mocker.patch('apps.workspaces.views.publish_to_rabbitmq')

    url = '/api/workspaces/{}/exports/trigger/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.post(url)
    assert response.status_code == 200

    # Verify that publish_to_rabbitmq was called (covers line 595)
    mock_publish_to_rabbitmq.assert_called_once()

    # Verify the payload structure
    call_args = mock_publish_to_rabbitmq.call_args
    payload_arg = call_args[1]['payload']
    routing_key_arg = call_args[1]['routing_key']

    assert payload_arg['workspace_id'] == workspace_id
    assert payload_arg['action'] == 'EXPORT.P0.DASHBOARD_SYNC'
    assert payload_arg['data']['workspace_id'] == workspace_id
    assert payload_arg['data']['triggered_by'] == 'DASHBOARD_SYNC'
    assert payload_arg['data']['run_in_rabbitmq_worker'] == True
    assert routing_key_arg == 'EXPORT.P0.*'

    # Reset the feature config
    feature_config.export_via_rabbitmq = False
    feature_config.save()


def test_workspaces_view_with_workspace_name_update(mocker, api_client, test_connection):
    """
    Test WorkspacesView to cover lines 151, 159 (RabbitMQ publish for workspace name update)
    """
    # Mock the RabbitMQ publish function to track if it's called
    mock_publish_to_rabbitmq = mocker.patch('apps.workspaces.views.publish_to_rabbitmq')

    # Get workspaces with org_id parameter and is_polling=False (or omitted)
    url = '/api/workspaces/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    # Test with org_id and without is_polling (defaults to False)
    response = api_client.get(url, {'org_id': 'or79Cob97KSh'})
    assert response.status_code == 200

    # Verify that publish_to_rabbitmq was called (covers line 159)
    mock_publish_to_rabbitmq.assert_called_once()

    # Verify the payload structure
    call_args = mock_publish_to_rabbitmq.call_args
    payload_arg = call_args[1]['payload']
    routing_key_arg = call_args[1]['routing_key']

    assert payload_arg['action'] == 'UTILITY.UPDATE_WORKSPACE_NAME'
    assert payload_arg['data']['workspace_id'] == 1  # Should be the workspace ID from fixtures
    assert 'access_token' in payload_arg['data']
    assert routing_key_arg == 'UTILITY.*'

    # Reset mock for next test
    mock_publish_to_rabbitmq.reset_mock()

    # Test with is_polling=True (should NOT trigger RabbitMQ)
    response = api_client.get(url, {'org_id': 'or79Cob97KSh', 'is_polling': 'true'})
    assert response.status_code == 200

    # Verify that publish_to_rabbitmq was NOT called when polling
    mock_publish_to_rabbitmq.assert_not_called()


def test_last_export_detail_view(mocker, db, api_client, test_connection):
    """
    Test Last Export Detail View
    """
    workspace_id = 1
    url = '/api/workspaces/{}/export_detail/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    last_export_detail = LastExportDetail.objects.filter(workspace_id=workspace_id).first()
    last_export_detail.total_expense_groups_count = 0
    last_export_detail.save()

    response = api_client.get(url)
    assert response.status_code == 404


def test_last_export_detail_2(mocker, api_client, test_connection):
    """
    Test Last Export Detail View
    """
    workspace_id = 1

    Configuration.objects.filter(workspace_id=workspace_id).update(
        reimbursable_expenses_object='BILL',
        corporate_credit_card_expenses_object='BILL'
    )

    url = "/api/workspaces/{}/export_detail/?start_date=2025-05-01".format(workspace_id)

    api_client.credentials(
        HTTP_AUTHORIZATION="Bearer {}".format(test_connection.access_token)
    )

    LastExportDetail.objects.get(workspace_id=workspace_id)
    # last_exported_at=datetime.now(), total_expense_groups_count=1

    TaskLog.objects.create(type='CREATING_EXPENSE_REPORT', status='COMPLETE', workspace_id=workspace_id)

    failed_count = TaskLog.objects.filter(workspace_id=workspace_id, status__in=['FAILED', 'FATAL']).count()

    response = api_client.get(url)
    assert response.status_code == 200

    response = json.loads(response.content)
    assert response['repurposed_successful_count'] == 1
    assert response['repurposed_failed_count'] == failed_count
    assert response['repurposed_last_exported_at'] is not None


def test_import_code_field_view(db, mocker, api_client, test_connection):
    """
    Test ImportCodeFieldView
    """
    workspace_id = 1
    url = reverse('import-code-fields-config', kwargs={'workspace_id': workspace_id})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    department_log = ImportLog.update_or_create_in_progress_import_log('COST_CENTER', workspace_id)
    project_log = ImportLog.update_or_create_in_progress_import_log('PROJECT', workspace_id)

    with mocker.patch('django.db.models.signals.post_save.send'):
        # Create MappingSetting object with the signal mocked
        MappingSetting.objects.update_or_create(
            destination_field='PROJECT',
            workspace_id=workspace_id,
            defaults={
                'source_field': 'PROJECT',
                'import_to_fyle': True,
                'is_custom': False
            }
        )

        MappingSetting.objects.update_or_create(
            destination_field='DEPARTMENT',
            workspace_id=workspace_id,
            defaults={
                'source_field': 'COST_CENTER',
                'import_to_fyle': True,
                'is_custom': False
            }
        )

    Configuration.objects.filter(workspace_id=workspace_id).update(import_code_fields=['ACCOUNT', 'EXPENSE_TYPE'])

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == {
        'PROJECT': False,
        'EXPENSE_TYPE': False,
        'ACCOUNT': False,
        'DEPARTMENT': False
    }

    project_log.delete()
    department_log.delete()

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == {
        'PROJECT': True,
        'EXPENSE_TYPE': False,
        'ACCOUNT': False,
        'DEPARTMENT': True
    }

    Configuration.objects.filter(workspace_id=workspace_id).update(import_code_fields=[])

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == {
        'PROJECT': True,
        'EXPENSE_TYPE': True,
        'ACCOUNT': True,
        'DEPARTMENT': True
    }


def test_handle_sage_intacct_rest_api_connection_new_credentials(mocker, api_client, test_connection):
    """
    Test handle_sage_intacct_rest_api_connection creates new credentials
    """
    workspace_id = 1

    # Enable migrated_to_rest_api feature
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.migrated_to_rest_api = True
    feature_config.save()

    # Delete existing credentials
    SageIntacctCredential.objects.filter(workspace_id=workspace_id).delete()

    # Mock IntacctRESTSDK
    mock_sdk_instance = mocker.MagicMock()
    mock_sdk_instance.access_token = 'test_access_token'
    mock_sdk_instance.access_token_expires_in = 21600
    mock_sdk_instance.attachment_folders.get_all_generator.return_value = iter([[]])

    mocker.patch('apps.workspaces.views.IntacctRESTSDK', return_value=mock_sdk_instance)

    url = '/api/workspaces/{}/credentials/sage_intacct/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.post(
        url,
        data={
            'si_user_id': 'test_user',
            'si_company_id': 'test_company',
            'si_company_name': 'Test Company'
        }
    )

    assert response.status_code == 200

    # Verify credentials were created
    credentials = SageIntacctCredential.objects.filter(workspace_id=workspace_id).first()
    assert credentials is not None
    assert credentials.si_user_id == 'test_user'
    assert credentials.si_company_id == 'test_company'
    assert credentials.access_token == 'test_access_token'

    # Reset feature config
    feature_config.migrated_to_rest_api = False
    feature_config.save()


def test_handle_sage_intacct_rest_api_connection_existing_credentials(mocker, api_client, test_connection):
    """
    Test handle_sage_intacct_rest_api_connection updates existing credentials
    """
    workspace_id = 1
    workspace = Workspace.objects.get(id=workspace_id)

    # Enable migrated_to_rest_api feature
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.migrated_to_rest_api = True
    feature_config.save()

    # Create existing credentials
    SageIntacctCredential.objects.filter(workspace_id=workspace_id).delete()
    SageIntacctCredential.objects.create(
        workspace=workspace,
        si_user_id='old_user',
        si_company_id='old_company',
        si_company_name='Old Company',
        access_token='old_token',
        is_expired=True
    )

    # Mock IntacctRESTSDK
    mock_sdk_instance = mocker.MagicMock()
    mock_sdk_instance.access_token = 'new_access_token'
    mock_sdk_instance.access_token_expires_in = 21600
    mock_sdk_instance.attachment_folders.get_all_generator.return_value = iter([[]])

    mocker.patch('apps.workspaces.views.IntacctRESTSDK', return_value=mock_sdk_instance)
    mocker.patch('apps.workspaces.views.patch_integration_settings')

    url = '/api/workspaces/{}/credentials/sage_intacct/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.post(
        url,
        data={
            'si_user_id': 'new_user',
            'si_company_id': 'new_company',
            'si_company_name': 'New Company'
        }
    )

    assert response.status_code == 200

    # Verify credentials were updated
    credentials = SageIntacctCredential.objects.filter(workspace_id=workspace_id).first()
    assert credentials.si_user_id == 'new_user'
    assert credentials.si_company_id == 'new_company'
    assert credentials.si_company_name == 'New Company'
    assert credentials.access_token == 'new_access_token'
    assert credentials.is_expired is False

    # Reset feature config
    feature_config.migrated_to_rest_api = False
    feature_config.save()


def test_handle_sage_intacct_rest_api_connection_invalid_token_error(mocker, api_client, test_connection):
    """
    Test handle_sage_intacct_rest_api_connection handles invalid token error and creates system comment
    """
    workspace_id = 1

    # Enable migrated_to_rest_api feature
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.migrated_to_rest_api = True
    feature_config.save()

    # Delete existing credentials to trigger new connection path
    SageIntacctCredential.objects.filter(workspace_id=workspace_id).delete()

    SystemComment.objects.filter(workspace_id=workspace_id, intent=SystemCommentIntentEnum.CONNECTION_FAILED).delete()

    # Mock IntacctRESTSDK to raise InvalidTokenError
    mocker.patch(
        'apps.workspaces.views.IntacctRESTSDK',
        side_effect=SageIntacctRestInvalidTokenError('Invalid credentials', 'Invalid token response')
    )

    url = '/api/workspaces/{}/credentials/sage_intacct/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.post(
        url,
        data={
            'si_user_id': 'test_user',
            'si_company_id': 'test_company',
            'si_company_name': 'Test Company'
        }
    )

    assert response.status_code == 401

    system_comments = SystemComment.objects.filter(
        workspace_id=workspace_id,
        source=SystemCommentSourceEnum.HANDLE_SAGE_INTACCT_REST_API_CONNECTION,
        intent=SystemCommentIntentEnum.CONNECTION_FAILED
    )
    assert system_comments.count() == 1

    comment = system_comments.first()
    assert comment.workspace_id == workspace_id
    assert comment.entity_type is None
    assert comment.entity_id is None
    assert 'Invalid token error' in comment.detail['reason']
    assert comment.detail['info']['error_type'] == 'InvalidTokenError'

    # Reset feature config
    feature_config.migrated_to_rest_api = False
    feature_config.save()


def test_handle_sage_intacct_rest_api_connection_bad_request_error(mocker, api_client, test_connection):
    """
    Test handle_sage_intacct_rest_api_connection handles bad request error and creates system comment
    """
    workspace_id = 1

    # Enable migrated_to_rest_api feature
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.migrated_to_rest_api = True
    feature_config.save()

    # Delete existing credentials to trigger new connection path
    SageIntacctCredential.objects.filter(workspace_id=workspace_id).delete()

    SystemComment.objects.filter(workspace_id=workspace_id, intent=SystemCommentIntentEnum.CONNECTION_FAILED).delete()

    # Mock IntacctRESTSDK to raise BadRequestError
    mocker.patch(
        'apps.workspaces.views.IntacctRESTSDK',
        side_effect=SageIntacctRESTBadRequestError('Bad request', 'Invalid request data')
    )

    url = '/api/workspaces/{}/credentials/sage_intacct/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.post(
        url,
        data={
            'si_user_id': 'test_user',
            'si_company_id': 'test_company',
            'si_company_name': 'Test Company'
        }
    )

    assert response.status_code == 400

    system_comments = SystemComment.objects.filter(
        workspace_id=workspace_id,
        source=SystemCommentSourceEnum.HANDLE_SAGE_INTACCT_REST_API_CONNECTION,
        intent=SystemCommentIntentEnum.CONNECTION_FAILED
    )
    assert system_comments.count() == 1

    comment = system_comments.first()
    assert comment.workspace_id == workspace_id
    assert comment.entity_type is None
    assert comment.entity_id is None
    assert 'Bad request error' in comment.detail['reason']
    assert comment.detail['info']['error_type'] == 'BadRequestError'

    # Reset feature config
    feature_config.migrated_to_rest_api = False
    feature_config.save()


def test_handle_sage_intacct_rest_api_connection_internal_server_error(mocker, api_client, test_connection):
    """
    Test handle_sage_intacct_rest_api_connection handles internal server error and creates system comment
    """
    workspace_id = 1

    # Enable migrated_to_rest_api feature
    feature_config = FeatureConfig.objects.get(workspace_id=workspace_id)
    feature_config.migrated_to_rest_api = True
    feature_config.save()

    # Delete existing credentials to trigger new connection path
    SageIntacctCredential.objects.filter(workspace_id=workspace_id).delete()

    SystemComment.objects.filter(workspace_id=workspace_id, intent=SystemCommentIntentEnum.CONNECTION_FAILED).delete()

    # Mock IntacctRESTSDK to raise InternalServerError
    mocker.patch(
        'apps.workspaces.views.IntacctRESTSDK',
        side_effect=SageIntacctRESTInternalServerError('Internal server error', 'Server error response')
    )

    url = '/api/workspaces/{}/credentials/sage_intacct/'.format(workspace_id)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.post(
        url,
        data={
            'si_user_id': 'test_user',
            'si_company_id': 'test_company',
            'si_company_name': 'Test Company'
        }
    )

    assert response.status_code == 401
    assert response.data['message'] == 'Something went wrong while connecting to Sage Intacct'

    system_comments = SystemComment.objects.filter(
        workspace_id=workspace_id,
        source=SystemCommentSourceEnum.HANDLE_SAGE_INTACCT_REST_API_CONNECTION,
        intent=SystemCommentIntentEnum.CONNECTION_FAILED
    )
    assert system_comments.count() == 1

    comment = system_comments.first()
    assert comment.workspace_id == workspace_id
    assert comment.entity_type is None
    assert comment.entity_id is None
    assert 'Internal server error' in comment.detail['reason']
    assert comment.detail['info']['error_type'] == 'InternalServerError'

    # Reset feature config
    feature_config.migrated_to_rest_api = False
    feature_config.save()
