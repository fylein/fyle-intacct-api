import logging
from datetime import datetime, timezone

from django_q.models import Schedule
from django.utils.module_loading import import_string

from apps.fyle.models import DependentFieldSetting
from apps.workspaces.models import (
    Workspace,
    Configuration,
    SageIntacctCredential
)

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def schedule_payment_sync(configuration: Configuration) -> None:
    """
    Schedule Payment Sync
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    Schedule.objects.update_or_create(
        func='apps.sage_intacct.queue.trigger_sync_payments',
        args='{}'.format(configuration.workspace_id),
        defaults={
            'schedule_type': Schedule.MINUTES,
            'minutes': 24 * 60,
            'next_run': datetime.now(timezone.utc),
        }
    )


def check_interval_and_sync_dimension(workspace_id: int, **kwargs) -> bool:
    """
    Check sync interval and sync dimensions
    :param workspace_id: Workspace ID
    :param kwargs: Keyword Arguments
    :return: Boolean
    """
    workspace = Workspace.objects.get(pk=workspace_id)
    try:
        if workspace.destination_synced_at:
            time_interval = datetime.now(timezone.utc) - workspace.source_synced_at

        if workspace.destination_synced_at is None or time_interval.days > 0:
            sync_dimensions(workspace.id)
            workspace.destination_synced_at = datetime.now()
            workspace.save(update_fields=['destination_synced_at'])
    except SageIntacctCredential.DoesNotExist:
        logger.info('Sage Intacct credentials does not exist workspace_id - %s', workspace_id)


def is_dependent_field_import_enabled(workspace_id: int) -> bool:
    """
    Check if dependent field import is enabled
    :param workspace_id: Workspace ID
    :return: Boolean
    """
    return DependentFieldSetting.objects.filter(workspace_id=workspace_id).exists()


def sync_dimensions(workspace_id: int, dimensions: list = []) -> None:
    """
    Sync Dimensions
    :param si_credentials: Sage Intacct Credentials
    :param workspace_id: Workspace ID
    :param dimensions: Dimensions List
    :return: None
    """
    sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace_id)
    sage_intacct_connection = import_string(
        'apps.sage_intacct.utils.SageIntacctConnector'
    )(sage_intacct_credentials, workspace_id)

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
