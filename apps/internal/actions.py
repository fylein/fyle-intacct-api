from apps.sage_intacct.utils import SageIntacctConnector
from apps.workspaces.models import Workspace, SageIntacctCredential


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
