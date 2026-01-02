from datetime import datetime
from unittest.mock import Mock

from fyle_accounting_mappings.models import DestinationAttribute

from apps.fyle.models import ExpenseGroup, ExpenseGroupSettings
from apps.mappings.models import GeneralMapping, LocationEntityMapping
from apps.workspaces.models import Configuration
from apps.sage_intacct.models import BillLineitem
from apps.sage_intacct.exports.helpers import (
    format_transaction_date,
    get_tax_exclusive_amount,
    get_tax_solution_id_or_none,
    get_location_id_for_journal_entry,
    get_source_entity_id,
)


def test_format_transaction_date_with_string(db):
    """
    Test format_transaction_date with string input
    """
    date_string = '2024-01-15T10:30:00'
    result = format_transaction_date(date_string)

    assert result == '2024-01-15'


def test_format_transaction_date_with_datetime(db):
    """
    Test format_transaction_date with datetime input
    """
    date_obj = datetime(2024, 1, 15, 10, 30, 0)
    result = format_transaction_date(date_obj)

    assert result == '2024-01-15'


def test_get_tax_exclusive_amount_with_tax_attribute(db):
    """
    Test get_tax_exclusive_amount with tax attribute present
    """
    workspace_id = 1

    DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='TAX_DETAIL',
        display_name='Tax Detail',
        value='GST 10%',
        destination_id='TAX001',
        detail={'tax_rate': 10},
        active=True
    )

    tax_exclusive_amount, tax_amount = get_tax_exclusive_amount(
        workspace_id=workspace_id,
        amount=110,
        default_tax_code_id='TAX001'
    )

    assert tax_exclusive_amount == 100.0
    assert tax_amount == 10.0


def test_get_tax_exclusive_amount_without_tax_attribute(db):
    """
    Test get_tax_exclusive_amount when tax attribute is not found
    """
    workspace_id = 1

    tax_exclusive_amount, tax_amount = get_tax_exclusive_amount(
        workspace_id=workspace_id,
        amount=100,
        default_tax_code_id='NON_EXISTENT_TAX'
    )

    assert tax_exclusive_amount == 100
    assert tax_amount is None


def test_get_tax_solution_id_or_none_with_location_entity(db):
    """
    Test get_tax_solution_id_or_none when location entity is set
    """
    workspace_id = 1

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.location_entity_id = 'LOC_ENTITY_001'
    general_mappings.save()

    line_items = list(BillLineitem.objects.filter(bill__expense_group__workspace_id=workspace_id)[:1])

    if line_items:
        result = get_tax_solution_id_or_none(
            workspace_id=workspace_id,
            line_items=line_items
        )
        assert result is None


def test_get_tax_solution_id_or_none_with_tax_code(db):
    """
    Test get_tax_solution_id_or_none when tax code is present in line item
    """
    workspace_id = 1

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.location_entity_id = None
    general_mappings.default_tax_code_name = 'Default Tax'
    general_mappings.save()

    DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='TAX_DETAIL',
        display_name='Tax Detail',
        value='TestTaxCode',
        destination_id='TAX_TEST',
        detail={'tax_solution_id': 'TAX_SOL_001'},
        active=True
    )

    mock_line_item = Mock()
    mock_line_item.tax_code = 'TestTaxCode'

    result = get_tax_solution_id_or_none(
        workspace_id=workspace_id,
        line_items=[mock_line_item]
    )

    assert result == 'TAX_SOL_001'


def test_get_location_id_for_journal_entry_with_general_mapping(db):
    """
    Test get_location_id_for_journal_entry with default_location_id set
    """
    workspace_id = 1

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_location_id = 'DEFAULT_LOC_001'
    general_mappings.save()

    result = get_location_id_for_journal_entry(workspace_id=workspace_id)

    assert result == 'DEFAULT_LOC_001'


def test_get_location_id_for_journal_entry_with_location_entity_mapping(db):
    """
    Test get_location_id_for_journal_entry with LocationEntityMapping
    """
    workspace_id = 1

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_location_id = None
    general_mappings.save()

    LocationEntityMapping.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'location_entity_name': 'Test Location',
            'destination_id': 'LOC_ENTITY_DEST_001'
        }
    )

    result = get_location_id_for_journal_entry(workspace_id=workspace_id)

    assert result == 'LOC_ENTITY_DEST_001'


def test_get_location_id_for_journal_entry_returns_none(db):
    """
    Test get_location_id_for_journal_entry returns None when no mapping found
    """
    workspace_id = 1

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_location_id = None
    general_mappings.save()

    LocationEntityMapping.objects.filter(workspace_id=workspace_id).delete()

    result = get_location_id_for_journal_entry(workspace_id=workspace_id)

    assert result is None


def test_get_source_entity_id_returns_location_id(db):
    """
    Test get_source_entity_id returns location_id when all conditions are met
    """
    workspace_id = 1

    LocationEntityMapping.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'location_entity_name': 'Top Level',
            'destination_id': 'top_level'
        }
    )

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.je_single_credit_line = True
    configuration.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_location_id = 'DEFAULT_LOC_001'
    general_mappings.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    expense_group.fund_source = 'PERSONAL'
    expense_group.save()

    expense_group_settings, _ = ExpenseGroupSettings.objects.get_or_create(
        workspace_id=workspace_id,
        defaults={
            'reimbursable_expense_group_fields': ['report_id'],
            'corporate_credit_card_expense_group_fields': ['report_id'],
            'expense_state': 'PAYMENT_PROCESSING',
            'reimbursable_export_date_type': 'current_date',
            'ccc_export_date_type': 'current_date'
        }
    )
    expense_group_settings.reimbursable_expense_group_fields = ['report_id']
    expense_group_settings.save()

    result = get_source_entity_id(
        workspace_id=workspace_id,
        configuration=configuration,
        general_mappings=general_mappings,
        expense_group=expense_group
    )

    assert result == 'DEFAULT_LOC_001'


def test_get_source_entity_id_returns_none_when_conditions_not_met(db):
    """
    Test get_source_entity_id returns None when conditions are not met
    """
    workspace_id = 1

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.je_single_credit_line = False
    configuration.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    expense_group = ExpenseGroup.objects.get(id=1)

    result = get_source_entity_id(
        workspace_id=workspace_id,
        configuration=configuration,
        general_mappings=general_mappings,
        expense_group=expense_group
    )

    assert result is None
