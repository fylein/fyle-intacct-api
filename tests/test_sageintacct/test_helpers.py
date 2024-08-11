from apps.sage_intacct.helpers import (
    schedule_payment_sync, check_interval_and_sync_dimension, is_dependent_field_import_enabled
)
from apps.workspaces.models import Configuration, Workspace, SageIntacctCredential


def test_schedule_payment_sync(db):
    workspace_id = 1
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    schedule_payment_sync(configuration)


def test_check_interval_and_sync_dimension(db):
    workspace_id = 1

    workspace = Workspace.objects.get(id=workspace_id)

    check_interval_and_sync_dimension(workspace_id)

    workspace.destination_synced_at = None
    workspace.save()

    check_interval_and_sync_dimension(workspace_id)


def test_is_dependent_field_import_enabled(db, create_dependent_field_setting):
    assert is_dependent_field_import_enabled(1) == True
