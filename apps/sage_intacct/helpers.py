from apps.sage_intacct.tasks import schedule_ap_payment_creation, schedule_sage_intacct_objects_status_sync, \
    schedule_sage_intacct_reimbursement_creation
from apps.workspaces.models import Configuration

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
