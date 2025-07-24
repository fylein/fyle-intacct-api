import logging
import traceback

from django.db import connection, transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.internal.actions import delete_integration_record, get_accounting_fields, get_exported_entry
from apps.internal.serializers import E2EDestroySerializer, E2ESetupSerializer
from apps.internal.services.e2e_setup import E2ESetupService
from apps.workspaces.models import Workspace
from apps.workspaces.permissions import IsAuthenticatedForInternalAPI
from fyle_intacct_api.utils import assert_valid

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
            "workspace_id": 123
        }
        """
        # Validate request data using serializer, and return 400 / 403 if it fails
        serializer = E2ESetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            # Initialize setup service
            setup_service = E2ESetupService(
                validated_data['workspace_id'],
                validated_data['use_real_intacct_credentials']
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
            "workspace_id": 123
        }
        """
        # Validate request data using serializer, and return 400 / 403 if it fails
        serializer = E2EDestroySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace_id = serializer.validated_data['workspace_id']

        try:
            workspace = Workspace.objects.get(id=workspace_id)

            logger.info(f"Safety check passed for workspace: {workspace.name} (ID: {workspace.id})")

            # Step 1: Clean up from integration settings service
            integration_cleanup_result = delete_integration_record(workspace.id)

            # Step 2: Execute database cleanup function
            deleted_at = timezone.now()
            with transaction.atomic():
                with connection.cursor() as cursor:
                    logger.info(f"Calling delete_workspace({workspace_id}) database function")
                    cursor.execute("SELECT delete_workspace(%s)", [workspace_id])
                    result = cursor.fetchone()
                    logger.info(f"Database cleanup function completed. Result: {result}")

            logger.info(f"E2E cleanup completed successfully for workspace_id: {workspace_id}")

            return Response({
                "success": True,
                "message": "Test workspace deleted successfully",
                "data": {
                    "workspace_id": workspace_id,
                    "org_id": workspace.fyle_org_id,
                    "workspace_name": workspace.name,
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
