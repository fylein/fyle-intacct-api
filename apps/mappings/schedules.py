from datetime import datetime

from django_q.models import Schedule

from apps.mappings.tasks import (
	schedule_auto_map_employees,
    schedule_auto_map_charge_card_employees
)
from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import MappingSetting


def schedule_or_delete_auto_mapping_tasks(configuration: Configuration):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    schedule_or_delete_fyle_import_tasks(configuration)
    schedule_auto_map_employees(
        employee_mapping_preference=configuration.auto_map_employees, workspace_id=int(configuration.workspace_id))

    if not configuration.auto_map_employees:
        schedule_auto_map_charge_card_employees(workspace_id=int(configuration.workspace_id))

def schedule_or_delete_fyle_import_tasks(configuration: Configuration, instance: MappingSetting = None):
    """
    Schedule or delete Fyle import tasks based on the configuration.
    :param configuration: Workspace Configuration Instance
    :param instance: Mapping Setting Instance
    :return: None
    """
    # Check if there is a task to be scheduled
    task_to_be_scheduled = MappingSetting.objects.filter(
        import_to_fyle=True,
        workspace_id=configuration.workspace_id,
        source_field=instance.source_field
    ).first()

    # Check if any of the configuration flags are True
    if task_to_be_scheduled or (
            configuration.import_categories or
            configuration.import_vendors_as_merchants or
            configuration.import_tax_codes
    ):
        Schedule.objects.update_or_create(
            func='apps.mappings.queues.chain_import_fields_to_fyle',
            args='{}'.format(configuration.workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': datetime.now()
            }
        )
        return

    # If none of the conditions are met, delete the existing schedule
    Schedule.objects.filter(
        func='apps.mappings.queues.chain_import_fields_to_fyle',
        args='{}'.format(configuration.workspace_id)
    ).delete()