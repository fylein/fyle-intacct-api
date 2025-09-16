import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Optional, Union

import requests
import django_filters
from django.db import models
from django.db.models import Q
from django.conf import settings
from rest_framework.exceptions import ValidationError
from django.utils.module_loading import import_string

from fyle_accounting_mappings.models import ExpenseAttribute
from fyle_integrations_platform_connector import PlatformConnector
from fyle_accounting_library.common_resources.models import DimensionDetail
from fyle_accounting_library.common_resources.enums import DimensionDetailSourceTypeEnum

from apps.tasks.models import TaskLog
from fyle_intacct_api.utils import get_access_token, post_request
from apps.workspaces.models import Configuration, FyleCredential, Workspace
from apps.mappings.tasks import construct_tasks_and_chain_import_fields_to_fyle
from apps.fyle.models import DependentFieldSetting, Expense, ExpenseFilter, ExpenseGroup, ExpenseGroupSettings

logger = logging.getLogger(__name__)
logger.level = logging.INFO

SOURCE_ACCOUNT_MAP = {'PERSONAL': 'PERSONAL_CASH_ACCOUNT', 'CCC': 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'}


def get_request(url: str, params: dict, refresh_token: str) -> Optional[dict]:
    """
    Create a HTTP get request.
    :param url: URL
    :param params: Params
    :param refresh_token: Refresh token
    :return: dict
    """
    access_token = get_access_token(refresh_token)
    api_headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer {0}'.format(access_token)
    }
    api_params = {}

    for k in params:
        # ignore all unused params
        if not params[k] is None:
            p = params[k]

            # convert boolean to lowercase string
            if isinstance(p, bool):
                p = str(p).lower()

            api_params[k] = p

    response = requests.get(
        url,
        headers=api_headers,
        params=api_params
    )

    if response.status_code == 200:
        return json.loads(response.text)
    else:
        raise Exception(response.text)


def get_fyle_orgs(refresh_token: str, cluster_domain: str) -> dict:
    """
    Get fyle orgs of a user
    :param refresh_token: (str)
    :param cluster_domain: (str)
    :return: fyle_orgs (dict)
    """
    api_url = '{0}/api/orgs/'.format(cluster_domain)

    return get_request(api_url, {}, refresh_token)


def get_cluster_domain(refresh_token: str) -> str:
    """
    Get cluster domain name from fyle
    :param refresh_token: (str)
    :return: cluster_domain (str)
    """
    cluster_api_url = '{0}/oauth/cluster/'.format(settings.FYLE_BASE_URL)

    return post_request(cluster_api_url, {}, refresh_token)['cluster_domain']


def add_expense_id_to_expense_group_settings(workspace_id: int) -> None:
    """
    Add Expense id to card expense grouping
    :param workspace_id: Workspace id
    return: None
    """
    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    ccc_expense_group_fields = expense_group_settings.corporate_credit_card_expense_group_fields
    ccc_expense_group_fields.append('expense_id')
    expense_group_settings.corporate_credit_card_expense_group_fields = list(set(ccc_expense_group_fields))
    expense_group_settings.save()


def check_interval_and_sync_dimension(workspace_id: int, **kwargs) -> None:
    """
    Check sync interval and sync dimension
    :param workspace_id: Workspace ID
    :param kwargs: Keyword arguments
    :return: None
    """
    workspace = Workspace.objects.get(pk=workspace_id)

    if workspace.source_synced_at:
        time_interval = datetime.now(timezone.utc) - workspace.source_synced_at

    if workspace.source_synced_at is None or time_interval.days > 0:
        sync_dimensions(workspace_id)
        workspace.source_synced_at = datetime.now()
        workspace.save(update_fields=['source_synced_at'])


