from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from django.db.models import Q, QuerySet
from django_q.tasks import async_task
from django_filters.rest_framework import DjangoFilterBackend

from fyle.platform.exceptions import PlatformError
from fyle_integrations_platform_connector import PlatformConnector
from fyle_accounting_mappings.models import ExpenseAttribute
from fyle_accounting_mappings.serializers import ExpenseAttributeSerializer
from fyle_accounting_library.common_resources.models import DimensionDetail
from fyle_accounting_library.common_resources.enums import DimensionDetailSourceTypeEnum
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from fyle_intacct_api.utils import LookupFieldMixin

from apps.tasks.models import TaskLog
from apps.exceptions import handle_view_exceptions
from apps.fyle.queue import async_import_and_export_expenses
from apps.fyle.helpers import ExpenseSearchFilter, ExpenseGroupSearchFilter
from apps.fyle.constants import DEFAULT_FYLE_CONDITIONS

from apps.workspaces.models import (
    Workspace,
    FyleCredential,
    Configuration
)
from apps.fyle.tasks import (
    create_expense_groups,
    get_task_log_and_fund_source,
    schedule_expense_group_creation
)
from apps.fyle.models import (
    Expense,
    ExpenseFilter,
    ExpenseGroup,
    ExpenseGroupSettings,
    DependentFieldSetting
)
from apps.fyle.serializers import (
    ExpenseSerializer,
    ExpenseFieldSerializer,
    ExpenseGroupSerializer,
    ExpenseFilterSerializer,
    ExpenseGroupExpenseSerializer,
    ExpenseGroupSettingsSerializer,
    DependentFieldSettingSerializer
)


class ExpenseGroupView(LookupFieldMixin, generics.ListCreateAPIView):
    """
    List Fyle Expenses
    """
    queryset = ExpenseGroup.objects.all().order_by("-updated_at").distinct()
    serializer_class = ExpenseGroupSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ExpenseGroupSearchFilter

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Create expense groups
        """
        task_log = TaskLog.objects.get(pk=request.data.get('task_log_id'))
        configuration = Configuration.objects.get(workspace_id=kwargs['workspace_id'])

        fund_source = []
        if configuration.reimbursable_expenses_object:
            fund_source.append('PERSONAL')
        if configuration.corporate_credit_card_expenses_object:
            fund_source.append('CCC')

        create_expense_groups(
            kwargs['workspace_id'],
            fund_source=fund_source,
            task_log=task_log,
            imported_from=ExpenseImportSourceEnum.DASHBOARD_SYNC
        )

        return Response(
            status=status.HTTP_200_OK
        )


class ExpenseGroupCountView(generics.ListAPIView):
    """
    Expense Group Count View
    """

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get expense group count
        """
        state_filter = {
            'tasklog__status': self.request.query_params.get('state')
        }
        expense_groups_count = ExpenseGroup.objects.filter(
            workspace_id=kwargs['workspace_id'], **state_filter
        ).count()

        return Response(
            data={'count': expense_groups_count},
            status=status.HTTP_200_OK
        )


