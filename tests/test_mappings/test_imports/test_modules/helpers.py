from fyle_integrations_platform_connector import PlatformConnector
from unittest import mock
from apps.mappings.constants import SYNC_METHODS

from apps.workspaces.models import FyleCredential
from fyle_integrations_imports.modules.base import Base


def get_base_class_instance(
    workspace_id: int = 1,
    source_field: str = 'PROJECT',
    destination_field: str = 'PROJECT',
    platform_class_name: str = 'projects',
    sync_after: str = None
):
    """
    Get Base class instance
    """
    sdk_connection = mock.Mock()
    destination_sync_methods = [SYNC_METHODS.get(destination_field, 'projects')]
    base = Base(
        workspace_id=workspace_id,
        source_field=source_field,
        destination_field=destination_field,
        platform_class_name=platform_class_name,
        sync_after=sync_after,
        sdk_connection=sdk_connection,
        destination_sync_methods=destination_sync_methods
    )

    return base


def get_platform_connection(workspace_id):
    """
    Get platform connection
    """
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    return platform
