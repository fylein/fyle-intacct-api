"""
Fyle Signal
"""
import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from fyle_integrations_platform_connector import PlatformConnector

from apps.mappings.tasks import create_dependent_custom_field_in_fyle
from apps.workspaces.models import FyleCredential

from .models import DependentField


logger = logging.getLogger(__name__)
logger.level = logging.INFO


@receiver(pre_save, sender=DependentField)
def run_pre_save_dependent_fields_triggers(sender, instance: DependentField, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    print('instance',instance.id, instance)
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=instance.workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    instance.project_field_id = platform.expense_fields.get_project_field_id()

    cost_code = create_dependent_custom_field_in_fyle(
        workspace_id=instance.workspace_id,
        fyle_attribute_type=instance.cost_code_field_name,
        platform=platform,
        parent_field_id=instance.project_field_id
    )
    instance.cost_code_field_id = cost_code['data']['id']

    cost_type = create_dependent_custom_field_in_fyle(
        workspace_id=instance.workspace_id,
        fyle_attribute_type=instance.cost_type_field_name,
        platform=platform,
        parent_field_id=instance.cost_code_field_id
    )
    instance.cost_type_field_id = cost_type['data']['id']


@receiver(post_save, sender=DependentField)
def run_post_save_dependent_fields_triggers(sender, instance: DependentField, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    print('post_save', instance)
