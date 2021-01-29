from typing import Dict

from apps.mappings.tasks import schedule_projects_creation

from .models import WorkspaceGeneralSettings

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
            'import_projects': general_settings_payload['import_projects']
        }
    )

    schedule_projects_creation(import_projects=general_settings.import_projects, workspace_id=workspace_id)

    return general_settings
