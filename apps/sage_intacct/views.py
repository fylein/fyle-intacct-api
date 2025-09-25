import logging

from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
from rest_framework import generics
from rest_framework.views import status
from rest_framework.request import Request
from rest_framework.response import Response

from sageintacctsdk.exceptions import InvalidTokenError
from fyle_accounting_mappings.models import DestinationAttribute
from fyle_accounting_library.common_resources.models import DimensionDetail
from fyle_accounting_mappings.serializers import DestinationAttributeSerializer
from fyle_accounting_library.common_resources.enums import DimensionDetailSourceTypeEnum

from apps.workspaces.enums import CacheKeyEnum
from apps.sage_intacct.helpers import sync_dimensions
from apps.sage_intacct.serializers import SageIntacctFieldSerializer
from fyle_intacct_api.utils import invalidate_sage_intacct_credentials
from workers.helpers import RoutingKeyEnum, WorkerActionEnum, publish_to_rabbitmq
from apps.workspaces.models import (
    Workspace,
    Configuration,
    SageIntacctCredential
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

        attributes = list(attributes)
        attributes.append({
            'attribute_type': 'PROJECT',
            'display_name': 'Project'
        })

        dimensions = DimensionDetail.objects.filter(workspace_id=self.kwargs['workspace_id'], source_type=DimensionDetailSourceTypeEnum.ACCOUNTING.value).values(
            'attribute_type', 'display_name'
        )

        allocation_fields = {'attribute_type': 'ALLOCATION', 'display_name': 'allocation'}

        for attribute in attributes:
            attribute_type = attribute['attribute_type']

            if dimensions.filter(attribute_type=attribute_type).exists():
                attribute['display_name'] = dimensions.get(attribute_type=attribute_type)['display_name']
                if attribute_type == 'ALLOCATION':
                    allocation_fields['display_name'] = attribute['display_name']

        serialized_attributes = SageIntacctFieldSerializer(attributes, many=True).data

        if settings.BRAND_ID != 'fyle':
            if allocation_fields in serialized_attributes:
                serialized_attributes.remove(allocation_fields)

        else:
            configurations = Configuration.objects.get(workspace_id=self.kwargs['workspace_id'])

            if configurations.corporate_credit_card_expenses_object not in ['BILL', 'JOURNAL_ENTRY'] and configurations.reimbursable_expenses_object not in ['BILL', 'JOURNAL_ENTRY']:
                if allocation_fields in serialized_attributes:
                    serialized_attributes.remove(allocation_fields)

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
            sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace.id)
            cache_key = CacheKeyEnum.SAGE_INTACCT_SYNC_DIMENSIONS.value.format(workspace_id=workspace.id)
            is_cached = cache.get(cache_key)

            if not is_cached:
                # Set cache to avoid multiple requests in the next 5 minutes
                cache.set(cache_key, True, timeout=300)
                payload = {
                    'workspace_id': workspace.id,
                    'action': WorkerActionEnum.CHECK_INTERVAL_AND_SYNC_SAGE_INTACCT_DIMENSION.value,
                    'data': {
                        'workspace_id': workspace.id
                    }
                }
                publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)

            return Response(
                status=status.HTTP_200_OK
            )

        except SageIntacctCredential.DoesNotExist:
            logger.info('Sage Intacct credentials not found workspace_id - %s', kwargs['workspace_id'])
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found workspace_id - %s' % kwargs['workspace_id']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except InvalidTokenError:
            invalidate_sage_intacct_credentials(workspace.id, sage_intacct_credentials)
            logger.info('Invalid Sage Intact Token for workspace_id - %s', kwargs['workspace_id'])
            return Response(
                data={
                    'message': 'Invalid Sage Intact Token for workspace_id - %s' % kwargs['workspace_id']
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
            cache_key = CacheKeyEnum.SAGE_INTACCT_SYNC_DIMENSIONS.value.format(workspace_id=workspace.id)
            is_cached = cache.get(cache_key)

            if not is_cached:
                cache.set(cache_key, True, timeout=300)
                # If only specified dimensions are to be synced, sync them synchronously
                if dimensions_to_sync:
                    sync_dimensions(workspace.id, dimensions_to_sync)
                else:
                    payload = {
                        'workspace_id': workspace.id,
                        'action': WorkerActionEnum.SYNC_SAGE_INTACCT_DIMENSION.value,
                        'data': {
                            'workspace_id': workspace.id
                        }
                    }
                    publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)

            return Response(
                status=status.HTTP_200_OK
            )

        except SageIntacctCredential.DoesNotExist:
            logger.info('Sage Intacct credentials not found workspace_id - %s', kwargs['workspace_id'])
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found workspace_id - %s' % kwargs['workspace_id']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except InvalidTokenError:
            invalidate_sage_intacct_credentials(workspace.id)
            logger.info('Invalid Sage Intact Token for workspace_id - %s', kwargs['workspace_id'])
            return Response(
                data={
                    'message': 'Invalid Sage Intact Token for workspace_id - %s' % kwargs['workspace_id']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
