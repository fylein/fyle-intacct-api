import logging
from typing import Optional
from datetime import datetime, timedelta, timezone

from fyle_accounting_mappings.models import ExpenseAttribute, DestinationAttribute

from fyle_integrations_imports.modules.projects import Project
from apps.mappings.schedules import schedule_or_delete_fyle_import_tasks as new_schedule_or_delete_fyle_import_tasks
from apps.mappings.tasks import schedule_auto_map_accounting_fields
from apps.workspaces.models import Configuration
from apps.workspaces.models import Configuration as WorkspaceGeneralSettings
from apps.workspaces.tasks import patch_integration_settings_for_unmapped_cards
from fyle_integrations_imports.models import ImportLog

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def schedule_or_delete_auto_mapping_tasks(configuration: Configuration) -> None:
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    new_schedule_or_delete_fyle_import_tasks(configuration)
    schedule_auto_map_accounting_fields(workspace_id=configuration.workspace_id)


def prepend_code_to_name(prepend_code_in_name: bool, value: str, code: str = None) -> str:
    """
    Format the attribute name based on the use_code_in_naming flag
    :param prepend_code_in_name: Boolean flag to prepend code in name
    :param value: Value of the attribute
    :param code: Code of the attribute
    :return: Formatted attribute name
    """
    if prepend_code_in_name and code:
        return "{}: {}".format(code, value)
    return value


def is_project_sync_allowed(import_log: ImportLog = None) -> bool:
    """
    Check if job sync is allowed
    :param import_log: Import Log Instance
    :return: Boolean
    """
    time_difference = datetime.now(timezone.utc) - timedelta(minutes=30)
    time_difference = time_difference.replace(tzinfo=timezone.utc)

    if (
        not import_log
        or import_log.last_successful_run_at is None
        or import_log.last_successful_run_at < time_difference
    ):
        return True

    return False


def patch_corporate_card_integration_settings(workspace_id: int) -> None:
    """
    Patch integration settings for unmapped corporate cards.
    This is called when corporate card mapping is created or when a corporate card is created via webhook.

    :param workspace_id: Workspace ID
    :return: None
    """
    workspace_general_settings = WorkspaceGeneralSettings.objects.filter(workspace_id=workspace_id).first()

    if workspace_general_settings and workspace_general_settings.corporate_credit_card_expenses_object in ('CHARGE_CARD_TRANSACTION',):
        unmapped_card_count = ExpenseAttribute.objects.filter(
            attribute_type="CORPORATE_CARD", workspace_id=workspace_id, active=True, mapping__isnull=True
        ).count()

        patch_integration_settings_for_unmapped_cards(workspace_id=workspace_id, unmapped_card_count=unmapped_card_count)
        logger.info(f"Patched integration settings for workspace {workspace_id}, unmapped card count: {unmapped_card_count}")


def get_project_billable_field_detail_key(workspace_id: int) -> Optional[str]:
    """
    Get billable field detail key
    :param workspace_id: Workspace ID
    :return: Billable field detail key
    If both export types are different and BILL/ER, return default_bill_billable
    """
    configuration = Configuration.objects.filter(workspace_id=workspace_id).first()

    if configuration:
        if configuration.reimbursable_expenses_object == 'BILL' or configuration.corporate_credit_card_expenses_object == 'BILL':
            return 'default_bill_billable'
        elif configuration.reimbursable_expenses_object == 'EXPENSE_REPORT' or configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            return 'default_expense_report_billable'
        elif configuration.reimbursable_expenses_object in ['BILL', 'EXPENSE_REPORT'] and configuration.corporate_credit_card_expenses_object in ['BILL', 'EXPENSE_REPORT']:
            return 'default_bill_billable'

    return None


def get_project_billable_map(workspace_id: int) -> dict:
    """
    Get current billable values from DestinationAttribute.
    :param workspace_id: Workspace ID
    :return: {destination_id: {'exp_report': bool, 'bill': bool}}
    """
    projects = DestinationAttribute.objects.filter(
        workspace_id=workspace_id,
        attribute_type='PROJECT'
    ).values('destination_id', 'detail')

    return {
        p['destination_id']: {
            'exp_report': p['detail'].get('default_expense_report_billable', False) if p['detail'] else False,
            'bill': p['detail'].get('default_bill_billable', False) if p['detail'] else False
        }
        for p in projects
    }


def sync_changed_project_billable_to_fyle(
    workspace_id: int,
    project_attributes: list,
    existing_billable_map: dict
) -> None:
    """
    Detect billable changes and sync to Fyle.
    :param workspace_id: Workspace ID
    :param project_attributes: List of project attributes from Intacct sync
    :param existing_billable_map: Billable map captured before sync
    """
    billable_field = get_project_billable_field_detail_key(workspace_id)
    if not billable_field:
        return

    # Find projects with billable changes
    changed_pks = []
    for attr in project_attributes:
        dest_id = attr['destination_id']
        if dest_id not in existing_billable_map:
            continue  # New project, handled by imports module

        old = existing_billable_map[dest_id]
        new_detail = attr.get('detail', {})

        if billable_field == 'default_expense_report_billable':
            old_val = old['exp_report']
            new_val = new_detail.get('default_expense_report_billable', False)
        else:
            old_val = old['bill']
            new_val = new_detail.get('default_bill_billable', False)

        if old_val != new_val:
            dest_attr = DestinationAttribute.objects.filter(
                workspace_id=workspace_id,
                attribute_type='PROJECT',
                destination_id=dest_id
            ).first()
            if dest_attr:
                changed_pks.append(dest_attr.pk)

    if not changed_pks:
        return

    logger.info(f'Found {len(changed_pks)} projects with billable changes for workspace {workspace_id}')

    project = Project(
        workspace_id=workspace_id,
        destination_field='PROJECT',
        sync_after=None,
        sdk_connection=None,
        destination_sync_methods=[],
        is_auto_sync_enabled=False,
        project_billable_field_detail_key=billable_field
    )

    project.sync_project_billable_to_fyle(destination_attribute_pks=changed_pks)
