from datetime import  datetime, timezone
import logging

from django.utils.module_loading import import_string

from fyle_accounting_mappings.models import MappingSetting

from apps.workspaces.models import Configuration, Workspace, SageIntacctCredential

from apps.sage_intacct.tasks import schedule_ap_payment_creation, schedule_sage_intacct_objects_status_sync, \
    schedule_sage_intacct_reimbursement_creation

logger = logging.getLogger(__name__)
logger.level = logging.INFO

def schedule_payment_sync(configuration: Configuration):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    schedule_sage_intacct_objects_status_sync(
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


def is_dependent_field_import_enabled(workspace_id: int) -> bool:
    return True
    # remove hack later
    # use boolean in config table, move away from mapping setting for deps
    # separate table to store destination fields for dependent fields - also think of moving source_field_id to this table instead of expense_filter
    return MappingSetting.objects.filter(workspace_id=workspace_id, destination_field='COST_TYPE').exists()


def sync_dimensions(si_credentials: SageIntacctCredential, workspace_id: int, dimensions: list = []) -> None:
    sage_intacct_connection = import_string(
        'apps.sage_intacct.utils.SageIntacctConnector'
    )(si_credentials, workspace_id)
    if not dimensions:
        # Get green from Shwetabh if we can remove cost types for orgs who don't use dependent fields import
        dimensions = [
            'locations', 'customers', 'departments', 'tax_details', 'projects', 
            'expense_payment_types', 'classes', 'charge_card_accounts','payment_accounts', 
            'vendors', 'employees', 'accounts', 'expense_types', 'items', 'user_defined_dimensions'
        ]
        is_dependent_field_enabled = is_dependent_field_import_enabled(workspace_id)

        if is_dependent_field_enabled:
            # TODO: Add project sync support to sync_cost_types
            # dimensions.remove('projects')
            # dimensions.append('cost_types')
            pass

    for dimension in dimensions:
        try:
            sync = getattr(sage_intacct_connection, 'sync_{}'.format(dimension))
            sync()
        except Exception as exception:
            logger.info(exception)