def sync_dimensions(workspace_id: int, is_export: bool = False) -> None:
    """
    Sync dimensions
    :param workspace_id: Workspace ID
    :param is_export: Is export
    :return: None
    """
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    configuration = Configuration.objects.filter(workspace_id=workspace_id).first()
    skip_dependent_field_ids = []

    dependent_field_settings = DependentFieldSetting.objects.filter(workspace_id=fyle_credentials.workspace_id, is_import_enabled=True).first()

    if dependent_field_settings:
        skip_dependent_field_ids = [dependent_field_settings.cost_code_field_id, dependent_field_settings.cost_type_field_id]

    platform = PlatformConnector(fyle_credentials)
    platform.import_fyle_dimensions(
        import_taxes=True,
        import_dependent_fields=True,
        is_export=is_export,
        skip_dependent_field_ids=skip_dependent_field_ids
    )

    unmapped_card_count = ExpenseAttribute.objects.filter(
        attribute_type="CORPORATE_CARD", workspace_id=workspace_id, active=True, mapping__isnull=True
    ).count()
    if configuration and configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
        import_string('apps.workspaces.tasks.patch_integration_settings_for_unmapped_cards')(workspace_id=workspace_id, unmapped_card_count=unmapped_card_count)

    update_dimension_details(platform=platform, workspace_id=fyle_credentials.workspace.id)

    if is_export:
        categories_count = platform.categories.get_count()

        categories_expense_attribute_count = ExpenseAttribute.objects.filter(
            attribute_type="CATEGORY", workspace_id=fyle_credentials.workspace_id, active=True
        ).count()

        if categories_count != categories_expense_attribute_count:
            platform.categories.sync()

        projects_count = platform.projects.get_count()

        projects_expense_attribute_count = ExpenseAttribute.objects.filter(
            attribute_type="PROJECT", workspace_id=fyle_credentials.workspace_id, active=True
        ).count()

        if projects_count != projects_expense_attribute_count:
            platform.projects.sync()


def handle_refresh_dimensions(workspace_id: int) -> None:
    """
    Handle refresh dimensions
    :param workspace_id: Workspace ID
    :return: None
    """
    workspace = Workspace.objects.get(id=workspace_id)
    configuration = Configuration.objects.filter(workspace_id=workspace_id).first()

    if configuration:
        construct_tasks_and_chain_import_fields_to_fyle(workspace_id)

    sync_dimensions(workspace_id)

    workspace.source_synced_at = datetime.now()
    workspace.save(update_fields=['source_synced_at'])


def construct_expense_filter(expense_filter: ExpenseFilter) -> Q:
    """
    Construct the expense filter
    :param expense_filter: Expense filter
    :return: Constructed expense filter
    """
    # If the expense filter is a custom field
    if expense_filter.is_custom:
        # If the operator is not isnull
        if expense_filter.operator != 'isnull':
            # If the custom field is of type SELECT and the operator is not_in
            if expense_filter.custom_field_type == 'SELECT' and expense_filter.operator == 'not_in':
                # Construct the filter for the custom property
                filter1 = {
                    f'custom_properties__{expense_filter.condition}__in': expense_filter.values
                }
                # Invert the filter using the ~Q operator and assign it to the constructed expense filter
                constructed_expense_filter = ~Q(**filter1)
            else:
                # If the custom field is of type NUMBER, convert the values to integers
                if expense_filter.custom_field_type == 'NUMBER':
                    expense_filter.values = [int(value) for value in expense_filter.values]
                # If the expense filter is a custom field and the operator is yes or no(checkbox)
                if expense_filter.custom_field_type == 'BOOLEAN':
                    expense_filter.values[0] = True if expense_filter.values[0] == 'true' else False
                # Construct the filter for the custom property
                filter1 = {
                    f'custom_properties__{expense_filter.condition}__{expense_filter.operator}':
                        expense_filter.values[0] if len(expense_filter.values) == 1 and expense_filter.operator != 'in'
                        else expense_filter.values
                }
                # Assign the constructed filter to the constructed expense filter
                constructed_expense_filter = Q(**filter1)

        # If the expense filter is a custom field and the operator is isnull
        elif expense_filter.operator == 'isnull':
            # Determine the value for the isnull filter based on the first value in the values list
            expense_filter_value: bool = True if expense_filter.values[0].lower() == 'true' else False
            # Construct the isnull filter for the custom property
            filter1 = {
                f'custom_properties__{expense_filter.condition}__isnull': expense_filter_value
            }
            # Construct the exact filter for the custom property
            filter2 = {
                f'custom_properties__{expense_filter.condition}__exact': None
            }
            if expense_filter_value:
                # If the isnull filter value is True, combine the two filters using the | operator and assign it to the constructed expense filter
                constructed_expense_filter = Q(**filter1) | Q(**filter2)
            else:
                # If the isnull filter value is False, invert the exact filter using the ~Q operator and assign it to the constructed expense filter
                constructed_expense_filter = ~Q(**filter2)
    # for category non-custom field with not_in as operator, to check this later on
    elif expense_filter.condition == 'category' and expense_filter.operator == 'not_in' and not expense_filter.is_custom:
        # construct the filter
        filter1 = {
            f'{expense_filter.condition}__in': expense_filter.values
        }
        # Invert the filter using the ~Q operator and assign it to the constructed expense filter
        constructed_expense_filter = ~Q(**filter1)
    # For all non-custom fields
    else:
        # Construct the filter for the non-custom field
        filter1 = {
            f'{expense_filter.condition}__{expense_filter.operator}':
                expense_filter.values[0] if len(expense_filter.values) == 1 and expense_filter.operator != 'in'
                else expense_filter.values
        }
        # Assign the constructed filter to the constructed expense filter
        constructed_expense_filter = Q(**filter1)

    # Return the constructed expense filter
    return constructed_expense_filter


