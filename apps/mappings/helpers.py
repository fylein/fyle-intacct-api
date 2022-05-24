from apps.mappings.tasks import schedule_categories_creation, schedule_auto_map_employees, \
    schedule_auto_map_charge_card_employees, schedule_tax_groups_creation, schedule_vendors_as_merchants_creation
from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import MappingSetting, ExpenseAttribute


def schedule_or_delete_auto_mapping_tasks(configuration: Configuration):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    schedule_categories_creation(
        import_categories=configuration.import_categories, workspace_id=configuration.workspace_id)
    schedule_auto_map_employees(
        employee_mapping_preference=configuration.auto_map_employees, workspace_id=int(configuration.workspace_id))
    
    schedule_tax_groups_creation(import_tax_codes=configuration.import_tax_codes, workspace_id=configuration.workspace_id)

    if not configuration.auto_map_employees:
        schedule_auto_map_charge_card_employees(workspace_id=int(configuration.workspace_id))

    schedule_vendors_as_merchants_creation(
        import_vendors_as_merchants=configuration.import_vendors_as_merchants, workspace_id=configuration.workspace_id)
