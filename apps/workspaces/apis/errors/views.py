from rest_framework import generics

from apps.tasks.models import Error
from apps.workspaces.apis.errors.serializers import ErrorSerializer


class ErrorsView(generics.ListAPIView):
    """
    List all errors in a workspace
    """
    serializer_class = ErrorSerializer
    pagination_class = None

    def get_queryset(self) -> Error:
        """
        Get all errors in a workspace
        :return: QuerySet
        """
        type = self.request.query_params.get('type')
        is_resolved = self.request.query_params.get('is_resolved', None)

        params = {
            'workspace__id': self.kwargs.get('workspace_id')
        }

        if type:
            params['type'] = type

        if is_resolved is not None:
            params['is_resolved'] = False

        return Error.objects.filter(**params)
