"""
Workspace Signals
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from fyle_accounting_mappings.models import DestinationAttribute
from apps.fyle.helpers import add_expense_id_to_expense_group_settings
from apps.sage_intacct.helpers import schedule_payment_sync
from apps.mappings.helpers import schedule_or_delete_auto_mapping_tasks

from .models import Configuration, SageIntacctCredential


@receiver(post_save, sender=Configuration)
def run_post_configration_triggers(sender, instance: Configuration, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row Instance of Sender Class
    :return: None
    """
    if instance.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
        add_expense_id_to_expense_group_settings(int(instance.workspace_id))

    schedule_or_delete_auto_mapping_tasks(configuration=instance)
    schedule_payment_sync(configuration=instance)


@receiver(post_save, sender=SageIntacctCredential)
def run_post_save_sage_intacct_credentials(sender, instance: SageIntacctCredential, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row Instance of Sender Class
    :return: Nonw
    """
    attribute = {
        'attribute_type': 'LOCATION_ENTITY',
        'destination_id': 'top-level',
        'active': True,
        'display_name': 'Location Entity',
        'value': 'Top Level',
        'detail': {
            'country': 'Top Level'
        }
    }

    DestinationAttribute.create_or_update_destination_attribute(attribute, int(instance.workspace_id))