def construct_expense_filter_query(expense_filters: list[ExpenseFilter]) -> Q:
    """
    Construct the expense filter query
    :param expense_filters: Expense filters
    :return: Constructed expense filter query
    """
    final_filter = None
    previous_join_by = None
    for expense_filter in expense_filters:
        constructed_expense_filter = construct_expense_filter(expense_filter)

        # If this is the first filter, set it as the final filter
        if expense_filter.rank == 1:
            final_filter = (constructed_expense_filter)

        # If join by is AND, OR
        elif expense_filter.rank != 1:
            if previous_join_by == 'AND':
                final_filter = final_filter & (constructed_expense_filter)
            else:
                final_filter = final_filter | (constructed_expense_filter)

        # Set the join type for the additonal filter
        previous_join_by = expense_filter.join_by

    return final_filter


def connect_to_platform(workspace_id: int) -> PlatformConnector:
    """
    Connect to platform
    :param workspace_id: Workspace ID
    :return: Platform connector
    """
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)

    return PlatformConnector(fyle_credentials=fyle_credentials)


def get_updated_accounting_export_summary(
    expense_id: str,
    state: str,
    error_type: Union[str, None],
    url: Union[str, None],
    is_synced: bool
) -> dict:
    """
    Get updated accounting export summary
    :param expense_id: expense id
    :param state: state
    :param error_type: error type
    :param url: url
    :param is_synced: is synced
    :return: updated accounting export summary
    """
    return {
        'id': expense_id,
        'state': state,
        'error_type': error_type,
        'url': url,
        'synced': is_synced
    }


def get_batched_expenses(batched_payload: list[dict], workspace_id: int) -> list[Expense]:
    """
    Get batched expenses
    :param batched_payload: batched payload
    :param workspace_id: workspace id
    :return: batched expenses
    """
    expense_ids = [expense['id'] for expense in batched_payload]
    return Expense.objects.filter(expense_id__in=expense_ids, workspace_id=workspace_id)


def get_source_account_type(fund_source: list[str]) -> list[str]:
    """
    Get source account type
    :param fund_source: fund source
    :return: source account type
    """
    source_account_type = []
    for source in fund_source:
        source_account_type.append(SOURCE_ACCOUNT_MAP[source])

    return source_account_type


def get_fund_source(workspace_id: int) -> list[str]:
    """
    Get fund source
    :param workspace_id: workspace id
    :return: fund source
    """
    general_settings = Configuration.objects.get(workspace_id=workspace_id)
    fund_source = []
    if general_settings.reimbursable_expenses_object:
        fund_source.append('PERSONAL')
    if general_settings.corporate_credit_card_expenses_object:
        fund_source.append('CCC')

    return fund_source


