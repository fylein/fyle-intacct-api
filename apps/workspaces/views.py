import logging
import traceback
from cryptography.fernet import Fernet
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q, QuerySet
from django.contrib.auth import get_user_model

from intacctsdk import IntacctRESTSDK
from sageintacctsdk import SageIntacctSDK
from sageintacctsdk import exceptions as sage_intacct_exc
from intacctsdk.exceptions import (
    BadRequestError as SageIntacctRESTBadRequestError,
    InvalidTokenError as SageIntacctRestInvalidTokenError,
    InternalServerError as SageIntacctRESTInternalServerError
)

from rest_framework.views import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from fyle_rest_auth.models import AuthToken
from fyle_rest_auth.utils import AuthUtils
from fyle.platform import exceptions as fyle_exc
from fyle_rest_auth.helpers import get_fyle_admin
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from fyle_accounting_mappings.models import ExpenseAttribute, FyleSyncTimestamp

from apps.tasks.models import TaskLog
from apps.fyle.helpers import get_cluster_domain
from apps.fyle.models import ExpenseGroupSettings
from apps.workspaces.actions import export_to_intacct
from apps.workspaces.tasks import patch_integration_settings
from apps.sage_intacct.models import SageIntacctAttributesCount
from apps.sage_intacct.helpers import get_sage_intacct_connection
from apps.sage_intacct.enums import SageIntacctRestConnectionTypeEnum
from workers.helpers import RoutingKeyEnum, WorkerActionEnum, publish_to_rabbitmq
from fyle_intacct_api.utils import assert_valid, invalidate_sage_intacct_credentials
from apps.workspaces.models import (
    Workspace,
    Configuration,
    FeatureConfig,
    FyleCredential,
    LastExportDetail,
    SageIntacctCredential,
    IntacctSyncedTimestamp,
)
from apps.workspaces.serializers import (
    WorkspaceSerializer,
    ConfigurationSerializer,
    FeatureConfigSerializer,
    FyleCredentialSerializer,
    LastExportDetailSerializer,
    SageIntacctCredentialSerializer,
)


