from unittest import mock

from fyle_accounting_mappings.models import DestinationAttribute

from apps.workspaces.models import Configuration
from apps.mappings.models import GeneralMapping
from apps.sage_intacct.exports.journal_entries import (
    construct_journal_entry_payload,
    construct_debit_line_payload,
    construct_credit_line_payload,
    construct_single_itemized_credit_line,
    construct_multiple_itemized_credit_line,
)
from tests.test_sageintacct.fixtures import data


def test_construct_journal_entry_payload(db, create_journal_entry):
    """
    Test construct_journal_entry_payload creates correct payload
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    with mock.patch('apps.sage_intacct.exports.journal_entries.settings') as mock_settings:
        mock_settings.BRAND_ID = 'fyle'

        payload = construct_journal_entry_payload(
            workspace_id=workspace_id,
            journal_entry=journal_entry,
            journal_entry_line_items=journal_entry_lineitems
        )

    assert payload is not None
    for key in data['journal_entry_payload_expected_keys']:
        assert key in payload
    assert payload['glJournal']['id'] == 'FYLE_JE'
    assert len(payload['lines']) > 0


def test_construct_journal_entry_payload_with_tax_codes(db, create_journal_entry):
    """
    Test construct_journal_entry_payload with import_tax_codes enabled
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.import_tax_codes = True
    configuration.save()

    with mock.patch('apps.sage_intacct.exports.journal_entries.settings') as mock_settings:
        mock_settings.BRAND_ID = 'fyle'

        payload = construct_journal_entry_payload(
            workspace_id=workspace_id,
            journal_entry=journal_entry,
            journal_entry_line_items=journal_entry_lineitems
        )

    assert 'tax' in payload
    assert payload['tax']['taxImplication'] == 'inbound'


def test_construct_journal_entry_payload_with_brand_id_em(db, create_journal_entry):
    """
    Test construct_journal_entry_payload with EM brand
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    with mock.patch('apps.sage_intacct.exports.journal_entries.settings') as mock_settings:
        mock_settings.BRAND_ID = 'em'

        payload = construct_journal_entry_payload(
            workspace_id=workspace_id,
            journal_entry=journal_entry,
            journal_entry_line_items=journal_entry_lineitems
        )

    assert payload['glJournal']['id'] == 'EM_JOURNAL'


def test_construct_journal_entry_payload_without_supdoc_id(db, create_journal_entry):
    """
    Test construct_journal_entry_payload when supdoc_id is None
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    journal_entry.supdoc_id = None
    journal_entry.save()

    with mock.patch('apps.sage_intacct.exports.journal_entries.settings') as mock_settings:
        mock_settings.BRAND_ID = 'fyle'

        payload = construct_journal_entry_payload(
            workspace_id=workspace_id,
            journal_entry=journal_entry,
            journal_entry_line_items=journal_entry_lineitems
        )

    assert payload['attachment']['id'] is None


def test_construct_debit_line_payload(db, create_journal_entry):
    """
    Test construct_debit_line_payload creates correct debit lines
    """
    workspace_id = 1
    _, journal_entry_lineitems = create_journal_entry

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    debit_payloads = construct_debit_line_payload(
        workspace_id=workspace_id,
        line_items=journal_entry_lineitems,
        general_mappings=general_mappings
    )

    assert debit_payloads is not None
    assert len(debit_payloads) == len(journal_entry_lineitems)

    for payload in debit_payloads:
        for key in data['journal_entry_debit_line_expected_keys']:
            assert key in payload


def test_construct_debit_line_payload_with_negative_amount(db, create_journal_entry):
    """
    Test construct_debit_line_payload with negative amount (refund)
    """
    workspace_id = 1
    _, journal_entry_lineitems = create_journal_entry

    for lineitem in journal_entry_lineitems:
        lineitem.amount = -50.0
        lineitem.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    debit_payloads = construct_debit_line_payload(
        workspace_id=workspace_id,
        line_items=journal_entry_lineitems,
        general_mappings=general_mappings
    )

    for payload in debit_payloads:
        assert payload['txnType'] == 'credit'


def test_construct_debit_line_payload_with_allocation(db, create_journal_entry):
    """
    Test construct_debit_line_payload with allocation
    """
    workspace_id = 1
    _, journal_entry_lineitems = create_journal_entry

    DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='ALLOCATION',
        display_name='Allocation',
        value='ALLOC001',
        destination_id='ALLOC001',
        detail={'location': 'LOC001', 'department': 'DEPT001'},
        active=True
    )

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    debit_payloads = construct_debit_line_payload(
        workspace_id=workspace_id,
        line_items=journal_entry_lineitems,
        general_mappings=general_mappings
    )

    assert debit_payloads is not None
    assert len(debit_payloads) == len(journal_entry_lineitems)


