from typing import List, Dict

from rest_framework.generics import ListCreateAPIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import status

from django_q.tasks import Chain
from django_q.models import Schedule

from fyle_accounting_mappings.models import MappingSetting
from fyle_accounting_mappings.views import logger
from fyle_accounting_mappings.exceptions import BulkError
from fyle_accounting_mappings.serializers import MappingSettingSerializer

from fyle_intacct_api.utils import assert_valid
from apps.workspaces.models import WorkspaceGeneralSettings

from .tasks import schedule_fyle_attributes_creation, upload_attributes_to_fyle, schedule_cost_centers_creation
from .serializers import GeneralMappingSerializer
from .models import GeneralMapping
from .utils import MappingUtils


class GeneralMappingView(generics.ListCreateAPIView):
    """
    General mappings
    """
    serializer_class = GeneralMappingSerializer
    queryset = GeneralMapping.objects.all()

    def post(self, request, *args, **kwargs):
        """
        Create general mappings
        """
        general_mapping_payload = request.data

        assert_valid(general_mapping_payload is not None, 'Request body is empty')

        mapping_utils = MappingUtils(kwargs['workspace_id'])

        general_mapping = mapping_utils.create_or_update_general_mapping(general_mapping_payload)

        return Response(
            data=self.serializer_class(general_mapping).data,
            status=status.HTTP_200_OK
        )

    def get(self, request, *args, **kwargs):
        """
        Get general mappings
        """
        try:
            general_mapping = self.queryset.get(workspace_id=kwargs['workspace_id'])
            return Response(
                data=self.serializer_class(general_mapping).data,
                status=status.HTTP_200_OK
            )
        except GeneralMapping.DoesNotExist:
            return Response(
                {
                    'message': 'General mappings do not exist for the workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class AutoMapEmployeeView(generics.CreateAPIView):
    """
    Auto Map Employee view
    """

    def post(self, request, *args, **kwargs):
        """
        Trigger Auto Map Employees
        """
        try:
            workspace_id = kwargs['workspace_id']
            general_settings = WorkspaceGeneralSettings.objects.get(workspace_id=workspace_id)

            chain = Chain()

            if not general_settings.auto_map_employees:
                return Response(
                    data={
                        'message': 'Employee mapping preference not found for this workspace'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            chain.append('apps.mappings.tasks.async_auto_map_employees', workspace_id)

            general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
            if general_mappings.default_charge_card_name:
                chain.append('apps.mappings.tasks.async_auto_map_charge_card_account', workspace_id)

            chain.run()

            return Response(
                data={},
                status=status.HTTP_200_OK
            )

        except GeneralMapping.DoesNotExist:
            return Response(
                {
                    'message': 'General mappings do not exist for this workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
