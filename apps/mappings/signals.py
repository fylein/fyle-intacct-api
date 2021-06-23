"""
Mappings Signal
"""
from django.db.models.signals import post_save, pre_save
from typing import List, Dict

from django.dispatch import receiver
from datetime import datetime, timedelta
from apps.workspaces.models import WorkspaceGeneralSettings

from django_q.models import Schedule

from fyle_accounting_mappings.models import MappingSetting
from .tasks import schedule_projects_creation, schedule_cost_centers_creation, schedule_fyle_attributes_creation,\
                        upload_attributes_to_fyle

@receiver(pre_save, sender=MappingSetting)
def run_pre_save(sender, instance: MappingSetting, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """

    if instance.source_field in ['CATEGORY', 'EMPLOYEE', 'COST_CENTER']  or instance.is_custom == False:
        pass

    if instance.is_custom and instance.import_to_fyle and instance.source_field != 'COST_CENTER':
        upload_attributes_to_fyle(
            workspace_id=instance.workspace_id,
            sageintacct_attribute_type=instance.destination_field,
            fyle_attribute_type=instance.source_field,
        )


@receiver(post_save, sender=MappingSetting)
def run_post_save(sender, instance: MappingSetting, **kwargs):
    """
        :param sender: Sender Class
        :param instance: Row instance of Sender Class
        :return: None
    """
    if instance.source_field == 'EMPLOYEE' or instance.source_field == 'CATEGORY':
        pass

    if instance.is_custom and instance.import_to_fyle:
        schedule_fyle_attributes_creation(
            workspace_id=instance.workspace_id,
            sageintacct_attribute_type=instance.destination_field,
            import_to_fyle=instance.import_to_fyle,
        )

        if instance.destination_field == 'PROJECT' and instance.import_to_fyle is False:
           schedule: Schedule = Schedule.objects.filter(
               func='apps.mappings.tasks.auto_create_project_mappings',
               args='{}'.format(instance.workspace_id)
           ).first()

           if schedule:
               schedule.delete()
               general_settings = Configuration.objects.get(
                   workspace_id=self.kwargs['workspace_id']
               )
               general_settings.import_projects = False
               general_settings.save()




