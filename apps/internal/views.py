import logging
import traceback

from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from django.db import connection, transaction
from django.utils import timezone

from fyle_intacct_api.utils import assert_valid

from apps.workspaces.permissions import IsAuthenticatedForInternalAPI
from apps.workspaces.models import Workspace

from .services.e2e_setup import E2ESetupService
from .actions import delete_integration_record, get_accounting_fields, get_exported_entry
from .helpers import is_safe_environment
from .serializers import E2ESetupSerializer, E2EDestroySerializer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AccountingFieldsView(generics.GenericAPIView):
    """
    Get accounting fields
    """
    authentication_classes = []
    permission_classes = [IsAuthenticatedForInternalAPI]

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get accounting fields
        """
        try:
            params = request.query_params

            assert_valid(params.get('org_id') is not None, 'Org ID is required')
            assert_valid(params.get('resource_type') is not None, 'Resource Type is required')

            if params.get('resource_type') in ('custom_segments', 'custom_lists', 'custom_record_types'):
                assert_valid(params.get('internal_id') is not None, 'Internal ID is required')

            response = get_accounting_fields(request.query_params)
            return Response(
                data={'data': response},
                status=status.HTTP_200_OK
            )

        except Exception:
            logger.info(f"Error in AccountingFieldsView: {traceback.format_exc()}")
            return Response(
                data={'error': traceback.format_exc()},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExportedEntryView(generics.GenericAPIView):
    """
    Get exported entry
    """
    authentication_classes = []
    permission_classes = [IsAuthenticatedForInternalAPI]

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get exported entry
        """
        try:
            params = request.query_params
            assert_valid(params.get('org_id') is not None, 'Org ID is required')
            assert_valid(params.get('resource_type') is not None, 'Resource Type is required')
            assert_valid(params.get('internal_id') is not None, 'Internal ID is required')

            response = get_exported_entry(request.query_params)

            return Response(
                data={'data': response},
                status=status.HTTP_200_OK
            )

        except Exception:
            logger.info(f"Error in AccountingFieldsView: {traceback.format_exc()}")
            return Response(
                data={'error': traceback.format_exc()},
                status=status.HTTP_400_BAD_REQUEST
            )


class E2ESetupView(generics.GenericAPIView):
    """
    ViewSet for E2E test fixture setup
    """
    authentication_classes = []
    permission_classes = [IsAuthenticatedForInternalAPI]

    def post(self, request: Request) -> Response:
        """
        Set up test organization data for E2E testing

        Expected payload:
        {
            "admin_email": "admin@example.com",
            "user_id": 12345,
            "refresh_token": "sample_token",
            "org_id": "orga1b2c3d4e5f6",
            "cluster_domain": "staging"
        }
        """
        try:
            # Validate environment
            if not is_safe_environment():
                return Response(
                    {"error": "E2E setup endpoint is only available in development/staging environments"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate request data using serializer
            serializer = E2ESetupSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Validation failed", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            # Initialize setup service
            setup_service = E2ESetupService(
                workspace_id=validated_data['workspace_id']
            )

            # Execute setup in transaction
            with transaction.atomic():
                result = setup_service.setup_organization()

            logger.info("E2E setup completed successfully")

            return Response({
                "success": True,
                "message": "Test organization setup completed successfully",
                "data": result
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"E2E setup failed: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Setup failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class E2EDestroyView(generics.GenericAPIView):
    """
    ViewSet for E2E test cleanup/destruction
    """
    authentication_classes = []
    permission_classes = [IsAuthenticatedForInternalAPI]

    def post(self, request: Request) -> Response:
        """
        Destroy test organization data after E2E testing

        Expected payload:
        {
            "org_id": "orga1b2c3d4e5f6"
        }
        """
        try:
            # Validate environment
            if not is_safe_environment():
                return Response(
                    {"error": "E2E destroy endpoint is only available in development/staging environments"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate request data using serializer
            serializer = E2EDestroySerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": "Validation failed", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get validated data and workspace
            org_id = serializer.validated_data['org_id']
            workspace = Workspace.objects.get(fyle_org_id=org_id)

            logger.info(f"Safety check passed for workspace: {workspace.name} (ID: {workspace.id})")

            # Step 1: Clean up from integration settings service
            integration_cleanup_result = delete_integration_record(workspace.id)

            # Step 2: Execute database cleanup function
            workspace_id = workspace.id
            workspace_name = workspace.name
            deleted_at = timezone.now()

            with connection.cursor() as cursor:
                logger.info(f"Calling delete_workspace({workspace_id}) database function")
                cursor.execute("SELECT delete_workspace(%s)", [workspace_id])
                result = cursor.fetchone()
                logger.info(f"Database cleanup function completed. Result: {result}")

            logger.info(f"E2E cleanup completed successfully for org_id: {org_id}")

            return Response({
                "success": True,
                "message": "Test workspace deleted successfully",
                "data": {
                    "workspace_id": workspace_id,
                    "org_id": org_id,
                    "workspace_name": workspace_name,
                    "deleted_at": deleted_at.isoformat(),
                    "cleanup_result": result[0] if result else "Success",
                    "integration_cleanup": integration_cleanup_result
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"E2E cleanup failed: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Cleanup failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
