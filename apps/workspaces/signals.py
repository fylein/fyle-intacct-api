import logging
from datetime import datetime, timezone

from django.db.models.signals import post_save
from django.dispatch import receiver
from fyle_accounting_mappings.models import ExpenseAttribute, MappingSetting

from apps.fyle.helpers import add_expense_id_to_expense_group_settings
from apps.mappings.helpers import schedule_or_delete_auto_mapping_tasks
from apps.sage_intacct.helpers import schedule_payment_sync
from apps.workspaces.models import Configuration
from apps.workspaces.tasks import patch_integration_settings_for_unmapped_cards

logger = logging.getLogger(__name__)
logger.level = logging.INFO


CORP_CARD_MAPPING = {
    'CHARGE_CARD_TRANSACTION': {
        'destination_field': 'CHARGE_CARD_NUMBER',
        'source_field': 'CORPORATE_CARD',
        'import_to_fyle': False,
        'is_custom': False,
    },
    'BILL': {
        'destination_field': 'VENDOR',
        'source_field': 'CORPORATE_CARD',
        'import_to_fyle': False,
        'is_custom': False,
    }
}


@receiver(post_save, sender=Configuration)
def run_post_configration_triggers(sender: type[Configuration], instance: Configuration, **kwargs) -> None:
    """
    :param sender: Sender Class
    :param instance: Row Instance of Sender Class
    :return: None
    """
    logger.info('Running post configuration triggers for workspace_id: %s', instance.workspace_id)

    selected = instance.corporate_credit_card_expenses_object
    for export_module_type, params in CORP_CARD_MAPPING.items():
        if selected == export_module_type:
            MappingSetting.objects.update_or_create(
                workspace_id=instance.workspace_id,
                destination_field=params['destination_field'],
                defaults={
                    'source_field': params['source_field'],
                    'import_to_fyle': params['import_to_fyle'],
                    'is_custom': params['is_custom'],
                }
            )
            if export_module_type == 'CHARGE_CARD_TRANSACTION':
                add_expense_id_to_expense_group_settings(int(instance.workspace_id))
        else:
            MappingSetting.objects.filter(
                workspace_id=instance.workspace_id,
                destination_field=params['destination_field'],
                source_field=params['source_field']
            ).delete()

    if (
        not instance.reimbursable_expenses_object
        and instance.auto_create_destination_entity
        and not instance.auto_map_employees
    ):
        # doing this to avoid signal recursion
        Configuration.objects.filter(
            workspace_id=instance.workspace_id
        ).update(auto_map_employees='NAME', updated_at=datetime.now(timezone.utc))

    if instance.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
        unmapped_card_count = ExpenseAttribute.objects.filter(
            attribute_type="CORPORATE_CARD", workspace_id=instance.workspace_id, active=True, mapping__isnull=True
        ).count()
        patch_integration_settings_for_unmapped_cards(workspace_id=instance.workspace_id, unmapped_card_count=unmapped_card_count)
    else:
        patch_integration_settings_for_unmapped_cards(workspace_id=instance.workspace_id, unmapped_card_count=0)

    schedule_or_delete_auto_mapping_tasks(configuration=instance)
    schedule_payment_sync(configuration=instance)