User = get_user_model()
auth_utils = AuthUtils()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TokenHealthView(viewsets.ViewSet):
    """
    Sage Intacct Connect View
    """

    def get(self, request: Request, **kwargs) -> Response:
        """
        Get token health
        """
        status_code = status.HTTP_200_OK
        message = "Intacct connection is active"

        workspace_id = kwargs['workspace_id']
        sage_intacct_credentials = SageIntacctCredential.objects.filter(workspace=workspace_id).first()

        migrated_to_rest_api = FeatureConfig.get_feature_config(workspace_id=workspace_id, key='migrated_to_rest_api')

        if not sage_intacct_credentials:
            status_code = status.HTTP_400_BAD_REQUEST
            message = "Intacct credentials not found"
        elif not migrated_to_rest_api and sage_intacct_credentials.is_expired:
            status_code = status.HTTP_400_BAD_REQUEST
            message = "Intacct connection expired"
        else:
            try:
                cache_key = f'HEALTH_CHECK_CACHE_{workspace_id}'
                is_healthy = cache.get(cache_key)

                if is_healthy is None:
                    sage_intacct_connection = get_sage_intacct_connection(workspace_id=workspace_id, connection_type=SageIntacctRestConnectionTypeEnum.SYNC.value)
                    sage_intacct_connection.connection.locations.count()
                    cache.set(cache_key, True, timeout=timedelta(hours=24).total_seconds())
            except (sage_intacct_exc.InvalidTokenError, SageIntacctRestInvalidTokenError):
                invalidate_sage_intacct_credentials(workspace_id, sage_intacct_credentials)
                status_code = status.HTTP_400_BAD_REQUEST
                message = "Intacct connection expired"
                logger.info('Invalid Sage Intact Token for workspace_id - %s', workspace_id)
            except (SageIntacctRESTBadRequestError, SageIntacctRESTInternalServerError) as e:
                status_code = status.HTTP_400_BAD_REQUEST
                message = "Sage Intacct REST API error for workspace_id - %s: %s" % (workspace_id, e.response)
                logger.info('Sage Intacct REST API error for workspace_id - %s: %s', workspace_id, e.response)
            except Exception:
                status_code = status.HTTP_400_BAD_REQUEST
                message = "Something went wrong"
                logger.error('Something went wrong for workspace_id - %s %s', workspace_id, traceback.format_exc())

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
            FeatureConfig.objects.create(
                workspace_id=workspace.id,
                migrated_to_rest_api=settings.BRAND_ID == 'fyle',
                import_billable_field_for_projects=settings.BRAND_ID == 'fyle'
            )
            FyleSyncTimestamp.objects.create(workspace_id=workspace.id)
            IntacctSyncedTimestamp.objects.create(workspace_id=workspace.id)
            SageIntacctAttributesCount.objects.create(workspace_id=workspace.id)

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
            payload = {
                'workspace_id': workspaces[0].id,
                'action': WorkerActionEnum.UPDATE_WORKSPACE_NAME.value,
                'data': {
                    'workspace_id': workspaces[0].id,
                    'access_token': request.META.get('HTTP_AUTHORIZATION'),
                }
            }
            publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.UTILITY.value)

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

    def get_or_create_attachments_folder_rest_api(self, sage_intacct_connection: IntacctRESTSDK) -> None:
        """
        Get or Create attachments folder in Sage Intacct
        """
        params = {
            'fields': ['id', 'status'],
            'filters': [
                {
                    '$eq': {
                        'id': 'FyleAttachments'
                    }
                }
            ]
        }
        attachment_folder_generator = sage_intacct_connection.attachment_folders.get_all_generator(**params)

        for attachment_folder in attachment_folder_generator:
            if not attachment_folder:
                return sage_intacct_connection.attachment_folders.post({
                    'id': 'FyleAttachments'
                })

    def post(self, request: Request, **kwargs) -> Response:
        """
        Post of Sage Intacct Credentials
        """
        si_user_id = request.data.get('si_user_id')
        si_company_id = request.data.get('si_company_id')
        si_company_name = request.data.get('si_company_name')
        si_user_password = request.data.get('si_user_password')
        workspace_id = kwargs['workspace_id']
        workspace = Workspace.objects.get(pk=workspace_id)

        migrated_to_rest_api = FeatureConfig.get_feature_config(workspace_id=workspace_id, key='migrated_to_rest_api')

        if migrated_to_rest_api:
            return self.handle_sage_intacct_rest_api_connection(
                workspace=workspace,
                si_user_id=si_user_id,
                si_company_id=si_company_id,
                si_company_name=si_company_name,
            )
        else:
            return self.handle_sage_intacct_soap_api_connection(
                workspace=workspace,
                si_user_id=si_user_id,
                si_company_id=si_company_id,
                si_company_name=si_company_name,
                si_user_password=si_user_password
            )

    def handle_sage_intacct_rest_api_connection(
        self,
        workspace: Workspace,
        si_user_id: str,
        si_company_id: str,
        si_company_name: str
    ) -> Response:
        """
        Handle Sage Intacct REST API connection
        :param workspace: Workspace
        :param si_user_id: Sage Intacct user ID
        :param si_company_id: Sage Intacct company ID
        :param si_company_name: Sage Intacct company name
        :param si_user_password: Sage Intacct user password
        :return: None
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.filter(workspace=workspace).first()

            if not sage_intacct_credentials:
                sage_intacct_connection = IntacctRESTSDK(
                    username=f'{si_user_id}@{si_company_id}',
                    client_id=settings.INTACCT_CLIENT_ID,
                    client_secret=settings.INTACCT_CLIENT_SECRET,
                )

                self.get_or_create_attachments_folder_rest_api(sage_intacct_connection)

                access_token_expires_in = sage_intacct_connection.access_token_expires_in if hasattr(sage_intacct_connection, 'access_token_expires_in') and sage_intacct_connection.access_token_expires_in else 21600
                access_token_hours_remaining = access_token_expires_in / 3600

                sage_intacct_credentials = SageIntacctCredential.objects.create(
                    si_user_id=si_user_id,
                    si_company_id=si_company_id,
                    si_company_name=si_company_name,
                    access_token=sage_intacct_connection.access_token,
                    access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=access_token_hours_remaining - 1),
                    workspace=workspace
                )

                workspace.onboarding_state = 'LOCATION_ENTITY_MAPPINGS'
                workspace.save()

            else:
                sage_intacct_connection = IntacctRESTSDK(
                    username=f'{si_user_id}@{si_company_id}',
                    client_id=settings.INTACCT_CLIENT_ID,
                    client_secret=settings.INTACCT_CLIENT_SECRET,
                    access_token=sage_intacct_credentials.access_token
                )

                self.get_or_create_attachments_folder_rest_api(sage_intacct_connection)

                access_token_expires_in = sage_intacct_connection.access_token_expires_in if hasattr(sage_intacct_connection, 'access_token_expires_in') and sage_intacct_connection.access_token_expires_in else 21600
                access_token_hours_remaining = access_token_expires_in / 3600

                sage_intacct_credentials.si_user_id = si_user_id
                sage_intacct_credentials.si_company_id = si_company_id
                sage_intacct_credentials.si_company_name = si_company_name
                sage_intacct_credentials.is_expired = False
                sage_intacct_credentials.access_token = sage_intacct_connection.access_token
                sage_intacct_credentials.access_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=access_token_hours_remaining - 1)
                sage_intacct_credentials.save()

                patch_integration_settings(workspace, is_token_expired=False)

            return Response(
                data=SageIntacctCredentialSerializer(sage_intacct_credentials).data,
                status=status.HTTP_200_OK
            )

        except SageIntacctRestInvalidTokenError as e:
            logger.info('Something went wrong while connecting to Sage Intacct - %s', e.response)
            return Response(
                {
                    'message': e.response
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctRESTBadRequestError as e:
            logger.info('Something went wrong while connecting to Sage Intacct - %s', e.response)
            return Response(
                {
                    'message': e.response
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except SageIntacctRESTInternalServerError as e:
            logger.info('Something went wrong while connecting to Sage Intacct - %s', e.response)
            return Response(
                {
                    'message': 'Something went wrong while connecting to Sage Intacct'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

    def handle_sage_intacct_soap_api_connection(
        self,
        workspace: Workspace,
        si_user_id: str,
        si_company_id: str,
        si_company_name: str,
        si_user_password: str
    ) -> Response:
        """
        Handle Sage Intacct SOAP API connection
        :param workspace: Workspace
        :param si_user_id: Sage Intacct user ID
        :param si_company_id: Sage Intacct company ID
        :param si_company_name: Sage Intacct company name
        :param si_user_password: Sage Intacct user password
        :return: None
        """
        try:
            sender_id = settings.SI_SENDER_ID
            sender_password = settings.SI_SENDER_PASSWORD
            encryption_key = settings.ENCRYPTION_KEY

            cipher_suite = Fernet(encryption_key)
            encrypted_password = cipher_suite.encrypt(str.encode(si_user_password)).decode('utf-8')
            sage_intacct_credentials = SageIntacctCredential.objects.filter(workspace=workspace).first()

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
        feature_config = FeatureConfig.objects.get(workspace_id=kwargs['workspace_id'])
        if feature_config.export_via_rabbitmq:
            payload = {
                'workspace_id': kwargs['workspace_id'],
                'action': WorkerActionEnum.DASHBOARD_SYNC.value,
                'data': {
                    'workspace_id': kwargs['workspace_id'],
                    'triggered_by': ExpenseImportSourceEnum.DASHBOARD_SYNC,
                    'run_in_rabbitmq_worker': True
                }
            }
            publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.EXPORT_P0.value)
        else:
            export_to_intacct(
                workspace_id=kwargs['workspace_id'],
                triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC
            )

        return Response(
            status=status.HTTP_200_OK
        )


class FeatureConfigView(generics.RetrieveAPIView):
    """
    Get Feature Configs
    """
    lookup_field = 'workspace_id'
    lookup_url_kwarg = 'workspace_id'

    queryset = FeatureConfig.objects.all()
    serializer_class = FeatureConfigSerializer
