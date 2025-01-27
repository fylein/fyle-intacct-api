import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.sage_intacct.dependent_fields import create_dependent_custom_field_in_fyle

from apps.fyle.helpers import connect_to_platform
from apps.fyle.models import DependentFieldSetting

logger = logging.getLogger(__name__)
logger.level = logging.INFO


@receiver(pre_save, sender=DependentFieldSetting)
def run_pre_save_dependent_field_settings_triggers(sender: type[DependentFieldSetting], instance: DependentFieldSetting, **kwargs) -> None:
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    # Patch alert - Skip creating dependent fields if they're already created
    if instance.cost_code_field_id:
        return

    platform = connect_to_platform(instance.workspace_id)

    instance.project_field_id = platform.dependent_fields.get_project_field_id()

    cost_code = create_dependent_custom_field_in_fyle(
        workspace_id=instance.workspace_id,
        fyle_attribute_type=instance.cost_code_field_name,
        platform=platform,
        source_placeholder=instance.cost_code_placeholder,
        parent_field_id=instance.project_field_id,
    )

    instance.cost_code_field_id = cost_code['data']['id']

    cost_type = create_dependent_custom_field_in_fyle(
        workspace_id=instance.workspace_id,
        fyle_attribute_type=instance.cost_type_field_name,
        platform=platform,
        source_placeholder=instance.cost_type_placeholder,
        parent_field_id=instance.cost_code_field_id,
    )
    instance.cost_type_field_id = cost_type['data']['id']
