from rest_framework import generics
from rest_framework.views import Response, status

from apps.workspaces.models import Workspace, Configuration

from .serializers import ImportSettingsSerializer

from apps.mappings.models import ImportLog
from fyle_accounting_mappings.models import MappingSetting


class ImportSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = ImportSettingsSerializer

    def get_object(self):
        return Workspace.objects.filter(id=self.kwargs['workspace_id']).first()

    def get_serializer_context(self):
        """
        Override to include the request in the serializer context.
        This allows serializers to access the current user.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class ImportCodeFieldView(generics.GenericAPIView):
    """
    Import Code Field View
    """
    def get(self, request, *args, **kwargs):
        workspace_id = kwargs['workspace_id']
        import_log_attributes = ImportLog.objects.filter(workspace_id=workspace_id).values_list('attribute_type', flat=True)
        configuration = Configuration.objects.filter(workspace_id=workspace_id).first()

        response_data = {
            'PROJECT': True,
            'DEPARTMENT': True,
            'ACCOUNT': True,
            'EXPENSE_TYPE': True
        }

        mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id).values('destination_field', 'source_field')
        for mapping in mapping_settings:
            if mapping['destination_field'] == 'PROJECT' and mapping['source_field'] in import_log_attributes:
                response_data['PROJECT'] = False
            elif mapping['destination_field'] == 'DEPARTMENT' and mapping['source_field'] in import_log_attributes:
                response_data['DEPARTMENT'] = False

        if configuration:
            if 'ACCOUNT' in configuration.import_code_fields or '_ACCOUNT' in configuration.import_code_fields:
                response_data['ACCOUNT'] = False

            if 'EXPENSE_TYPE' in configuration.import_code_fields or '_EXPENSE_TYPE' in configuration.import_code_fields:
                response_data['EXPENSE_TYPE'] = False

        return Response(
            data=response_data,
            status=status.HTTP_200_OK
        )
