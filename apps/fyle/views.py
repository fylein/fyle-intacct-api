from django.db.models import Q
from datetime import datetime, timezone

from rest_framework.views import status
from rest_framework import generics
from rest_framework.response import Response

from django_q.tasks import Chain

from fyle_accounting_mappings.models import ExpenseAttribute, MappingSetting
from fyle_accounting_mappings.serializers import ExpenseAttributeSerializer
from fyle.platform.exceptions import PlatformError
from apps.fyle.constants import DEFAULT_FYLE_CONDITIONS

from fyle_integrations_platform_connector import PlatformConnector

from apps.workspaces.models import FyleCredential, Configuration, Workspace
from apps.tasks.models import TaskLog

from .tasks import create_expense_groups, schedule_expense_group_creation
from .helpers import check_interval_and_sync_dimension, sync_dimensions
from .models import Expense, ExpenseFilter, ExpenseGroup, ExpenseGroupSettings, DependentFieldSetting
from .serializers import (
    ExpenseFilterSerializer, ExpenseGroupExpenseSerializer, ExpenseGroupSerializer,
    ExpenseSerializer, ExpenseFieldSerializer, ExpenseGroupSettingsSerializer,
    DependentFieldSettingSerializer
)


class ExpenseGroupView(generics.ListCreateAPIView):
    """
    List Fyle Expenses
    """
    serializer_class = ExpenseGroupSerializer

    def get_queryset(self):
        state = self.request.query_params.get('state', 'ALL')
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        expense_group_ids = self.request.query_params.get('expense_group_ids', None)
        exported_at = self.request.query_params.get('exported_at', None)

        if expense_group_ids:
            return ExpenseGroup.objects.filter(
                workspace_id=self.kwargs['workspace_id'],
                id__in=expense_group_ids.split(',')
            )

        if state == 'ALL':
            return ExpenseGroup.objects.filter(workspace_id=self.kwargs['workspace_id']).order_by('-updated_at')

        if state == 'FAILED':
            return ExpenseGroup.objects.filter(tasklog__status='FAILED',
                                               workspace_id=self.kwargs['workspace_id']).order_by('-updated_at')

        elif state == 'COMPLETE':
            filters = {
                'workspace_id': self.kwargs['workspace_id'],
                'tasklog__status': 'COMPLETE'
            }

            if start_date and end_date:
                filters['exported_at__range'] = [start_date, end_date]

            if exported_at:
                filters['exported_at__gte'] = exported_at
            return ExpenseGroup.objects.filter(**filters).order_by('-exported_at')

        elif state == 'READY':
            return ExpenseGroup.objects.filter(
                bill__id__isnull=True,
                journalentry__id__isnull=True,
                expensereport__id__isnull=True,
                chargecardtransaction__id__isnull=True,
                workspace_id=self.kwargs['workspace_id']
            ).order_by('-updated_at')

    def post(self, request, *args, **kwargs):
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
        )
        return Response(
            status=status.HTTP_200_OK
        )


