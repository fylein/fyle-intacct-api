from datetime import datetime

from django_q.models import Schedule

from apps.mappings.tasks import (
    schedule_auto_map_employees,
    schedule_auto_map_charge_card_employees
)
from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import MappingSetting
from apps.fyle.models import DependentFieldSetting
from apps.mappings.imports.schedules import schedule_or_delete_fyle_import_tasks as new_schedule_or_delete_fyle_import_tasks


def schedule_or_delete_auto_mapping_tasks(configuration: Configuration):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    schedule_or_delete_fyle_import_tasks(configuration)
    new_schedule_or_delete_fyle_import_tasks(configuration)
    schedule_auto_map_employees(
        employee_mapping_preference=configuration.auto_map_employees, workspace_id=int(configuration.workspace_id))

    if not configuration.auto_map_employees:
        schedule_auto_map_charge_card_employees(workspace_id=int(configuration.workspace_id))


def schedule_or_delete_fyle_import_tasks(configuration: Configuration):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    project_mapping = MappingSetting.objects.filter(
        source_field='PROJECT',
        workspace_id=configuration.workspace_id,
        import_to_fyle=True
    ).first()
    dependent_fields = DependentFieldSetting.objects.filter(workspace_id=configuration.workspace_id, is_import_enabled=True).first()

    if project_mapping and dependent_fields:
        start_datetime = datetime.now()
        Schedule.objects.update_or_create(
            func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
            cluster='import',
            args='{}'.format(configuration.workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    elif not (project_mapping and dependent_fields):
        Schedule.objects.filter(
            func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
            args='{}'.format(configuration.workspace_id)
        ).delete()
