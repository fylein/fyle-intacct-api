from typing import Dict

from apps.mappings.tasks import schedule_projects_creation

from .models import WorkspaceGeneralSettings
from apps.sage_intacct.tasks import schedule_ap_payment_creation, schedule_sage_objects_status_sync,\
    schedule_sage_intacct_reimbursement_creation, schedule_reimbursements_sync


def create_or_update_general_settings(general_settings_payload: Dict, workspace_id):
    """
    Create or update general settings
    :param workspace_id:
    :param general_settings_payload: general settings payload
    :return:
    """

    general_settings, _ = WorkspaceGeneralSettings.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'reimbursable_expenses_object': general_settings_payload['reimbursable_expenses_object'],
            'corporate_credit_card_expenses_object': general_settings_payload['corporate_credit_card_expenses_object'],
            'import_projects': general_settings_payload['import_projects'],
            'sync_fyle_to_sage_intacct_payments': general_settings_payload['sync_fyle_to_sage_intacct_payments'],
            'sync_sage_intacct_to_fyle_payments': general_settings_payload['sync_sage_intacct_to_fyle_payments']
        }
    )

    schedule_projects_creation(import_projects=general_settings.import_projects, workspace_id=workspace_id)

    schedule_ap_payment_creation(general_settings.sync_fyle_to_sage_intacct_payments, workspace_id)

    schedule_sage_intacct_reimbursement_creation(general_settings.sync_fyle_to_sage_intacct_payments, workspace_id)

    schedule_sage_objects_status_sync(
        sync_sage_to_fyle_payments=general_settings.sync_sage_intacct_to_fyle_payments,
        workspace_id=workspace_id
    )

    schedule_reimbursements_sync(
        sync_sage_intacct_to_fyle_payments=general_settings.sync_sage_intacct_to_fyle_payments,
        workspace_id=workspace_id
    )
   
    return general_settings
