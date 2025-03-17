import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from apps.fyle.tasks import re_run_skip_export_rule
from apps.sage_intacct.dependent_fields import create_dependent_custom_field_in_fyle

from apps.fyle.helpers import connect_to_platform
from apps.fyle.models import DependentFieldSetting, ExpenseFilter

logger = logging.getLogger(__name__)
logger.level = logging.INFO


@receiver(pre_save, sender=DependentFieldSetting)
def run_pre_save_dependent_field_settings_triggers(sender: type[DependentFieldSetting], instance: DependentFieldSetting, **kwargs) -> None:
    """
    Ensure dependent fields are created before saving.
    """
    if getattr(instance, "_skip_signal", False):
        return  # Prevent infinite loop

    # If both cost_code and cost_type are created in Fyle then return
    if instance.cost_code_field_id and instance.cost_type_field_id:
        return  # Already set

    platform = connect_to_platform(instance.workspace_id)
    instance.project_field_id = platform.dependent_fields.get_project_field_id()

    # Create cost code field if not exists in Fyle
    if not instance.cost_code_field_id:
        cost_code = create_dependent_custom_field_in_fyle(
            workspace_id=instance.workspace_id,
            fyle_attribute_type=instance.cost_code_field_name,
            platform=platform,
            source_placeholder=instance.cost_code_placeholder,
            parent_field_id=instance.project_field_id,
        )
        instance.cost_code_field_id = cost_code['data']['id']

    # Create cost type field if not exists in Fyle and cost code field is created
    if not instance.cost_type_field_id and instance.cost_type_field_name:
        cost_type = create_dependent_custom_field_in_fyle(
            workspace_id=instance.workspace_id,
            fyle_attribute_type=instance.cost_type_field_name,
            platform=platform,
            source_placeholder=instance.cost_type_placeholder,
            parent_field_id=instance.cost_code_field_id,
        )
        instance.cost_type_field_id = cost_type['data']['id']

        # Ensure instance is already saved before updating fields
        if instance.pk:
            instance._skip_signal = True
            instance.save(update_fields=['cost_type_field_id'])


@receiver(post_save, sender=ExpenseFilter)
def run_post_save_expense_filters(sender: type[ExpenseFilter], instance: ExpenseFilter, **kwargs) -> None:
    """
    :param sender: Sender Class
    :param instance: Row Instance of Sender Class
    :return: None
    """
    if instance.join_by is None:
        try:
            re_run_skip_export_rule(instance.workspace)
        except Exception as e:
            logger.error(f'Error while processing expense filter for workspace: {instance.workspace.id} - {str(e)}')
            raise ValidationError('Failed to process expense filter')
