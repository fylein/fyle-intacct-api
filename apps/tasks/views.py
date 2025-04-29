from fyle_intacct_api.utils import LookupFieldMixin
from django.db.models import Q

from rest_framework import generics
from rest_framework.views import status
from rest_framework.request import Request
from rest_framework.response import Response

from fyle_intacct_api.utils import assert_valid

from apps.tasks.models import TaskLog
from apps.tasks.serializers import TaskLogSerializer
from django_filters.rest_framework import DjangoFilterBackend


class TasksView(generics.ListAPIView):
    """
    Tasks view
    """
    serializer_class = TaskLogSerializer

    def get_queryset(self) -> TaskLog:
        """
        Return task logs in workspace
        :return: TaskLog
        """
        task_status = self.request.query_params.getlist('status')
        task_type = ['CREATING_AP_PAYMENT', 'CREATING_REIMBURSEMENT']

        if len(task_status) == 1 and task_status[0] == 'ALL':
            task_status = ['ENQUEUED', 'IN_PROGRESS', 'FAILED', 'COMPLETE']

        task_logs = TaskLog.objects.filter(~Q(type__in=task_type),
            workspace_id=self.kwargs['workspace_id'], status__in=task_status).order_by('-updated_at').all()
        return task_logs


class NewTaskView(LookupFieldMixin, generics.ListAPIView):
    """
    Task logs view with filtering capabilities for type, expense_group_id, and status
    """
    queryset = TaskLog.objects.all().order_by('-updated_at')
    serializer_class = TaskLogSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = {'type':{'in'}, 'expense_group_id':{'in'}, 'status': {'in'}}


class TasksByIdView(generics.RetrieveAPIView):
    """
    Get Task by Ids
    """
    serializer_class = TaskLogSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get task logs by ids
        """
        task_log_ids = self.request.query_params.getlist('id', [])

        assert_valid(task_log_ids != [], 'task log ids not found')

        task_logs = TaskLog.objects.filter(id__in=task_log_ids).all()

        return Response(
            data=self.serializer_class(task_logs, many=True).data,
            status=status.HTTP_200_OK
        )


class TasksByExpenseGroupIdView(generics.RetrieveAPIView):
    """
    Get Task by Ids
    """
    serializer_class = TaskLogSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get task logs by ids
        """
        task_log = TaskLog.objects.get(expense_group_id=kwargs['expense_group_id'])

        return Response(
            data=self.serializer_class(task_log).data,
            status=status.HTTP_200_OK
        )
