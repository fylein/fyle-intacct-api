from apps.mappings.imports.modules.base import Base
from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential


def get_base_class_instance(
        workspace_id: int = 1,
        source_field: str='PROJECT',
        destination_field: str = 'PROJECT',
        platform_class_name: str='projects',
        sync_after: str = None
    ):

    base = Base(
        workspace_id=workspace_id,
        source_field =source_field ,
        destination_field = destination_field,
        platform_class_name = platform_class_name,
        sync_after = sync_after
    )

    return base

def get_platform_connection(workspace_id):
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    return platform
