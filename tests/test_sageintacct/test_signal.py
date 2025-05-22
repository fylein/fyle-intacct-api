from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import MappingSetting


def test_signal_for_ccc_vendor_mapping(db):
    """
    Test signal for ccc vendor mapping
    """
    configuration = Configuration.objects.get(workspace_id=1)
    configuration.corporate_credit_card_expenses_object = 'BILL'
    configuration.save()

    mapping_setting = MappingSetting.objects.get(workspace_id=1, source_field='CORPORATE_CARD')
    assert mapping_setting.destination_field == 'VENDOR'

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    configuration.save()

    mapping_setting = MappingSetting.objects.get(workspace_id=1, source_field='CORPORATE_CARD')
    assert mapping_setting.destination_field == 'CHARGE_CARD_NUMBER'
