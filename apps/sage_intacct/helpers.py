from datetime import  datetime, timezone
import logging

from django.utils.module_loading import import_string

from apps.workspaces.models import Configuration, Workspace, SageIntacctCredential

from apps.sage_intacct.tasks import schedule_ap_payment_creation, schedule_sage_intacct_objects_status_sync, \
    schedule_sage_intacct_reimbursement_creation

logger = logging.getLogger(__name__)

def schedule_payment_sync(configuration: Configuration):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    schedule_ap_payment_creation(
        sync_fyle_to_sage_intacct_payments=configuration.sync_fyle_to_sage_intacct_payments,
        workspace_id=configuration.workspace_id
    )

    schedule_sage_intacct_objects_status_sync(
        sync_sage_intacct_to_fyle_payments=configuration.sync_sage_intacct_to_fyle_payments,
        workspace_id=configuration.workspace_id
    )

    schedule_sage_intacct_reimbursement_creation(
        sync_fyle_to_sage_intacct_payments=configuration.sync_fyle_to_sage_intacct_payments,
        workspace_id=configuration.workspace_id
    )

def check_interval_and_sync_dimension(workspace: Workspace, si_credentials: SageIntacctCredential) -> bool:
    """
    Check sync interval and sync dimensions
    :param workspace: Workspace Instance
    :param si_credentials: SageIntacctCredentials Instance

    return: True/False based on sync
    """

    if workspace.destination_synced_at:
        time_interval = datetime.now(timezone.utc) - workspace.source_synced_at

    if workspace.destination_synced_at is None or time_interval.days > 0:
        sync_dimensions(si_credentials, workspace.id)
        return True

    return False

def sync_dimensions(si_credentials: SageIntacctCredential, workspace_id: int, dimensions: list = []) -> None:
    sage_intacct_connection = import_string(
        'apps.sage_intacct.utils.SageIntacctConnector'
    )(si_credentials, workspace_id)
    if not dimensions:
        dimensions = [
            'locations', 'customers', 'departments', 'projects', 'expense_payment_types',
            'classes', 'charge_card_accounts','payment_accounts', 'vendors', 'employees', 'accounts',
            'expense_types', 'items', 'user_defined_dimensions', 'tax_details'
        ]

    for dimension in dimensions:
        try:
            sync = getattr(sage_intacct_connection, 'sync_{}'.format(dimension))
            sync()
        except Exception as exception:
            logger.exception(exception)
