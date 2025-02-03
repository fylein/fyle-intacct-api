from typing import Dict

from apps.sage_intacct.utils import SageIntacctConnector
from apps.workspaces.models import Workspace, SageIntacctCredential


def get_intacct_connection(query_params: Dict):
    org_id = query_params.get('org_id')

    workspace = Workspace.objects.get(fyle_org_id=org_id)
    workspace_id = workspace.id
    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace.id)

    return SageIntacctConnector(intacct_credentials, workspace_id)


def get_accounting_fields(query_params: Dict):
    intacct_connection = get_intacct_connection(query_params)
    resource_type = query_params.get('resource_type')
    internal_id = query_params.get('internal_id')

    return intacct_connection.get_accounting_fields(resource_type)


def get_exported_entry(query_params: Dict):
    intacct_connection = get_intacct_connection(query_params)
    resource_type = query_params.get('resource_type')
    internal_id = query_params.get('internal_id')

    return intacct_connection.get_exported_entry(resource_type, internal_id)