class ExpenseGroupCountView(generics.ListAPIView):
    """
    Expense Group Count View
    """

    def get(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
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

    def get(self, request, *args, **kwargs):
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

    def get_queryset(self):
        return ExpenseAttribute.objects.filter(
            attribute_type='EMPLOYEE', workspace_id=self.kwargs['workspace_id']).order_by('value')


class CategoryView(generics.ListCreateAPIView):
    """
    Category view
    """

    serializer_class = ExpenseAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return ExpenseAttribute.objects.filter(
            attribute_type='CATEGORY', workspace_id=self.kwargs['workspace_id']).order_by('value')


class ProjectView(generics.ListCreateAPIView):
    """
    Project view
    """
    serializer_class = ExpenseAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return ExpenseAttribute.objects.filter(
            attribute_type='PROJECT', workspace_id=self.kwargs['workspace_id']).order_by('value')


class CostCenterView(generics.ListCreateAPIView):
    """
    Cost Center view
    """

    serializer_class = ExpenseAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return ExpenseAttribute.objects.filter(
            attribute_type='COST_CENTER', workspace_id=self.kwargs['workspace_id']).order_by('value')


class ExpenseGroupSettingsView(generics.ListCreateAPIView):
    """
    Expense Group Settings View
    """
    serializer_class = ExpenseGroupSettingsSerializer

    def get(self, request, *args, **kwargs):
        expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=self.kwargs['workspace_id'])

        return Response(
            data=self.serializer_class(expense_group_settings).data,
            status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        expense_group_settings, _ = ExpenseGroupSettings.update_expense_group_settings(
            request.data, self.kwargs['workspace_id'])
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

    def get_queryset(self):
        attribute_type = self.request.query_params.get('attribute_type')
        active = self.request.query_params.get('active')

        params = {
            'workspace_id': self.kwargs['workspace_id'],
            'attribute_type': self.request.query_params.get('attribute_type')
        }

        if active and active.lower() == 'true':
            params['active'] = True


        return ExpenseAttribute.objects.filter(**params).order_by('value')


class FyleFieldsView(generics.ListAPIView):
    pagination_class = None
    serializer_class = ExpenseFieldSerializer

    def get(self, request, *args, **kwargs):
        default_attributes = ['EMPLOYEE', 'CATEGORY', 'PROJECT', 'COST_CENTER', 'LOCATION_ENTITY', 'TAX_GROUP', 'CORPORATE_CARD', 'MERCHANT']

        attributes = ExpenseAttribute.objects.filter(
            ~Q(attribute_type__in=default_attributes),
            workspace_id=self.kwargs['workspace_id']
        ).values('attribute_type', 'display_name').distinct()

        expense_fields= [
            {'attribute_type': 'COST_CENTER', 'display_name': 'Cost Center'},
            {'attribute_type': 'PROJECT', 'display_name': 'Project'}
        ]

        for attribute in attributes:
            expense_fields.append(attribute)

        return Response(
            expense_fields,
            status=status.HTTP_200_OK
        )


class SyncFyleDimensionView(generics.ListCreateAPIView):
    """
    Sync Fyle Dimensions view
    """
    def post(self, request, *args, **kwargs):
        """
        Sync data from Fyle
        """
        try:
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])
            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace.id)

            synced = check_interval_and_sync_dimension(workspace, fyle_credentials)
            if synced:
                workspace.source_synced_at = datetime.now()
                workspace.save(update_fields=['source_synced_at'])

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
    def post(self, request, *args, **kwargs):
        """
        Sync data from Fyle
        """
        try:
            workspace = Workspace.objects.get(id=kwargs['workspace_id'])
            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace.id)

            mapping_settings = MappingSetting.objects.filter(workspace_id=kwargs['workspace_id'], import_to_fyle=True)
            chain = Chain()

            for mapping_setting in mapping_settings:
                if mapping_setting.source_field == 'PROJECT':
                    chain.append('apps.mappings.tasks.auto_import_and_map_fyle_fields', int(kwargs['workspace_id']))
                elif mapping_setting.source_field == 'COST_CENTER':
                    chain.append('apps.mappings.tasks.auto_create_cost_center_mappings', int(kwargs['workspace_id']))
                elif mapping_setting.is_custom:
                    chain.append('apps.mappings.tasks.async_auto_create_custom_field_mappings',
                                int(kwargs['workspace_id']))

            if chain.length() > 0:
                chain.run()


            sync_dimensions(fyle_credentials, workspace.id)

            workspace.source_synced_at = datetime.now()
            workspace.save(update_fields=['source_synced_at'])

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

    def get_queryset(self):
        queryset = ExpenseFilter.objects.filter(workspace_id=self.kwargs['workspace_id']).order_by('rank')
        return queryset

    def delete(self, request, *args, **kwargs):
        workspace_id = self.kwargs['workspace_id']
        rank = self.request.query_params.getlist('rank')
        ExpenseFilter.objects.filter(workspace_id=workspace_id, rank__in=rank).delete()

        return Response(data={
            'workspace_id': workspace_id,
            'rank' : rank,
            'message': 'Expense filter deleted'
        })


class ExpenseView(generics.ListAPIView):
    """
    Expense view
    """

    serializer_class = ExpenseSerializer

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        org_id = Workspace.objects.get(id=self.kwargs['workspace_id']).fyle_org_id

        filters = {
            'org_id': org_id,
            'is_skipped': True
        }

        if start_date and end_date:
            filters['updated_at__range'] = [start_date, end_date]

        queryset = Expense.objects.filter(**filters).order_by('-updated_at')

        return queryset


class CustomFieldView(generics.RetrieveAPIView):
    """
    Custom Field view
    """
    def get(self, request, *args, **kwargs):
        """
        Get Custom Fields
        """
        workspace_id = self.kwargs['workspace_id']

        fyle_credentails = FyleCredential.objects.get(workspace_id=workspace_id)

        platform = PlatformConnector(fyle_credentails)

        custom_fields = platform.expense_custom_fields.list_all()

        response = []
        response.extend(DEFAULT_FYLE_CONDITIONS)
        for custom_field in custom_fields:
            if custom_field['type'] in ('SELECT', 'NUMBER', 'TEXT'):
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
    def get(self, request, *args, **kwargs):
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
    def post(self, request, *args, **kwargs):
        """
        Post expense groups creation
        """
        task_log, fund_source = get_task_log_and_fund_source(kwargs['workspace_id'])

        async_create_expense_groups(kwargs['workspace_id'], fund_source, task_log)

        return Response(
            status=status.HTTP_200_OK
        )
