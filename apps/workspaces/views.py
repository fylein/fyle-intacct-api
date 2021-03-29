from django.conf import settings

from django.contrib.auth import get_user_model

from cryptography.fernet import Fernet

from sageintacctsdk import SageIntacctSDK, exceptions as sage_intacct_exc

from rest_framework.response import Response
from rest_framework.views import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from fylesdk import exceptions as fyle_exc

from fyle_rest_auth.utils import AuthUtils
from fyle_rest_auth.models import AuthToken

from fyle_intacct_api.utils import assert_valid

from apps.fyle.models import ExpenseGroupSettings

from .models import Workspace, FyleCredential, SageIntacctCredential, WorkspaceGeneralSettings, WorkspaceSchedule
from .utils import create_or_update_general_settings
from .serializers import WorkspaceSerializer, FyleCredentialSerializer, SageIntacctCredentialSerializer, \
    WorkSpaceGeneralSettingsSerializer, WorkspaceScheduleSerializer
from .tasks import schedule_sync

User = get_user_model()
auth_utils = AuthUtils()


class WorkspaceView(viewsets.ViewSet):
    """
    Sage Intacct Workspace
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a Workspace
        """

        auth_tokens = AuthToken.objects.get(user__user_id=request.user)
        fyle_user = auth_utils.get_fyle_user(auth_tokens.refresh_token)
        org_name = fyle_user['org_name']
        org_id = fyle_user['org_id']

        workspace = Workspace.objects.filter(fyle_org_id=org_id).first()

        if workspace:
            workspace.user.add(User.objects.get(user_id=request.user))
        else:
            workspace = Workspace.objects.create(name=org_name, fyle_org_id=org_id)

            ExpenseGroupSettings.objects.create(workspace_id=workspace.id)

            workspace.user.add(User.objects.get(user_id=request.user))

            FyleCredential.objects.update_or_create(
                refresh_token=auth_tokens.refresh_token,
                workspace_id=workspace.id
            )

        return Response(
            data=WorkspaceSerializer(workspace).data,
            status=status.HTTP_200_OK
        )

    def get(self, request):
        """
        Get workspace
        """
        user = User.objects.get(user_id=request.user)
        org_id = request.query_params.get('org_id')
        workspace = Workspace.objects.filter(user__in=[user], fyle_org_id=org_id).all()

        return Response(
            data=WorkspaceSerializer(workspace, many=True).data,
            status=status.HTTP_200_OK
        )

    def get_by_id(self, request, **kwargs):
        """
        Get Workspace by id
        """
        try:
            user = User.objects.get(user_id=request.user)
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'], user=user)

            return Response(
                data=WorkspaceSerializer(workspace).data if workspace else {},
                status=status.HTTP_200_OK
            )
        except Workspace.DoesNotExist:
            return Response(
                data={
                    'message': 'Workspace with this id does not exist'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ConnectFyleView(viewsets.ViewSet):
    """
    Fyle Connect Oauth View
    """
    def post(self, request, **kwargs):
        """
        Post of Fyle Credentials
        """
        try:
            authorization_code = request.data.get('code')

            workspace = Workspace.objects.get(id=kwargs['workspace_id'])

            refresh_token = auth_utils.generate_fyle_refresh_token(authorization_code)['refresh_token']
            fyle_user = auth_utils.get_fyle_user(refresh_token)
            org_id = fyle_user['org_id']
            org_name = fyle_user['org_name']

            assert_valid(workspace.fyle_org_id and workspace.fyle_org_id == org_id,
                         'Please select the correct Fyle account - {0}'.format(workspace.name))

            workspace.name = org_name
            workspace.fyle_org_id = org_id
            workspace.save()

            fyle_credentials, _ = FyleCredential.objects.update_or_create(
                workspace_id=kwargs['workspace_id'],
                defaults={
                    'refresh_token': refresh_token,
                }
            )

            return Response(
                data=FyleCredentialSerializer(fyle_credentials).data,
                status=status.HTTP_200_OK
            )
        except fyle_exc.UnauthorizedClientError:
            return Response(
                {
                    'message': 'Invalid Authorization Code'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        except fyle_exc.NotFoundClientError:
            return Response(
                {
                    'message': 'Fyle Application not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except fyle_exc.WrongParamsError:
            return Response(
                {
                    'message': 'Some of the parameters are wrong'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except fyle_exc.InternalServerError:
            return Response(
                {
                    'message': 'Wrong/Expired Authorization code'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

    def delete(self, request, **kwargs):
        """Delete credentials"""
        workspace_id = kwargs['workspace_id']
        FyleCredential.objects.filter(workspace_id=workspace_id).delete()

        return Response(data={
            'workspace_id': workspace_id,
            'message': 'Fyle credentials deleted'
        })

    def get(self, request, **kwargs):
        """
        Get Fyle Credentials in Workspace
        """
        try:
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])
            fyle_credentials = FyleCredential.objects.get(workspace=workspace)

            if fyle_credentials:
                return Response(
                    data=FyleCredentialSerializer(fyle_credentials).data,
                    status=status.HTTP_200_OK
                )
        except FyleCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Fyle Credentials not found in this workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ConnectSageIntacctView(viewsets.ViewSet):
    """
    Sage Intacct Connect View
    """
    def get_or_create_attachments_folder(self, sage_intacct_connection):
        """
        Get or Create attachments folder in Sage Intacct
        """
        attachment_folder = sage_intacct_connection.attachments.get_folder(field='name', value='FyleAttachments')
        if attachment_folder['listtype'] == 'supdocfolder':
            data = {
                'supdocfoldername': 'FyleAttachments'
            }
            sage_intacct_connection.attachments.create_attachments_folder(data)

    def post(self, request, **kwargs):
        """
        Post of Sage Intacct Credentials
        """
        try:
            si_user_id = request.data.get('si_user_id')
            si_company_id = request.data.get('si_company_id')
            si_company_name = request.data.get('si_company_name')
            si_user_password = request.data.get('si_user_password')
            workspace_id = kwargs['workspace_id']
            workspace = Workspace.objects.get(pk=workspace_id)

            sage_intacct_credentials = SageIntacctCredential.objects.filter(workspace=workspace).first()
            sender_id = settings.SI_SENDER_ID
            sender_password = settings.SI_SENDER_PASSWORD
            encryption_key = settings.ENCRYPTION_KEY

            cipher_suite = Fernet(encryption_key)
            encrypted_password = cipher_suite.encrypt(str.encode(si_user_password)).decode('utf-8')

            if not sage_intacct_credentials:
                sage_intacct_connection = SageIntacctSDK(
                    sender_id=sender_id,
                    sender_password=sender_password,
                    user_id=si_user_id,
                    company_id=si_company_id,
                    user_password=si_user_password
                )

                self.get_or_create_attachments_folder(sage_intacct_connection)

                sage_intacct_credentials = SageIntacctCredential.objects.create(
                    si_user_id=si_user_id,
                    si_company_id=si_company_id,
                    si_company_name=si_company_name,
                    si_user_password=encrypted_password,
                    workspace=workspace
                )
            else:
                SageIntacctSDK(
                    sender_id=sender_id,
                    sender_password=sender_password,
                    user_id=si_user_id,
                    company_id=si_company_id,
                    user_password=si_user_password
                )
                sage_intacct_credentials.si_user_id = si_user_id
                sage_intacct_credentials.si_company_id = si_company_id
                sage_intacct_credentials.si_company_name = si_company_name
                sage_intacct_credentials.si_user_password = encrypted_password

                sage_intacct_credentials.save()

            return Response(
                data=SageIntacctCredentialSerializer(sage_intacct_credentials).data,
                status=status.HTTP_200_OK
            )
        except sage_intacct_exc.InvalidTokenError:
            return Response(
                {
                    'message': 'Invalid token / Incorrect credentials'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        except sage_intacct_exc.NotFoundItemError:
            return Response(
                {
                    'message': 'Sage Intacct Application not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except sage_intacct_exc.WrongParamsError as e:
            return Response(
                {
                    'message': e.response
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except sage_intacct_exc.InternalServerError:
            return Response(
                {
                    'message': 'Wrong/Expired Authorization code'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

    def delete(self, request, **kwargs):
        """
        Delete credentials
        """
        workspace_id = kwargs['workspace_id']
        SageIntacctCredential.objects.filter(workspace_id=workspace_id).delete()

        return Response(data={
            'workspace_id': workspace_id,
            'message': 'Sage Intacct credentials deleted'
        })

    def get(self, request, **kwargs):
        """
        Get Sage Intacct Credentials in Workspace
        """
        try:
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace=workspace)

            return Response(
                data=SageIntacctCredentialSerializer(sage_intacct_credentials).data,
                status=status.HTTP_200_OK
            )
        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct Credentials not found in this workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ReadyView(viewsets.ViewSet):
    """
    Ready call
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        """
        Ready call
        """

        Workspace.objects.raw('Select 1 from workspaces')

        return Response(
            data={
                'message': 'Ready'
            },
            status=status.HTTP_200_OK
        )


class GeneralSettingsView(viewsets.ViewSet):
    """
    General Settings
    """
    serializer_class = WorkSpaceGeneralSettingsSerializer
    queryset = WorkspaceGeneralSettings.objects.all()

    def post(self, request, *args, **kwargs):
        """
        Post workspace general settings
        """
        general_settings_payload = request.data

        assert_valid(general_settings_payload is not None, 'Request body is empty')

        workspace_id = kwargs['workspace_id']

        general_settings = create_or_update_general_settings(general_settings_payload, workspace_id)
        return Response(
            data=self.serializer_class(general_settings).data,
            status=status.HTTP_200_OK
        )

    def get(self, request, *args, **kwargs):
        """
        Get workspace general settings
        """
        try:
            general_settings = self.queryset.get(workspace_id=kwargs['workspace_id'])
            return Response(
                data=self.serializer_class(general_settings).data,
                status=status.HTTP_200_OK
            )
        except WorkspaceGeneralSettings.DoesNotExist:
            return Response(
                {
                    'message': 'General Settings does not exist in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ScheduleView(viewsets.ViewSet):
    """
    Schedule View
    """
    def post(self, request, **kwargs):
        """
        Post Settings
        """
        schedule_enabled = request.data.get('schedule_enabled')
        assert_valid(schedule_enabled is not None, 'Schedule enabled cannot be null')

        hours = request.data.get('hours')
        assert_valid(hours is not None, 'Hours cannot be left empty')

        next_run = request.data.get('next_run')
        assert_valid(next_run is not None, 'next_run value cannot be empty')

        schedule_settings = schedule_sync(
            workspace_id=kwargs['workspace_id'],
            schedule_enabled=schedule_enabled,
            hours=hours,
            next_run=next_run
        )

        return Response(
            data=WorkspaceScheduleSerializer(schedule_settings).data,
            status=status.HTTP_200_OK
        )

    def get(self, *args, **kwargs):
        try:
            schedule = WorkspaceSchedule.objects.get(workspace_id=kwargs['workspace_id'])

            return Response(
                data=WorkspaceScheduleSerializer(schedule).data,
                status=status.HTTP_200_OK
            )
        except WorkspaceSchedule.DoesNotExist:
            return Response(
                data={
                    'message': 'Schedule settings does not exist in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
