import logging
from datetime import datetime

from django.dispatch import receiver
from django.db.models.signals import post_save

from fyle_accounting_mappings.models import MappingSetting

from apps.workspaces.models import Configuration
from apps.sage_intacct.helpers import schedule_payment_sync
from apps.fyle.helpers import add_expense_id_to_expense_group_settings
from apps.mappings.helpers import schedule_or_delete_auto_mapping_tasks

logger = logging.getLogger(__name__)
logger.level = logging.INFO


@receiver(post_save, sender=Configuration)
def run_post_configration_triggers(sender: type[Configuration], instance: Configuration, **kwargs) -> None:
    """
    :param sender: Sender Class
    :param instance: Row Instance of Sender Class
    :return: None
    """
    logger.info('Running post configuration triggers for workspace_id: %s', instance.workspace_id)

    if instance.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
        add_expense_id_to_expense_group_settings(int(instance.workspace_id))

        MappingSetting.objects.update_or_create(
            destination_field='CHARGE_CARD_NUMBER',
            workspace_id=instance.workspace_id,
            defaults={
                'source_field': 'CORPORATE_CARD',
                'import_to_fyle': False,
                'is_custom': False
            }
        )

    if instance.corporate_credit_card_expenses_object != 'CHARGE_CARD_TRANSACTION':
        mapping_setting = MappingSetting.objects.filter(
            workspace_id=instance.workspace_id,
            source_field='CORPORATE_CARD',
            destination_field='CHARGE_CARD_NUMBER'
        ).first()

        if mapping_setting:
            mapping_setting.delete()

    if (
        not instance.reimbursable_expenses_object
        and instance.auto_create_destination_entity
        and not instance.auto_map_employees
    ):
        # doing this to avoid signal recursion
        Configuration.objects.filter(
            workspace_id=instance.workspace_id
        ).update(auto_map_employees='NAME', updated_at=datetime.now())

    schedule_or_delete_auto_mapping_tasks(configuration=instance)
    schedule_payment_sync(configuration=instance)
