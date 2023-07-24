"""
Workspace Signals
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from fyle_accounting_mappings.models import MappingSetting

from apps.fyle.helpers import add_expense_id_to_expense_group_settings
from apps.sage_intacct.helpers import schedule_payment_sync
from apps.mappings.helpers import schedule_or_delete_auto_mapping_tasks

from .models import Configuration
from ..fyle.models import ExpenseGroupSettings


@receiver(post_save, sender=Configuration)
def run_post_configration_triggers(sender, instance: Configuration, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row Instance of Sender Class
    :return: None
    """
    if instance.corporate_credit_card_expenses_object in {'EXPENSE_REPORT', 'BILL', 'JOURNAL_ENTRY'}:
        expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=int(instance.workspace_id))
        expense_group_settings.import_card_credits = True
        expense_group_settings.save()

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
    
    if instance.corporate_credit_card_expenses_object != 'CHARGE_CARD_TRANSACTION' :
        mapping_setting = MappingSetting.objects.filter(
            workspace_id=instance.workspace_id,
            source_field='CORPORATE_CARD',
            destination_field='CHARGE_CARD_NUMBER'
        ).first()

        if mapping_setting:
            mapping_setting.delete()

    schedule_or_delete_auto_mapping_tasks(configuration=instance)
    schedule_payment_sync(configuration=instance)
