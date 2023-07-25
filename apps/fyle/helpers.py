import json
import requests
from datetime import datetime, timezone
from fyle_integrations_platform_connector import PlatformConnector
import logging

from django.utils.module_loading import import_string
from django.conf import settings
from django.db.models import Q

from apps.fyle.models import ExpenseFilter, ExpenseGroupSettings
from apps.workspaces.models import FyleCredential, Workspace

from typing import List

logger = logging.getLogger(__name__)


def post_request(url, body, refresh_token=None):
    """
    Create a HTTP post request.
    """
    access_token = None
    api_headers = {}
    if refresh_token:
        access_token = get_access_token(refresh_token)

        api_headers['content-type'] = 'application/json'
        api_headers['Authorization'] = 'Bearer {0}'.format(access_token)

    response = requests.post(
        url,
        headers=api_headers,
        data=body
    )

    if response.status_code == 200:
        return json.loads(response.text)
    else:
        raise Exception(response.text)


def get_request(url, params, refresh_token):
    """
    Create a HTTP get request.
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


def get_access_token(refresh_token: str) -> str:
    """
    Get access token from fyle
    """
    api_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': settings.FYLE_CLIENT_ID,
        'client_secret': settings.FYLE_CLIENT_SECRET
    }
    return post_request(settings.FYLE_TOKEN_URI, body=api_data)['access_token']


def get_fyle_orgs(refresh_token: str, cluster_domain: str):
    """
    Get fyle orgs of a user
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


def add_expense_id_to_expense_group_settings(workspace_id: int):
    """
    Add Expense id to card expense grouping
    :param workspace_id: Workspace id
    return: None
    """
    expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
    ccc_expense_group_fields = expense_group_settings.corporate_credit_card_expense_group_fields
    ccc_expense_group_fields.append('expense_id')
    expense_group_settings.corporate_credit_card_expense_group_fields = list(set(ccc_expense_group_fields))
    expense_group_settings.ccc_export_date_type = 'spent_at'
    expense_group_settings.save()


def check_interval_and_sync_dimension(workspace: Workspace, fyle_credentials: FyleCredential) -> bool:
    """
    Check sync interval and sync dimension
    :param workspace: Workspace Instance
    :param fyle_credentials: Fyle credentials of an org
    return: True/False based on sync
    """
    if workspace.source_synced_at:
        time_interval = datetime.now(timezone.utc) - workspace.source_synced_at

    if workspace.source_synced_at is None or time_interval.days > 0:
        sync_dimensions(fyle_credentials, workspace.id)
        return True

    return False


def sync_dimensions(fyle_credentials: FyleCredential, workspace_id: int) -> None:
    platform = PlatformConnector(fyle_credentials)
    platform.import_fyle_dimensions(import_taxes=True)


def construct_expense_filter(expense_filter):
    constructed_expense_filter = {}

    # If the expense filter is a custom field and the operator is not isnull
    if expense_filter.is_custom and expense_filter.operator != 'isnull':
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
            # Construct the filter for the custom property
            filter1 = {
                f'custom_properties__{expense_filter.condition}__{expense_filter.operator}':
                    expense_filter.values[0] if len(expense_filter.values) == 1 and expense_filter.operator != 'in'
                    else expense_filter.values
            }
            # Assign the constructed filter to the constructed expense filter
            constructed_expense_filter = Q(**filter1)

    # If the expense filter is a custom field and the operator is isnull
    elif expense_filter.is_custom and expense_filter.operator == 'isnull':
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
    # If the expense filter is a custom field and the operator is yes or no(checkbox)
    elif expense_filter.is_custom and expense_filter.custom_field_type == 'BOOLEAN' and (expense_filter.operator == 'yes' or expense_filter.is_custom and expense_filter.operator == 'no'):
        filter1 = {
            f'custom_properties__{expense_filter.condition}__exact': expense_filter.values[0].lower()
        }
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

def construct_expense_filter_query(expense_filters: List[ExpenseFilter]):
    final_filter = None
    for expense_filter in expense_filters:
        constructed_expense_filter = construct_expense_filter(expense_filter)
        
        # If this is the first filter, set it as the final filter
        if expense_filter.rank == 1:
            final_filter = (constructed_expense_filter)
        
        # If join by is AND, OR
        elif expense_filter.rank != 1:
            if join_by == 'AND':
                final_filter = final_filter & (constructed_expense_filter)
            else:
                final_filter = final_filter | (constructed_expense_filter)

        # Set the join type for the additonal filter
        join_by = expense_filter.join_by

    return final_filter

def connect_to_platform(workspace_id: int) -> PlatformConnector:
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)

    return PlatformConnector(fyle_credentials=fyle_credentials)
