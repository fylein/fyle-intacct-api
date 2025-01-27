from rest_framework import generics

from apps.workspaces.models import Workspace
from apps.workspaces.apis.advanced_settings.serializers import AdvancedConfigurationsSerializer


class AdvancedConfigurationsView(generics.RetrieveUpdateAPIView):
    """
    AdvancedConfigurationsView
    """
    serializer_class = AdvancedConfigurationsSerializer

    def get_object(self) -> Workspace:
        """
        Get the workspace object
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
