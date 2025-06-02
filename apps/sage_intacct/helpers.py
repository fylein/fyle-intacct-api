import logging
from datetime import datetime, timezone

from django.utils.module_loading import import_string

from apps.fyle.models import DependentFieldSetting
from apps.workspaces.models import (
    Workspace,
    Configuration,
    SageIntacctCredential
)
from apps.sage_intacct.queue import (
    schedule_ap_payment_creation,
    schedule_fyle_reimbursements_sync,
    schedule_sage_intacct_objects_status_sync,
    schedule_sage_intacct_reimbursement_creation,
)

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def schedule_payment_sync(configuration: Configuration) -> None:
    """
    Schedule Payment Sync
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    schedule_sage_intacct_objects_status_sync(
        sync_sage_intacct_to_fyle_payments=configuration.sync_sage_intacct_to_fyle_payments,
        workspace_id=configuration.workspace_id
    )

    schedule_fyle_reimbursements_sync(
        sync_sage_intacct_to_fyle_payments=configuration.sync_sage_intacct_to_fyle_payments,
        workspace_id=configuration.workspace_id
    )

    schedule_ap_payment_creation(
        configuration=configuration,
        workspace_id=configuration.workspace_id
    )

    schedule_sage_intacct_reimbursement_creation(
        configuration=configuration,
        workspace_id=configuration.workspace_id
    )


def check_interval_and_sync_dimension(workspace_id: int, **kwargs) -> bool:
    """
    Check sync interval and sync dimensions
    :param workspace_id: Workspace ID
    :param kwargs: Keyword Arguments
    :return: Boolean
    """
    workspace = Workspace.objects.get(pk=workspace_id)
    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace.id)

    if workspace.destination_synced_at:
        time_interval = datetime.now(timezone.utc) - workspace.source_synced_at

    if workspace.destination_synced_at is None or time_interval.days > 0:
        sync_dimensions(sage_intacct_credentials, workspace.id)
        workspace.destination_synced_at = datetime.now()
        workspace.save(update_fields=['destination_synced_at'])


def is_dependent_field_import_enabled(workspace_id: int) -> bool:
    """
    Check if dependent field import is enabled
    :param workspace_id: Workspace ID
    :return: Boolean
    """
    return DependentFieldSetting.objects.filter(workspace_id=workspace_id).exists()


def sync_dimensions(si_credentials: SageIntacctCredential, workspace_id: int, dimensions: list = []) -> None:
    """
    Sync Dimensions
    :param si_credentials: Sage Intacct Credentials
    :param workspace_id: Workspace ID
    :param dimensions: Dimensions List
    :return: None
    """
    sage_intacct_connection = import_string(
        'apps.sage_intacct.utils.SageIntacctConnector'
    )(si_credentials, workspace_id)

    update_timestamp = False
    if not dimensions:
        dimensions = [
            'locations', 'customers', 'departments', 'tax_details', 'projects',
            'expense_payment_types', 'classes', 'charge_card_accounts','payment_accounts',
            'vendors', 'employees', 'accounts', 'expense_types', 'items', 'user_defined_dimensions', 'allocations'
        ]
        update_timestamp = True

    for dimension in dimensions:
        try:
            sync = getattr(sage_intacct_connection, 'sync_{}'.format(dimension))
            sync()
        except Exception as exception:
            logger.info(exception)

    if update_timestamp:
        # Update destination_synced_at to current time only when full refresh happens
        workspace = Workspace.objects.get(pk=workspace_id)

        workspace.destination_synced_at = datetime.now()
        workspace.save(update_fields=['destination_synced_at'])
