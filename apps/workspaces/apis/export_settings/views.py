from rest_framework import generics

from apps.workspaces.models import Workspace
from apps.workspaces.apis.export_settings.serializers import ExportSettingsSerializer


class ExportSettingsView(generics.RetrieveUpdateAPIView):
    """
    API endpoint that allows export settings to be viewed or edited.
    """
    serializer_class = ExportSettingsSerializer

    def get_object(self) -> Workspace:
        """
        Get the workspace object.
        """
        return Workspace.objects.filter(id=self.kwargs['workspace_id']).first()

    def get_serializer_context(self) -> dict:
        """
        Override to include the request in the serializer context.
        This allows serializers to access the current user.
        """
        context = super().get_serializer_context()
        context['request'] = self.request

        return context
