"""
Fyle Signal
"""
import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.sage_intacct.dependent_fields import create_dependent_custom_field_in_fyle
from apps.sage_intacct.dependent_fields import schedule_dependent_field_imports

from .helpers import connect_to_platform
from .models import DependentFieldSetting


logger = logging.getLogger(__name__)
logger.level = logging.INFO


@receiver(pre_save, sender=DependentFieldSetting)
def run_pre_save_dependent_field_settings_triggers(sender, instance: DependentFieldSetting, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    # Patch alert - Skip creating dependent fields if they're already created
    if instance.cost_code_field_id:
        return

    platform = connect_to_platform(instance.workspace_id)

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


@receiver(post_save, sender=DependentFieldSetting)
def run_post_save_dependent_field_settings_triggers(sender, instance: DependentFieldSetting, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    schedule_dependent_field_imports(instance.workspace_id, instance.is_import_enabled)
