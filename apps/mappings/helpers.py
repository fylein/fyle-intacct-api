from apps.mappings.tasks import schedule_categories_creation, schedule_auto_map_employees, \
    schedule_auto_map_charge_card_employees
from apps.workspaces.models import Configuration
from apps.mappings.models import GeneralMapping
from django_q.tasks import Chain
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
    if not configuration.auto_map_employees:
        schedule_auto_map_charge_card_employees(workspace_id=int(configuration.workspace_id))


def validate_and_trigger_auto_map_employees(workspace_id: int):
    general_mappings = GeneralMapping.objects.filter(workspace_id=workspace_id).first()
    configuration = Configuration.objects.get(workspace_id=workspace_id)

    chain = Chain()

    if configuration.auto_map_employees:
        chain.append('apps.mappings.tasks.async_auto_map_employees', workspace_id)

    if general_mappings and general_mappings.default_charge_card_name:
        chain.append('apps.mappings.tasks.async_auto_map_charge_card_account', workspace_id)

    chain.run()