class ExpenseGroupScheduleView(generics.CreateAPIView):
    """
    Create expense group schedule
    """

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Post expense schedule
        """
        schedule_expense_group_creation(kwargs['workspace_id'])

        return Response(
            status=status.HTTP_200_OK
        )


class ExpenseGroupByIdView(generics.RetrieveAPIView):
    """
    Expense Group by Id view
    """
    serializer_class = ExpenseGroupSerializer
    queryset = ExpenseGroup.objects.all()


class ExpenseGroupExpenseView(generics.RetrieveAPIView):
    """
    Expense view
    """
    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get expenses
        """
        try:
            expense_group = ExpenseGroup.objects.get(
                workspace_id=kwargs['workspace_id'], pk=kwargs['expense_group_id']
            )
            expenses = Expense.objects.filter(
                id__in=expense_group.expenses.values_list('id', flat=True)).order_by('-updated_at')
            return Response(
                data=ExpenseGroupExpenseSerializer(expenses, many=True).data,
                status=status.HTTP_200_OK
            )

        except ExpenseGroup.DoesNotExist:
            return Response(
                data={
                    'message': 'Expense group not found'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class EmployeeView(generics.ListCreateAPIView):
    """
    Employee view
    """

    serializer_class = ExpenseAttributeSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        """
        Get queryset for employee
        """
        return ExpenseAttribute.objects.filter(
            attribute_type='EMPLOYEE', workspace_id=self.kwargs['workspace_id']).order_by('value')


class CategoryView(generics.ListCreateAPIView):
    """
    Category view
    """
    serializer_class = ExpenseAttributeSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        """
        Get queryset for category
        """
        return ExpenseAttribute.objects.filter(
            attribute_type='CATEGORY', workspace_id=self.kwargs['workspace_id']).order_by('value')


class ProjectView(generics.ListCreateAPIView):
    """
    Project view
    """
    serializer_class = ExpenseAttributeSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        """
        Get queryset for project
        """
        return ExpenseAttribute.objects.filter(
            attribute_type='PROJECT', workspace_id=self.kwargs['workspace_id']).order_by('value')


class CostCenterView(generics.ListCreateAPIView):
    """
    Cost Center view
    """

    serializer_class = ExpenseAttributeSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        """
        Get queryset for cost center
        """
        return ExpenseAttribute.objects.filter(
            attribute_type='COST_CENTER', workspace_id=self.kwargs['workspace_id']).order_by('value')


class ExpenseGroupSettingsView(generics.ListCreateAPIView):
    """
    Expense Group Settings View
    """
    serializer_class = ExpenseGroupSettingsSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get Expense Group Settings
        """
        expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=self.kwargs['workspace_id'])

        return Response(
            data=self.serializer_class(expense_group_settings).data,
            status=status.HTTP_200_OK
        )

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Update Expense Group Settings
        """
        expense_group_settings, _ = ExpenseGroupSettings.update_expense_group_settings(
            request.data, self.kwargs['workspace_id'], request.user)
        return Response(
            data=self.serializer_class(expense_group_settings).data,
            status=status.HTTP_200_OK
        )


class ExpenseAttributesView(generics.ListAPIView):
    """
    Expense Attributes view
    """
    serializer_class = ExpenseAttributeSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        """
        Get queryset
        """
        active = self.request.query_params.get('active')

        params = {
            'workspace_id': self.kwargs['workspace_id'],
            'attribute_type': self.request.query_params.get('attribute_type')
        }

        if active and active.lower() == 'true':
            params['active'] = True

        return ExpenseAttribute.objects.filter(**params).order_by('value')


class FyleFieldsView(generics.ListAPIView):
    """
    Fyle Fields view
    """
    pagination_class = None
    serializer_class = ExpenseFieldSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get Fyle Fields
        """
        default_attributes = ['EMPLOYEE', 'CATEGORY', 'PROJECT', 'COST_CENTER', 'LOCATION_ENTITY', 'TAX_GROUP', 'CORPORATE_CARD', 'MERCHANT']

        fields = ExpenseAttribute.objects.filter(
            ~Q(attribute_type__in=default_attributes),
            workspace_id=self.kwargs['workspace_id'],
            detail__is_dependent=False
        ).values('attribute_type', 'display_name').distinct()

        dependent_fields = ExpenseAttribute.objects.filter(
            ~Q(attribute_type__in=default_attributes),
            workspace_id=self.kwargs['workspace_id'],
            detail__is_dependent=True
        ).values('attribute_type', 'display_name').distinct()

        dimensions = DimensionDetail.objects.filter(workspace_id=self.kwargs['workspace_id'], source_type=DimensionDetailSourceTypeEnum.FYLE.value).values(
            'attribute_type', 'display_name'
        )

        cost_center_display_name = dimensions.get(attribute_type='COST_CENTER')['display_name'] if dimensions.filter(attribute_type='COST_CENTER').exists() else 'Cost Center'
        project_display_name = dimensions.get(attribute_type='PROJECT')['display_name'] if dimensions.filter(attribute_type='PROJECT').exists() else 'Project'

        expense_fields = [{
            'attribute_type': 'COST_CENTER', 'display_name': cost_center_display_name, 'is_dependent': False
        },{
            'attribute_type': 'PROJECT', 'display_name': project_display_name, 'is_dependent': False
        }]

        for attribute in fields:
            attribute['is_dependent'] = False
            expense_fields.append(attribute)

        for attribute in dependent_fields:
            attribute['is_dependent'] = True
            expense_fields.append(attribute)

        return Response(
            expense_fields,
            status=status.HTTP_200_OK
        )


class SyncFyleDimensionView(generics.ListCreateAPIView):
    """
    Sync Fyle Dimensions view
    """
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Sync data from Fyle
        """
        try:
            # check if fyle credentials are present, and return 400 otherwise
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])
            FyleCredential.objects.get(workspace_id=workspace.id)

            async_task(
                'apps.fyle.helpers.check_interval_and_sync_dimension',
                kwargs['workspace_id']
            )

            return Response(
                status=status.HTTP_200_OK
            )
        except FyleCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Fyle credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except PlatformError:
            return Response(
                data={
                    'message': 'Something wrong with PlatformConnector'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class RefreshFyleDimensionView(generics.ListCreateAPIView):
    """
    Refresh Fyle Dimensions view
    """
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Sync data from Fyle
        """
        try:
            # check if fyle credentials are present, and return 400 otherwise
            workspace = Workspace.objects.get(id=kwargs['workspace_id'])
            FyleCredential.objects.get(workspace_id=workspace.id)

            async_task('apps.fyle.helpers.handle_refresh_dimensions', kwargs['workspace_id'])

            return Response(
                status=status.HTTP_200_OK
            )
        except FyleCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Fyle credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except PlatformError:
            return Response(
                data={
                    'message': 'Something wrong with PlatformConnector'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ExpenseFilterView(generics.ListCreateAPIView, generics.DestroyAPIView):
    """
    Expense Filter view
    """
    serializer_class = ExpenseFilterSerializer

    def get_queryset(self) -> QuerySet:
        """
        Get Expense Filter queryset
        """
        queryset = ExpenseFilter.objects.filter(workspace_id=self.kwargs['workspace_id']).order_by('rank')
        return queryset

    def delete(self, request: Request, *args, **kwargs) -> Response:
        """
        Delete Expense Filter
        """
        workspace_id = self.kwargs['workspace_id']
        rank = request.data.get('rank')
        ExpenseFilter.objects.filter(workspace_id=workspace_id, rank=rank).delete()

        return Response(data={
            'workspace_id': workspace_id,
            'rank': rank,
            'message': 'Expense filter deleted'
        })


class ExpenseView(LookupFieldMixin, generics.ListAPIView):
    """
    Expense view
    """

    queryset = Expense.objects.all().order_by("-updated_at").distinct()
    serializer_class = ExpenseSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ExpenseSearchFilter


class CustomFieldView(generics.RetrieveAPIView):
    """
    Custom Field view
    """
    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get Custom Fields
        """
        response = []
        response.extend(DEFAULT_FYLE_CONDITIONS)

        workspace_id = self.kwargs['workspace_id']
        fyle_credentails = FyleCredential.objects.get(workspace_id=workspace_id)
        platform = PlatformConnector(fyle_credentails)
        custom_fields = platform.expense_custom_fields.list_all()

        for custom_field in custom_fields:
            if custom_field['type'] in ('SELECT', 'NUMBER', 'TEXT', 'BOOLEAN'):
                response.append({
                    'field_name': custom_field['field_name'],
                    'type': custom_field['type'],
                    'is_custom': custom_field['is_custom']
                })

        return Response(
            data=response,
            status=status.HTTP_200_OK
        )


class DependentFieldSettingView(generics.CreateAPIView, generics.RetrieveUpdateAPIView):
    """
    Dependent Field view
    """
    serializer_class = DependentFieldSettingSerializer
    lookup_field = 'workspace_id'
    queryset = DependentFieldSetting.objects.all()


class ExportableExpenseGroupsView(generics.RetrieveAPIView):
    """
    List Exportable Expense Groups
    """
    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get exportable expense groups
        """
        configuration = Configuration.objects.get(workspace_id=kwargs['workspace_id'])
        fund_source = []

        if configuration.reimbursable_expenses_object:
            fund_source.append('PERSONAL')
        if configuration.corporate_credit_card_expenses_object:
            fund_source.append('CCC')

        expense_group_ids = ExpenseGroup.objects.filter(
            workspace_id=self.kwargs['workspace_id'],
            exported_at__isnull=True,
            fund_source__in=fund_source
        ).values_list('id', flat=True)

        return Response(
            data={'exportable_expense_group_ids': expense_group_ids},
            status=status.HTTP_200_OK
        )


class ExpenseGroupSyncView(generics.CreateAPIView):
    """
    Create expense groups
    """
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Post expense groups creation
        """
        task_log, fund_source = get_task_log_and_fund_source(kwargs['workspace_id'])

        create_expense_groups(kwargs['workspace_id'], fund_source, task_log, imported_from=ExpenseImportSourceEnum.DASHBOARD_SYNC)

        return Response(
            status=status.HTTP_200_OK
        )


class ExportView(generics.CreateAPIView):
    """
    Export View
    """
    authentication_classes = []
    permission_classes = []

    @handle_view_exceptions()
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Import and Export expenses
        """
        async_import_and_export_expenses(request.data, int(kwargs['workspace_id']))

        return Response(data={}, status=status.HTTP_200_OK)
