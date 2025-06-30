import logging

from django.conf import settings

from apps.fyle.helpers import delete_request
from apps.sage_intacct.utils import SageIntacctConnector
from apps.workspaces.models import FyleCredential, Workspace, SageIntacctCredential


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def get_intacct_connection(query_params: dict) -> SageIntacctConnector:
    """
    Get Sage Intacct connection
    :param query_params: Query parameters
    :return: Sage Intacct connection
    """
    org_id = query_params.get('org_id')

    workspace = Workspace.objects.get(fyle_org_id=org_id)
    workspace_id = workspace.id
    try:
        intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace_id)
        return SageIntacctConnector(intacct_credentials, workspace_id)
    except SageIntacctCredential.DoesNotExist:
        raise Exception('Sage Intacct credentials not found')


def get_accounting_fields(query_params: dict) -> dict:
    """
    Get accounting fields
    :param query_params: Query parameters
    :return: Accounting fields
    """
    intacct_connection = get_intacct_connection(query_params)
    resource_type = query_params.get('resource_type')
    _ = query_params.get('internal_id')

    return intacct_connection.get_accounting_fields(resource_type)


def get_exported_entry(query_params: dict) -> dict:
    """
    Get exported entry
    :param query_params: Query parameters
    :return: Exported entry
    """
    intacct_connection = get_intacct_connection(query_params)
    resource_type = query_params.get('resource_type')
    internal_id = query_params.get('internal_id')

    return intacct_connection.get_exported_entry(resource_type, internal_id)


def delete_integration_record(workspace_id: int) -> str:
    """
    Delete integration record
    :param workspace_id: Workspace ID
    """

    logger.info(f"Cleaning up integration settings for workspace_id: {workspace_id}")

    refresh_token = FyleCredential.objects.get(workspace_id=workspace_id).refresh_token
    url = '{}/integrations/'.format(settings.INTEGRATIONS_SETTINGS_API)
    payload = {
        'tpa_name': 'Fyle Sage Intacct Integration'
    }

    try:
        delete_request(url, payload, refresh_token)
        logger.info(f"Integration settings cleanup successful for workspace_id: {workspace_id}")
        return "SUCCESS"
    except Exception as error:
        logger.error(f"Integration settings cleanup failed for workspace_id {workspace_id}: {str(error)}")
        logger.error(error, exc_info=True)
        return "FAILED"
