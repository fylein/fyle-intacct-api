from datetime import datetime

from django_q.models import Schedule

from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import MappingSetting


# TODO: merge all import tasks to this function, remove old schedules and functions
def schedule_or_delete_fyle_import_tasks(configuration: Configuration):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    project_mapping = MappingSetting.objects.filter(source_field='PROJECT', workspace_id=configuration.workspace_id).first()
    if configuration.import_categories or (project_mapping and project_mapping.import_to_fyle) or configuration.import_vendors_as_merchants:
        start_datetime = datetime.now()
        Schedule.objects.update_or_create(
            func='apps.mappings.queues.chain_import_fields_to_fyle',
            args='{}'.format(configuration.workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    elif not configuration.import_categories and not (project_mapping and project_mapping.import_to_fyle) and not configuration.import_vendors_as_merchants:
        Schedule.objects.filter(
            func='apps.mappings.queues.chain_import_fields_to_fyle',
            args='{}'.format(configuration.workspace_id)
        ).delete()
