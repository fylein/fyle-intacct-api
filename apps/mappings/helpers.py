from datetime import datetime

from django_q.models import Schedule

from apps.mappings.tasks import schedule_auto_map_employees, \
    schedule_auto_map_charge_card_employees, schedule_tax_groups_creation
from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import MappingSetting
from apps.fyle.models import DependentFieldSetting


def schedule_or_delete_auto_mapping_tasks(configuration: Configuration):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    schedule_or_delete_fyle_import_tasks(configuration)
    schedule_auto_map_employees(
        employee_mapping_preference=configuration.auto_map_employees, workspace_id=int(configuration.workspace_id))
    
    schedule_tax_groups_creation(import_tax_codes=configuration.import_tax_codes, workspace_id=configuration.workspace_id)

    if not configuration.auto_map_employees:
        schedule_auto_map_charge_card_employees(workspace_id=int(configuration.workspace_id))


def schedule_or_delete_fyle_import_tasks(configuration: Configuration):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    project_mapping = MappingSetting.objects.filter(source_field='PROJECT', workspace_id=configuration.workspace_id).first()
    dependent_fields = DependentFieldSetting.objects.filter(workspace_id=configuration.workspace_id).first()

    if configuration.import_categories or configuration.import_vendors_as_merchants or (project_mapping and project_mapping.import_to_fyle and dependent_fields and dependent_fields.is_import_enabled):
        start_datetime = datetime.now()
        Schedule.objects.update_or_create(
            func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
            args='{}'.format(configuration.workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    elif not configuration.import_categories and not configuration.import_vendors_as_merchants and not (project_mapping and project_mapping.import_to_fyle and dependent_fields and dependent_fields.is_import_enabled):
        Schedule.objects.filter(
            func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
            args='{}'.format(configuration.workspace_id)
        ).delete()
