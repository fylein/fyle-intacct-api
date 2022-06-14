from django.db.models import Q
from datetime import datetime

from rest_framework.response import Response
from rest_framework.views import status
from rest_framework import generics

from fyle_accounting_mappings.models import DestinationAttribute
from fyle_accounting_mappings.serializers import DestinationAttributeSerializer

from sageintacctsdk.exceptions import InvalidTokenError

from fyle_intacct_api.utils import assert_valid

from apps.fyle.models import ExpenseGroup
from apps.tasks.models import TaskLog
from apps.workspaces.models import SageIntacctCredential, Workspace, Configuration

from .utils import SageIntacctConnector
from .helpers import sync_dimensions, check_interval_and_sync_dimension
from .tasks import create_expense_report, schedule_expense_reports_creation,schedule_journal_entries_creation, create_bill, schedule_bills_creation, \
    create_charge_card_transaction, schedule_charge_card_transaction_creation, create_ap_payment, \
    create_sage_intacct_reimbursement, check_sage_intacct_object_status, process_fyle_reimbursements
from .models import ExpenseReport, Bill, ChargeCardTransaction
from .serializers import ExpenseReportSerializer, BillSerializer, ChargeCardTransactionSerializer, \
    SageIntacctFieldSerializer


class DestinationAttributesView(generics.ListAPIView):
    """
    Destination Attributes view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        attribute_types = self.request.query_params.get('attribute_types').split(',')

        return DestinationAttribute.objects.filter(
            attribute_type__in=attribute_types, workspace_id=self.kwargs['workspace_id']).order_by('value')


class DestinationAttributesCountView(generics.RetrieveAPIView):
    """
    Destination Attributes Count view
    """
    def get(self, request, *args, **kwargs):
        attribute_type = self.request.query_params.get('attribute_type')

        attribute_count = DestinationAttribute.objects.filter(
            attribute_type=attribute_type, workspace_id=self.kwargs['workspace_id']
        ).count()

        return Response(
            data={
                'count': attribute_count
            },
            status=status.HTTP_200_OK
        )

class TriggerExportsView(generics.GenericAPIView):
    """
    Trigger exports creation
    """
    def post(self, request, *args, **kwargs):
        expense_group_ids = request.data.get('expense_group_ids', [])
        export_type = request.data.get('export_type')

        if export_type == 'BILL':
            schedule_bills_creation(kwargs['workspace_id'], expense_group_ids)
        elif export_type == 'CHARGE_CARD_TRANSACTION':
            schedule_charge_card_transaction_creation(kwargs['workspace_id'], expense_group_ids)
        elif export_type == 'EXPENSE_REPORT':
            schedule_expense_reports_creation(kwargs['workspace_id'], expense_group_ids)
        elif export_type == 'JOURNAL_ENTRY':
            schedule_journal_entries_creation(kwargs['workspace_id'], expense_group_ids)

        return Response(
            status=status.HTTP_200_OK
        )

class TriggerPaymentsView(generics.GenericAPIView):
    """
    Trigger payments sync
    """
    def post(self, request, *args, **kwargs):
        configurations = Configuration.objects.get(workspace_id=kwargs['workspace_id'])

        if configurations.sync_fyle_to_sage_intacct_payments:
            create_ap_payment(workspace_id=self.kwargs['workspace_id'])
            create_sage_intacct_reimbursement(workspace_id=self.kwargs['workspace_id'])

        elif configurations.sync_sage_intacct_to_fyle_payments:
            check_sage_intacct_object_status(workspace_id=self.kwargs['workspace_id'])
            process_fyle_reimbursements(workspace_id=self.kwargs['workspace_id'])

        return Response(
            status=status.HTTP_200_OK
        )

class SageIntacctFieldsView(generics.ListAPIView):
    pagination_class = None
    serializer_class = SageIntacctFieldSerializer

    def get_queryset(self):
        attributes = DestinationAttribute.objects.filter(
            ~Q(attribute_type='EMPLOYEE') & ~Q(attribute_type='VENDOR') & ~Q(attribute_type='CHARGE_CARD_NUMBER') &
            ~Q(attribute_type='EXPENSE_TYPE') & ~Q(attribute_type='ACCOUNT') & ~Q(attribute_type='CCC_ACCOUNT'),
            ~Q(attribute_type='PAYMENT_ACCOUNT'), ~Q(attribute_type='EXPENSE_PAYMENT_TYPE'), ~Q(attribute_type='ITEM'),
            ~Q(attribute_type='LOCATION_ENTITY'), ~Q(attribute_type='TAX_DETAIL'),
            workspace_id=self.kwargs['workspace_id']
        ).values('attribute_type', 'display_name').distinct()

        return attributes


class SyncSageIntacctDimensionView(generics.ListCreateAPIView):
    """
    Sync Sage Intacct Dimension View
    """

    def post(self, request, *args, **kwargs):

        try:
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace.id)

            synced = check_interval_and_sync_dimension(workspace, sage_intacct_credentials)

            if synced:
                workspace.destination_synced_at = datetime.now()
                workspace.save(update_fields=['destination_synced_at'])

            return Response(
                status=status.HTTP_200_OK
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct Credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class RefreshSageIntacctDimensionView(generics.ListCreateAPIView):
    """
    Refresh Sage Intacct Dimensions view
    """

    def post(self, request, *args, **kwargs):
        """
        Sync data from sage intacct
        """
        try:
            dimensions_to_sync = request.data.get('dimensions_to_sync', [])
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])

            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace.id)
            sync_dimensions(sage_intacct_credentials, workspace.id, dimensions_to_sync)

            # Update destination_synced_at to current time only when full refresh happens
            if not dimensions_to_sync:
                workspace.destination_synced_at = datetime.now()
                workspace.save(update_fields=['destination_synced_at'])

            return Response(
                status=status.HTTP_200_OK
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
