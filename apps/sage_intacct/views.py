import logging

from django.db.models import Q
from django.conf import settings
from django_q.tasks import async_task

from rest_framework import generics
from rest_framework.views import status
from rest_framework.request import Request
from rest_framework.response import Response

from fyle_accounting_mappings.models import DestinationAttribute
from fyle_accounting_mappings.serializers import DestinationAttributeSerializer

from sageintacctsdk.exceptions import InvalidTokenError

from apps.sage_intacct.helpers import sync_dimensions
from apps.workspaces.actions import export_to_intacct
from apps.sage_intacct.serializers import SageIntacctFieldSerializer
from apps.workspaces.models import (
    Workspace,
    Configuration,
    SageIntacctCredential
)
from apps.sage_intacct.tasks import (
    create_ap_payment,
    create_sage_intacct_reimbursement,
    check_sage_intacct_object_status,
    process_fyle_reimbursements
)

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class DestinationAttributesView(generics.ListAPIView):
    """
    Destination Attributes view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self) -> DestinationAttribute:
        """
        Get Destination Attributes
        """
        attribute_types = self.request.query_params.get('attribute_types').split(',')
        account_type = self.request.query_params.get('account_type')
        active = self.request.query_params.get('active')

        params = {
            'attribute_type__in': attribute_types,
            'workspace_id': self.kwargs['workspace_id']
        }

        if active and active.lower() == 'true':
            params['active'] = True

        destination_attributes = DestinationAttribute.objects.filter(
            **params).order_by('value')

        if account_type:
            params = {
                'attribute_type': 'ACCOUNT',
                'detail__account_type': account_type
            }
            destination_attributes = destination_attributes.exclude(**params)  # to filter out data with account_type='incomestatement

        return destination_attributes


class PaginatedDestinationAttributesView(generics.ListAPIView):
    """
    Paginated Destination Attributes view
    """
    serializer_class = DestinationAttributeSerializer

    def get_queryset(self) -> DestinationAttribute:
        """
        Get Destination Attributes
        """
        value = self.request.query_params.get('value')
        params = {
            'attribute_type': self.request.query_params.get('attribute_type'),
            'workspace_id': self.kwargs['workspace_id'],
            'active': True
        }

        if value:
            params['value__icontains'] = value

        return DestinationAttribute.objects.filter(**params).order_by('value')


class DestinationAttributesCountView(generics.RetrieveAPIView):
    """
    Destination Attributes Count view
    """
    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get Destination Attributes Count
        """
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
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Trigger exports
        """
        export_to_intacct(workspace_id=self.kwargs['workspace_id'])

        return Response(
            status=status.HTTP_200_OK
        )


class TriggerPaymentsView(generics.GenericAPIView):
    """
    Trigger payments sync
    """
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Trigger payments sync
        """
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
    """
    Sage Intacct Fields View
    """
    pagination_class = None
    serializer_class = SageIntacctFieldSerializer

    def get_queryset(self) -> DestinationAttribute:
        """
        Get Sage Intacct Fields
        """
        attributes = DestinationAttribute.objects.filter(
            ~Q(attribute_type='EMPLOYEE') & ~Q(attribute_type='VENDOR') & ~Q(attribute_type='CHARGE_CARD_NUMBER')
            & ~Q(attribute_type='EXPENSE_TYPE') & ~Q(attribute_type='ACCOUNT') & ~Q(attribute_type='CCC_ACCOUNT'),
            ~Q(attribute_type='PAYMENT_ACCOUNT'), ~Q(attribute_type='EXPENSE_PAYMENT_TYPE'),
            ~Q(attribute_type='LOCATION_ENTITY'), ~Q(attribute_type='TAX_DETAIL'),
            ~Q(attribute_type='PROJECT'), ~Q(attribute_type='COST_CODE'),
            workspace_id=self.kwargs['workspace_id']
        ).values('attribute_type', 'display_name').distinct()

        serialized_attributes = SageIntacctFieldSerializer(attributes, many=True).data

        if settings.BRAND_ID != 'fyle':
            if {'attribute_type': 'ALLOCATION', 'display_name': 'allocation'} in serialized_attributes:
                serialized_attributes.remove({'attribute_type': 'ALLOCATION', 'display_name': 'allocation'})

        else:
            configurations = Configuration.objects.get(workspace_id=self.kwargs['workspace_id'])

            if configurations.corporate_credit_card_expenses_object not in ['BILL', 'JOURNAL_ENTRY'] and configurations.reimbursable_expenses_object not in ['BILL', 'JOURNAL_ENTRY']:
                if {'attribute_type': 'ALLOCATION', 'display_name': 'allocation'} in serialized_attributes:
                    serialized_attributes.remove({'attribute_type': 'ALLOCATION', 'display_name': 'allocation'})

        # Adding project by default since we support importing Projects from Sage Intacct even though they don't exist
        serialized_attributes.append({'attribute_type': 'PROJECT', 'display_name': 'Project'})

        return serialized_attributes


class SyncSageIntacctDimensionView(generics.ListCreateAPIView):
    """
    Sync Sage Intacct Dimension View
    """
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Sync data from sage intacct
        """
        try:
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])
            SageIntacctCredential.objects.get(workspace_id=workspace.id)

            async_task(
                'apps.sage_intacct.helpers.check_interval_and_sync_dimension',
                kwargs['workspace_id'],
            )

            return Response(
                status=status.HTTP_200_OK
            )

        except (SageIntacctCredential.DoesNotExist, InvalidTokenError) as exception:
            logger.info('Sage Intacct credentials not found / invalid in workspace', exception.__dict__)
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found / invalid in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class RefreshSageIntacctDimensionView(generics.ListCreateAPIView):
    """
    Refresh Sage Intacct Dimensions view
    """
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Sync data from sage intacct
        """
        dimensions_to_sync = request.data.get('dimensions_to_sync', [])

        try:
            workspace = Workspace.objects.get(pk=kwargs['workspace_id'])
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace.id)

            # If only specified dimensions are to be synced, sync them synchronously
            if dimensions_to_sync:
                sync_dimensions(sage_intacct_credentials, workspace.id, dimensions_to_sync)
            else:
                async_task(
                    'apps.sage_intacct.helpers.sync_dimensions',
                    sage_intacct_credentials,
                    workspace.id
                )

            return Response(
                status=status.HTTP_200_OK
            )

        except (SageIntacctCredential.DoesNotExist, InvalidTokenError) as exception:
            logger.info('Sage Intacct credentials not found / invalid in workspace', exception.__dict__)
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found / invalid in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
