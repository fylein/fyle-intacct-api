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


class MappingSettingsView(ListCreateAPIView):
    """
    Mapping Settings View
    """
    serializer_class = MappingSettingSerializer

    def get_queryset(self):
        return MappingSetting.objects.filter(workspace_id=self.kwargs['workspace_id'])

    def post(self, request, *args, **kwargs):
        """
        Post mapping settings
        """
        try:
            mapping_settings: List[Dict] = request.data

            assert_valid(mapping_settings != [], 'Mapping settings not found')

            all_mapping_settings = []

            for mapping_setting in mapping_settings:
                if 'is_custom' not in mapping_setting:
                    mapping_setting['source_field'] = mapping_setting['source_field'].upper().replace(' ', '_')
                    all_mapping_settings.append(mapping_setting)

                if 'is_custom' in mapping_setting and 'import_to_fyle' in mapping_setting:
                    if mapping_setting['is_custom']:
                        upload_attributes_to_fyle(
                            workspace_id=self.kwargs['workspace_id'],
                            sageintacct_attribute_type=mapping_setting['destination_field'],
                            fyle_attribute_type=mapping_setting['source_field'],
                        )

                    mapping_setting['source_field'] = mapping_setting['source_field'].upper().replace(' ', '_')

                    schedule_fyle_attributes_creation(
                        workspace_id=self.kwargs['workspace_id'],
                        sageintacct_attribute_type=mapping_setting['destination_field'],
                        fyle_attribute_type=mapping_setting['source_field'],
                        import_to_fyle=mapping_setting['import_to_fyle'],
                    )

                    all_mapping_settings.append(mapping_setting)

                    if mapping_setting['destination_field'] in ['PROJECT'] and \
                            mapping_setting['import_to_fyle'] is False:
                        schedule: Schedule = Schedule.objects.filter(
                            func='apps.mappings.tasks.auto_create_project_mappings',
                            args=(self.kwargs['workspace_id']),
                        ).first()

                        if schedule:
                            schedule.delete()
                            general_settings = Configuration.objects.get(
                                workspace_id=self.kwargs['workspace_id']
                            )
                            general_settings.import_projects = False
                            general_settings.save()

            mapping_settings = MappingSetting.bulk_upsert_mapping_setting(
                all_mapping_settings, self.kwargs['workspace_id']
            )

            return Response(data=self.serializer_class(mapping_settings, many=True).data, status=status.HTTP_200_OK)

        except BulkError as exception:
            logger.error(exception.response)
            return Response(
                data=exception.response,
                status=status.HTTP_400_BAD_REQUEST
            )
