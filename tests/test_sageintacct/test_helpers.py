from apps.workspaces.models import Configuration, Workspace
from apps.sage_intacct.helpers import (
    schedule_payment_sync,
    check_interval_and_sync_dimension,
    is_dependent_field_import_enabled
)


def test_schedule_payment_sync(db):
    """
    Test schedule_payment_sync
    """
    workspace_id = 1
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    schedule_payment_sync(configuration)


def test_check_interval_and_sync_dimension(db):
    """
    Test check_interval_and_sync_dimension
    """
    workspace_id = 1

    workspace = Workspace.objects.get(id=workspace_id)

    check_interval_and_sync_dimension(workspace_id)

    workspace.destination_synced_at = None
    workspace.save()

    check_interval_and_sync_dimension(workspace_id)


def test_is_dependent_field_import_enabled(db, create_dependent_field_setting):
    """
    Test is_dependent_field_import_enabled
    """
    assert is_dependent_field_import_enabled(1) == True