def test_construct_credit_line_payload_single_line(db, create_journal_entry):
    """
    Test construct_credit_line_payload with single credit line configuration
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.je_single_credit_line = True
    configuration.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    credit_payloads = construct_credit_line_payload(
        workspace_id=workspace_id,
        journal_entry=journal_entry,
        line_items=journal_entry_lineitems,
        configuration=configuration,
        general_mappings=general_mappings
    )

    assert credit_payloads is not None


def test_construct_credit_line_payload_multiple_lines(db, create_journal_entry):
    """
    Test construct_credit_line_payload with multiple credit lines configuration
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.je_single_credit_line = False
    configuration.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    credit_payloads = construct_credit_line_payload(
        workspace_id=workspace_id,
        journal_entry=journal_entry,
        line_items=journal_entry_lineitems,
        configuration=configuration,
        general_mappings=general_mappings
    )

    assert credit_payloads is not None
    assert len(credit_payloads) == len(journal_entry_lineitems)


def test_construct_single_itemized_credit_line(db, create_journal_entry):
    """
    Test construct_single_itemized_credit_line creates correct payload
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    credit_payloads = construct_single_itemized_credit_line(
        workspace_id=workspace_id,
        journal_entry=journal_entry,
        line_items=journal_entry_lineitems,
        general_mappings=general_mappings
    )

    assert credit_payloads is not None

    for payload in credit_payloads:
        for key in data['journal_entry_credit_line_expected_keys']:
            assert key in payload
        assert payload['description'] == 'Total Credit Line'


def test_construct_single_itemized_credit_line_skips_zero_amount(db, create_journal_entry):
    """
    Test construct_single_itemized_credit_line skips zero total amount
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    for lineitem in journal_entry_lineitems:
        lineitem.amount = 0
        lineitem.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    credit_payloads = construct_single_itemized_credit_line(
        workspace_id=workspace_id,
        journal_entry=journal_entry,
        line_items=journal_entry_lineitems,
        general_mappings=general_mappings
    )

    assert len(credit_payloads) == 0


def test_construct_single_itemized_credit_line_refund_case(db, create_journal_entry):
    """
    Test construct_single_itemized_credit_line with negative amount (refund)
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    for lineitem in journal_entry_lineitems:
        lineitem.amount = -50.0
        lineitem.vendor_id = 'VENDOR001'
        lineitem.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    credit_payloads = construct_single_itemized_credit_line(
        workspace_id=workspace_id,
        journal_entry=journal_entry,
        line_items=journal_entry_lineitems,
        general_mappings=general_mappings
    )

    for payload in credit_payloads:
        assert payload['txnType'] == 'debit'


def test_construct_multiple_itemized_credit_line(db, create_journal_entry):
    """
    Test construct_multiple_itemized_credit_line creates correct payload
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    credit_payloads = construct_multiple_itemized_credit_line(
        workspace_id=workspace_id,
        journal_entry=journal_entry,
        line_items=journal_entry_lineitems,
        configuration=configuration,
        general_mappings=general_mappings
    )

    assert credit_payloads is not None
    assert len(credit_payloads) == len(journal_entry_lineitems)

    for payload in credit_payloads:
        for key in data['journal_entry_credit_line_expected_keys']:
            assert key in payload


def test_construct_multiple_itemized_credit_line_with_billable(db, create_journal_entry):
    """
    Test construct_multiple_itemized_credit_line with billable credit line
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.is_journal_credit_billable = True
    configuration.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    credit_payloads = construct_multiple_itemized_credit_line(
        workspace_id=workspace_id,
        journal_entry=journal_entry,
        line_items=journal_entry_lineitems,
        configuration=configuration,
        general_mappings=general_mappings
    )

    for payload in credit_payloads:
        assert 'isBillable' in payload


def test_construct_multiple_itemized_credit_line_ccc_fund_source(db, create_journal_entry):
    """
    Test construct_multiple_itemized_credit_line with CCC fund source
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    journal_entry.expense_group.fund_source = 'CCC'
    journal_entry.expense_group.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_credit_card_id = 'CC_ACCOUNT_001'
    general_mappings.save()

    credit_payloads = construct_multiple_itemized_credit_line(
        workspace_id=workspace_id,
        journal_entry=journal_entry,
        line_items=journal_entry_lineitems,
        configuration=configuration,
        general_mappings=general_mappings
    )

    for payload in credit_payloads:
        assert payload['glAccount']['id'] == 'CC_ACCOUNT_001'


def test_construct_multiple_itemized_credit_line_personal_fund_source(db, create_journal_entry):
    """
    Test construct_multiple_itemized_credit_line with PERSONAL fund source
    """
    workspace_id = 1
    journal_entry, journal_entry_lineitems = create_journal_entry

    journal_entry.expense_group.fund_source = 'PERSONAL'
    journal_entry.expense_group.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_gl_account_id = 'GL_ACCOUNT_001'
    general_mappings.save()

    credit_payloads = construct_multiple_itemized_credit_line(
        workspace_id=workspace_id,
        journal_entry=journal_entry,
        line_items=journal_entry_lineitems,
        configuration=configuration,
        general_mappings=general_mappings
    )

    for payload in credit_payloads:
        assert payload['glAccount']['id'] == 'GL_ACCOUNT_001'