def handle_import_exception(task_log: TaskLog | None) -> None:
    """
    Handle import exception
    :param task_log: task log
    :return: None
    """
    error = traceback.format_exc()
    if task_log:
        task_log.detail = {'error': error}
        task_log.status = 'FATAL'
        task_log.updated_at = datetime.now()
        task_log.save(update_fields=['detail', 'status', 'updated_at'])
        logger.error('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)
    else:
        logger.error('Something unexpected happened %s', error)


def assert_valid_request(workspace_id:int, fyle_org_id:str) -> None:
    """
    Assert if the request is valid by checking
    the url_workspace_id and fyle_org_id workspace
    :param workspace_id: Workspace ID
    :param fyle_org_id: Fyle Org ID
    :return: None
    """
    workspace = Workspace.objects.get(fyle_org_id=fyle_org_id)
    if workspace.id != workspace_id:
        raise ValidationError('Workspace mismatch')


def update_dimension_details(platform: PlatformConnector, workspace_id: int) -> None:
    """
    Update dimension details
    :param platform: Platform connector
    :param workspace_id: Workspace ID
    :return: None
    """
    fields = platform.expense_custom_fields.list_all({
        'order': 'updated_at.desc',
        'is_custom': 'eq.false',
        'column_name': 'in.(project_id, cost_center_id)'
    })
    fields.extend(
        platform.expense_custom_fields.list_all()
    )
    details = []

    for field in fields:
        if field['column_name'] == 'project_id':
            details.append({
                'attribute_type': 'PROJECT',
                'display_name': field['field_name'],
                'source_type': DimensionDetailSourceTypeEnum.FYLE.value,
                'workspace_id': workspace_id
            })
        elif field['column_name'] == 'cost_center_id':
            details.append({
                'attribute_type': 'COST_CENTER',
                'display_name': field['field_name'],
                'source_type': DimensionDetailSourceTypeEnum.FYLE.value,
                'workspace_id': workspace_id
            })
        elif field['type'] in ('SELECT'):
            details.append({
                'attribute_type': field['field_name'].upper().replace(' ', '_'),
                'display_name': field['field_name'],
                'source_type': DimensionDetailSourceTypeEnum.FYLE.value,
                'workspace_id': workspace_id
            })

    if details:
        DimensionDetail.bulk_create_or_update_dimension_details(
            dimensions=details,
            workspace_id=workspace_id,
            source_type=DimensionDetailSourceTypeEnum.FYLE.value
        )


class AdvanceSearchFilter(django_filters.FilterSet):
    """
    Advance search filter
    """
    def filter_queryset(self, queryset: models.QuerySet) -> models.QuerySet:
        """
        Filter queryset
        :param queryset: Queryset
        :return: Filtered queryset
        """
        or_filtered_queryset = queryset.none()
        or_filter_fields = getattr(self.Meta, 'or_fields', [])
        or_field_present = False

        for field_name in self.Meta.fields:
            value = self.data.get(field_name)
            if value:
                if field_name == 'is_skipped':
                    value = True if str(value) == 'true' else False
                filter_instance = self.filters[field_name]
                queryset = filter_instance.filter(queryset, value)

        for field_name in or_filter_fields:
            value = self.data.get(field_name)
            if value:
                or_field_present = True
                filter_instance = self.filters[field_name]
                field_filtered_queryset = filter_instance.filter(queryset, value)
                or_filtered_queryset |= field_filtered_queryset

        if or_field_present:
            queryset = queryset & or_filtered_queryset
            return queryset

        return queryset


class ExpenseGroupSearchFilter(AdvanceSearchFilter):
    """
    Expense group search filter
    """
    exported_at__gte = django_filters.DateTimeFilter(lookup_expr='gte', field_name='exported_at')
    exported_at__lte = django_filters.DateTimeFilter(lookup_expr='lte', field_name='exported_at')
    tasklog__status = django_filters.CharFilter()
    expenses__expense_number = django_filters.CharFilter(field_name='expenses__expense_number', lookup_expr='icontains')
    expenses__employee_name = django_filters.CharFilter(field_name='expenses__employee_name', lookup_expr='icontains')
    expenses__employee_email = django_filters.CharFilter(field_name='expenses__employee_email', lookup_expr='icontains')
    expenses__claim_number = django_filters.CharFilter(field_name='expenses__claim_number', lookup_expr='icontains')

    class Meta:
        model = ExpenseGroup
        fields = ['exported_at__gte', 'exported_at__lte', 'tasklog__status']
        or_fields = ['expenses__expense_number', 'expenses__employee_name', 'expenses__employee_email', 'expenses__claim_number']


class ExpenseSearchFilter(AdvanceSearchFilter):
    """
    Expense search filter
    """
    org_id = django_filters.CharFilter()
    is_skipped = django_filters.BooleanFilter()
    updated_at__gte = django_filters.DateTimeFilter(lookup_expr='gte', field_name='updated_at')
    updated_at__lte = django_filters.DateTimeFilter(lookup_expr='lte', field_name='updated_at')
    expense_number = django_filters.CharFilter(field_name='expense_number', lookup_expr='icontains')
    employee_name = django_filters.CharFilter(field_name='employee_name', lookup_expr='icontains')
    employee_email = django_filters.CharFilter(field_name='employee_email', lookup_expr='icontains')
    claim_number = django_filters.CharFilter(field_name='claim_number', lookup_expr='icontains')

    class Meta:
        model = Expense
        fields = ['org_id', 'is_skipped', 'updated_at__gte', 'updated_at__lte']
        or_fields = ['expense_number', 'employee_name', 'employee_email', 'claim_number']


def update_task_log_post_import(task_log: TaskLog, status: str, message: str = None, error: str = None) -> None:
    """Helper function to update task log status and details"""
    if task_log:
        task_log.status = status
        task_log.detail = {"message": message} if message else {"error": error}
        task_log.updated_at = datetime.now()
        task_log.save(update_fields=['status', 'detail', 'updated_at'])
