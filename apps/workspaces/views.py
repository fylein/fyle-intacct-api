from cryptography.fernet import Fernet
from datetime import timedelta

from django.db.models import Q, QuerySet
from django.conf import settings
from django.core.cache import cache
from django_q.tasks import async_task
from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework import generics
from rest_framework.views import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from sageintacctsdk import SageIntacctSDK, exceptions as sage_intacct_exc

from fyle.platform import exceptions as fyle_exc
from fyle_rest_auth.utils import AuthUtils
from fyle_rest_auth.models import AuthToken
from fyle_rest_auth.helpers import get_fyle_admin
from fyle_accounting_mappings.models import ExpenseAttribute
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from fyle_intacct_api.utils import assert_valid, invalidate_intacct_credentials
from apps.sage_intacct.utils import SageIntacctConnector
from apps.sage_intacct.helpers import patch_integration_settings

from apps.fyle.models import ExpenseGroupSettings
from apps.fyle.helpers import get_cluster_domain
from apps.tasks.models import TaskLog
from apps.workspaces.actions import export_to_intacct
from apps.workspaces.models import (
    Workspace,
    Configuration,
    FyleCredential,
    LastExportDetail,
    SageIntacctCredential
)
from apps.workspaces.serializers import (
    WorkspaceSerializer,
    ConfigurationSerializer,
    FyleCredentialSerializer,
    LastExportDetailSerializer,
    SageIntacctCredentialSerializer,
)

User = get_user_model()
auth_utils = AuthUtils()


class TokenHealthView(viewsets.ViewSet):
    """
    Sage Intacct Connect View
    """

    def get(self, request: Request, **kwargs) -> Response:
        status_code = status.HTTP_200_OK
        message = "Intacct connection is active"

        workspace_id = kwargs['workspace_id']
        sage_intacct_credentials = SageIntacctCredential.objects.filter(workspace=workspace_id).first()

        if not sage_intacct_credentials:
            status_code = status.HTTP_400_BAD_REQUEST
            message = "Intacct credentials not found"
        elif sage_intacct_credentials.is_expired:
            status_code = status.HTTP_400_BAD_REQUEST
            message = "Intacct connection expired"
        else:
            try:
                cache_key = f'HEALTH_CHECK_CACHE_{workspace_id}'
                is_healthy = cache.get(cache_key)

                if is_healthy is None:
                    sage_intacct_connection = SageIntacctConnector(credentials_object=sage_intacct_credentials, workspace_id=workspace_id)
                    sage_intacct_connection.connection.locations.count()
                    cache.set(cache_key, True, timeout=timedelta(hours=24).total_seconds())
            except Exception:
                invalidate_intacct_credentials(workspace_id, sage_intacct_credentials)
                status_code = status.HTTP_400_BAD_REQUEST
                message = "Intacct connection expired"

        return Response({"message": message}, status=status_code)


class WorkspaceView(viewsets.ViewSet):
    """
    Sage Intacct Workspace
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Create a Workspace
        """
        access_token = request.META.get('HTTP_AUTHORIZATION')
        fyle_user = get_fyle_admin(access_token.split(' ')[1], None)
        org_name = fyle_user['data']['org']['name']
        org_id = fyle_user['data']['org']['id']

        workspace = Workspace.objects.filter(fyle_org_id=org_id).first()

        if workspace:
            workspace.user.add(User.objects.get(user_id=request.user))
            workspace.name = org_name
            workspace.save()
            cache.delete(str(workspace.id))
        else:
            auth_tokens = AuthToken.objects.get(user__user_id=request.user)
            cluster_domain = get_cluster_domain(auth_tokens.refresh_token)

            workspace = Workspace.objects.create(name=org_name, fyle_org_id=org_id, cluster_domain=cluster_domain)
            ExpenseGroupSettings.objects.create(workspace_id=workspace.id)

            LastExportDetail.objects.create(workspace_id=workspace.id)

            workspace.user.add(User.objects.get(user_id=request.user))

            FyleCredential.objects.update_or_create(
                refresh_token=auth_tokens.refresh_token,
                workspace_id=workspace.id,
                cluster_domain=cluster_domain
            )

        return Response(
            data=WorkspaceSerializer(workspace).data,
            status=status.HTTP_200_OK
        )

    def get(self, request: Request) -> Response:
        """
        Get workspace
        """
        user = User.objects.get(user_id=request.user)
        org_id = request.query_params.get('org_id')
        is_polling = request.query_params.get('is_polling', False)
        workspaces = Workspace.objects.filter(user__in=[user], fyle_org_id=org_id).all()

        if workspaces and not is_polling:
            async_task(
                'apps.workspaces.tasks.async_update_workspace_name',
                workspaces[0],
                request.META.get('HTTP_AUTHORIZATION'),
                q_options={'cluster': 'import'}
            )
        return Response(
            data=WorkspaceSerializer(workspaces, many=True).data,
            status=status.HTTP_200_OK
        )

    def get_by_id(self, request: Request, **kwargs) -> Response:
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

    def patch(self, request: Request, **kwargs) -> Response:
        """
        PATCH workspace
        """
        workspace_instance = Workspace.objects.get(pk=kwargs['workspace_id'])
        serializer = WorkspaceSerializer(
            workspace_instance, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )


class ConnectFyleView(viewsets.ViewSet):
    """
    Fyle Connect Oauth View
    """
    def post(self, request: Request, **kwargs) -> Response:
        """
        Post of Fyle Credentials
        """
        try:
            authorization_code = request.data.get('code')

            workspace = Workspace.objects.get(id=kwargs['workspace_id'])

            tokens = auth_utils.generate_fyle_refresh_token(authorization_code)
            refresh_token = tokens['refresh_token']
            fyle_user = get_fyle_admin(tokens['access_token'], None)
            org_name = fyle_user['data']['org']['name']
            org_id = fyle_user['data']['org']['id']

            assert_valid(workspace.fyle_org_id and workspace.fyle_org_id == org_id,
                         'Please select the correct Fyle account - {0}'.format(workspace.name))

            workspace.name = org_name
            workspace.fyle_org_id = org_id
            workspace.save()

            cluster_domain = get_cluster_domain(refresh_token)

            fyle_credentials, _ = FyleCredential.objects.update_or_create(
                workspace_id=kwargs['workspace_id'],
                defaults={
                    'refresh_token': refresh_token,
                    'cluster_domain': cluster_domain
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

    def delete(self, request: Request, **kwargs) -> Response:
        """
        Delete credentials
        """
        workspace_id = kwargs['workspace_id']
        FyleCredential.objects.filter(workspace_id=workspace_id).delete()

        return Response(data={
            'workspace_id': workspace_id,
            'message': 'Fyle credentials deleted'
        })

    def get(self, request: Request, **kwargs) -> Response:
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
    def get_or_create_attachments_folder(self, sage_intacct_connection: SageIntacctSDK) -> None:
        """
        Get or Create attachments folder in Sage Intacct
        """
        attachment_folder = sage_intacct_connection.attachments.get_folder(field='name', value='FyleAttachments')
        if attachment_folder['listtype'] == 'supdocfolder':
            data = {
                'supdocfoldername': 'FyleAttachments'
            }
            sage_intacct_connection.attachments.create_attachments_folder(data)

    def post(self, request: Request, **kwargs) -> Response:
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
                workspace.onboarding_state = 'LOCATION_ENTITY_MAPPINGS'
                workspace.save()
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
                sage_intacct_credentials.is_expired = False
                patch_integration_settings(workspace, is_token_expired=False)
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

    def delete(self, request: Request, **kwargs) -> Response:
        """
        Delete credentials
        """
        workspace_id = kwargs['workspace_id']
        SageIntacctCredential.objects.filter(workspace_id=workspace_id).delete()

        return Response(data={
            'workspace_id': workspace_id,
            'message': 'Sage Intacct credentials deleted'
        })

    def get(self, request: Request, **kwargs) -> Response:
        """
        Get Sage Intacct Credentials in Workspace
        """
        try:
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])
            sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace.id)

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

    def get(self, request: Request) -> Response:
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


class ConfigurationsView(generics.ListCreateAPIView):
    """
    General Settings
    """
    serializer_class = ConfigurationSerializer
    queryset = Configuration.objects.all()

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get workspace general settings
        """
        try:
            configuration = self.queryset.get(workspace_id=kwargs['workspace_id'])
            return Response(
                data=self.serializer_class(configuration).data,
                status=status.HTTP_200_OK
            )
        except Configuration.DoesNotExist:
            return Response(
                {
                    'message': 'General Settings does not exist in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request: Request, **kwargs) -> Response:
        """
        PATCH workspace configuration settings
        """
        configurations_object = Configuration.objects.get(workspace_id=kwargs['workspace_id'])
        serializer = ConfigurationSerializer(
            configurations_object, data=request.data, partial=True
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )


class WorkspaceAdminsView(viewsets.ViewSet):
    """
    Workspace Admins View
    """
    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get Admins for the workspaces
        """
        workspace = Workspace.objects.get(pk=kwargs['workspace_id'])

        admin_email = []
        users = workspace.user.all()
        for user in users:
            admin = User.objects.get(user_id=user)
            employee = ExpenseAttribute.objects.filter(value=admin.email, workspace_id=kwargs['workspace_id'], attribute_type='EMPLOYEE').first()
            if employee:
                admin_email.append({'name': employee.detail['full_name'], 'email': admin.email})

        return Response(
            data=admin_email,
            status=status.HTTP_200_OK
        )


class LastExportDetailView(generics.RetrieveAPIView):
    """
    Last Export Details
    """
    lookup_field = 'workspace_id'
    lookup_url_kwarg = 'workspace_id'

    queryset = LastExportDetail.objects.filter(last_exported_at__isnull=False, total_expense_groups_count__gt=0)
    serializer_class = LastExportDetailSerializer

    def get_queryset(self) -> QuerySet[LastExportDetail]:
        return super().get_queryset()

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response_data = serializer.data

        start_date = request.query_params.get('start_date')

        if start_date and response_data:
            misc_task_log_types = ['CREATING_REIMBURSEMENT', 'CREATING_AP_PAYMENT', 'FETCHING_EXPENSES']

            task_logs = TaskLog.objects.filter(
                ~Q(type__in=misc_task_log_types),
                workspace_id=kwargs['workspace_id'],
                updated_at__gte=start_date,
                status='COMPLETE',
            ).order_by('-updated_at')

            successful_count = task_logs.count()

            failed_count = TaskLog.objects.filter(
                ~Q(type__in=misc_task_log_types),
                status__in=['FAILED', 'FATAL'],
                workspace_id=kwargs['workspace_id'],
            ).count()

            response_data.update({
                'repurposed_successful_count': successful_count,
                'repurposed_failed_count': failed_count,
                'repurposed_last_exported_at': task_logs.last().updated_at if task_logs.last() else None
            })

        return Response(response_data)


class ExportToIntacctView(viewsets.ViewSet):
    """
    Export Expenses to Intacct
    """
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Export to Intacct
        """
        export_to_intacct(workspace_id=kwargs['workspace_id'], triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC)

        return Response(
            status=status.HTTP_200_OK
        )
