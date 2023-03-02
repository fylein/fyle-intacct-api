"""
Mappings Signal
"""
import logging
import json

from rest_framework.exceptions import ValidationError

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django_q.tasks import async_task

from fyle_accounting_mappings.models import MappingSetting, ExpenseAttribute
from fyle.platform.exceptions import WrongParamsError
from apps.mappings.tasks import schedule_projects_creation, schedule_cost_centers_creation, schedule_fyle_attributes_creation,\
    upload_attributes_to_fyle


logger = logging.getLogger(__name__)


@receiver(post_save, sender=MappingSetting)
def run_post_mapping_settings_triggers(sender, instance: MappingSetting, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    if instance.source_field == 'PROJECT':
        schedule_projects_creation(instance.import_to_fyle, int(instance.workspace_id))
    
    if instance.source_field == 'COST_CENTER':
        schedule_cost_centers_creation(instance.import_to_fyle, int(instance.workspace_id))
    
    if instance.is_custom:
        schedule_fyle_attributes_creation(int(instance.workspace_id))


@receiver(pre_save, sender=MappingSetting)
def run_pre_mapping_settings_triggers(sender, instance: MappingSetting, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    default_attributes = ['EMPLOYEE', 'CATEGORY', 'PROJECT', 'COST_CENTER', 'TAX_GROUP']

    instance.source_field = instance.source_field.upper().replace(' ', '_')
    parent_field = instance.expense_field.source_field_id if instance.expense_field else None

    if instance.source_field not in default_attributes:
        try:
            upload_attributes_to_fyle(
                workspace_id=int(instance.workspace_id),
                sageintacct_attribute_type=instance.destination_field,
                fyle_attribute_type=instance.source_field,
                parent_field=parent_field
            )
        except WrongParamsError as error:
            logger.error(
                'Error while creating %s workspace_id - %s in Fyle %s %s',
                instance.source_field, instance.workspace_id, error.message, {'error': error.response}
            )
            if error.response:
                response = json.loads(error.response)
                if response and 'message' in response and \
                    response['message'] == ('duplicate key value violates unique constraint '
                    '"idx_expense_fields_org_id_field_name_is_enabled_is_custom"'):
                    raise ValidationError({
                        'message': 'Duplicate custom field name',
                        'field_name': instance.source_field
                    })

        async_task(
            'apps.mappings.tasks.auto_create_expense_fields_mappings',
            int(instance.workspace_id),
            instance.destination_field,
            instance.source_field,
            parent_field
        )
