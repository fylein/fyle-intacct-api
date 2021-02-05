from typing import Dict

from .models import WorkspaceGeneralSettings
from apps.sage_intacct.tasks import schedule_payment_creation, schedule_sage_objects_status_sync, schedule_reimbursements_sync

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
            'sync_fyle_to_sage_payments': general_settings_payload['sync_fyle_to_sage_payments'],
            'sync_sage_to_fyle_payments': general_settings_payload['sync_sage_to_fyle_payments']
        }
    )

    schedule_payment_creation(general_settings.sync_fyle_to_sage_payments, workspace_id)

    schedule_sage_objects_status_sync(
        sync_sage_to_fyle_payments=general_settings.sync_sage_to_fyle_payments,
        workspace_id=workspace_id
    )

    schedule_reimbursements_sync(
        sync_sage_to_fyle_payments=general_settings.sync_sage_to_fyle_payments,
        workspace_id=workspace_id
    )

    return general_settings
