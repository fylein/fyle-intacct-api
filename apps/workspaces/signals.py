"""
Workspace Signals
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.fyle.helpers import add_expense_id_to_expense_group_settings
from apps.sage_intacct.helpers import schedule_payment_sync
from apps.mappings.helpers import schedule_or_delete_auto_mapping_tasks

from .models import Configuration


@receiver(post_save, sender=Configuration)
def run_post_configration_triggers(sender, instance: Configuration, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row Instance of Sender Class
    :return: None
    """
    if instance.corporate_credit_card_expenses_object == 'CHARGE CARD TRANSACTIONS':
        add_expense_id_to_expense_group_settings(int(instance.workspace_id))

    schedule_or_delete_auto_mapping_tasks(configuration=instance)
    schedule_payment_sync(configuration=instance)
