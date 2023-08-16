from datetime import datetime
from django_q.models import Schedule
from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import MappingSetting


def schedule_or_delete_fyle_import_tasks(configuration: Configuration, instance: MappingSetting = None):
    """
    Schedule or delete Fyle import tasks based on the configuration.
    :param configuration: Workspace Configuration Instance
    :param instance: Mapping Setting Instance
    :return: None
    """
    # Check if there is a task to be scheduled
    if instance:
        task_to_be_scheduled = MappingSetting.objects.filter(
            import_to_fyle=True,
            workspace_id=configuration.workspace_id,
            source_field=instance.source_field
        ).first()

    # Check if any of the configuration flags are True
    if (instance and task_to_be_scheduled) or (configuration.import_projects):
        Schedule.objects.update_or_create(
            func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
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
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(configuration.workspace_id)
    ).delete()
