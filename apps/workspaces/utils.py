from typing import Dict

from apps.mappings.tasks import schedule_auto_map_employees, schedule_categories_creation, \
    schedule_auto_map_charge_card_employees

from .models import WorkspaceGeneralSettings
from apps.sage_intacct.tasks import schedule_ap_payment_creation, schedule_sage_intacct_objects_status_sync,\
    schedule_sage_intacct_reimbursement_creation, schedule_fyle_reimbursements_sync
from apps.fyle.models import ExpenseGroupSettings
from fyle_intacct_api.utils import assert_valid


def create_or_update_general_settings(general_settings_payload: Dict, workspace_id):
    """
    Create or update general settings
    :param workspace_id:
    :param general_settings_payload: general settings payload
    :return:
    """

    assert_valid('auto_map_employees' in general_settings_payload, 'auto_map_employees field is missing')

    if general_settings_payload['auto_map_employees']:
        assert_valid(general_settings_payload['auto_map_employees'] in ['EMAIL', 'NAME', 'EMPLOYEE_CODE'],
                    'auto_map_employees can have only EMAIL / NAME / EMPLOYEE_CODE')

    general_settings, _ = WorkspaceGeneralSettings.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'reimbursable_expenses_object': general_settings_payload['reimbursable_expenses_object'],
            'corporate_credit_card_expenses_object': general_settings_payload['corporate_credit_card_expenses_object'],
            'import_projects': general_settings_payload['import_projects'],
            'import_categories': general_settings_payload['import_categories'],
            'sync_fyle_to_sage_intacct_payments': general_settings_payload['sync_fyle_to_sage_intacct_payments'],
            'sync_sage_intacct_to_fyle_payments': general_settings_payload['sync_sage_intacct_to_fyle_payments'],
            'auto_map_employees': general_settings_payload['auto_map_employees'],
            'auto_create_destination_entity': general_settings_payload['auto_create_destination_entity']
        }
    )

    if general_settings.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
        expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)

        ccc_expense_group_fields = expense_group_settings.corporate_credit_card_expense_group_fields
        ccc_expense_group_fields.append('expense_id')
        expense_group_settings.corporate_credit_card_expense_group_fields = list(set(ccc_expense_group_fields))

        expense_group_settings.save()

    schedule_categories_creation(import_categories=general_settings.import_categories, workspace_id=workspace_id)

    schedule_ap_payment_creation(general_settings.sync_fyle_to_sage_intacct_payments, workspace_id)

    schedule_sage_intacct_reimbursement_creation(general_settings.sync_fyle_to_sage_intacct_payments, workspace_id)

    schedule_sage_intacct_objects_status_sync(
        sync_sage_to_fyle_payments=general_settings.sync_sage_intacct_to_fyle_payments,
        workspace_id=workspace_id
    )

    schedule_fyle_reimbursements_sync(
        sync_sage_intacct_to_fyle_payments=general_settings.sync_sage_intacct_to_fyle_payments,
        workspace_id=workspace_id
    )

    schedule_auto_map_employees(general_settings_payload['auto_map_employees'], workspace_id)

    schedule_auto_map_charge_card_employees(workspace_id)
   
    return general_settings
