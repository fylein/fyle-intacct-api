import pytest

from apps.workspaces.models import Configuration
from apps.sage_intacct.exports.charge_card_transactions import (
    construct_charge_card_transaction_payload,
    construct_charge_card_transaction_line_item_payload,
)
from tests.test_sageintacct.fixtures import data


@pytest.mark.django_db
def test_construct_charge_card_transaction_payload(create_charge_card_transaction):
    """
    Test construct_charge_card_transaction_payload creates correct payload
    """
    workspace_id = 1
    cct, cct_lineitems = create_charge_card_transaction

    payload = construct_charge_card_transaction_payload(
        workspace_id=workspace_id,
        charge_card_transaction=cct,
        charge_card_transaction_line_items=cct_lineitems
    )

    assert payload is not None
    for key in data['charge_card_transaction_payload_expected_keys']:
        assert key in payload
    assert payload['creditCardAccount']['id'] == cct.charge_card_id
    assert payload['currency']['baseCurrency'] == cct.currency
    assert payload['currency']['txnCurrency'] == cct.currency
    assert len(payload['lines']) == len(cct_lineitems)


@pytest.mark.django_db
def test_construct_charge_card_transaction_payload_with_tax_codes(create_charge_card_transaction):
    """
    Test construct_charge_card_transaction_payload with import_tax_codes enabled
    """
    workspace_id = 1
    cct, cct_lineitems = create_charge_card_transaction

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.import_tax_codes = True
    configuration.save()

    payload = construct_charge_card_transaction_payload(
        workspace_id=workspace_id,
        charge_card_transaction=cct,
        charge_card_transaction_line_items=cct_lineitems
    )

    assert payload['isInclusiveTax'] is True


@pytest.mark.django_db
def test_construct_charge_card_transaction_payload_without_tax_codes(create_charge_card_transaction):
    """
    Test construct_charge_card_transaction_payload without import_tax_codes
    """
    workspace_id = 1
    cct, cct_lineitems = create_charge_card_transaction

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.import_tax_codes = False
    configuration.save()

    payload = construct_charge_card_transaction_payload(
        workspace_id=workspace_id,
        charge_card_transaction=cct,
        charge_card_transaction_line_items=cct_lineitems
    )

    assert payload['isInclusiveTax'] is False


@pytest.mark.django_db
def test_construct_charge_card_transaction_payload_without_supdoc_id(create_charge_card_transaction):
    """
    Test construct_charge_card_transaction_payload when supdoc_id is None
    """
    workspace_id = 1
    cct, cct_lineitems = create_charge_card_transaction

    cct.supdoc_id = None
    cct.save()

    payload = construct_charge_card_transaction_payload(
        workspace_id=workspace_id,
        charge_card_transaction=cct,
        charge_card_transaction_line_items=cct_lineitems
    )

    assert payload['attachment']['id'] is None


@pytest.mark.django_db
def test_construct_charge_card_transaction_line_item_payload(create_charge_card_transaction):
    """
    Test construct_charge_card_transaction_line_item_payload creates correct payload
    """
    workspace_id = 1
    cct, cct_lineitems = create_charge_card_transaction

    line_item_payloads = construct_charge_card_transaction_line_item_payload(
        workspace_id=workspace_id,
        charge_card_transaction=cct,
        charge_card_transaction_line_items=cct_lineitems
    )

    assert line_item_payloads is not None
    assert len(line_item_payloads) == len(cct_lineitems)

    for payload in line_item_payloads:
        for key in data['charge_card_transaction_line_item_expected_keys']:
            assert key in payload
        for key in data['charge_card_transaction_dimensions_expected_keys']:
            assert key in payload['dimensions']


@pytest.mark.django_db
def test_construct_charge_card_transaction_line_item_payload_with_tax(create_charge_card_transaction):
    """
    Test construct_charge_card_transaction_line_item_payload with tax code
    """
    workspace_id = 1
    cct, cct_lineitems = create_charge_card_transaction

    for lineitem in cct_lineitems:
        lineitem.tax_code = 'TAX001'
        lineitem.tax_amount = 10.0
        lineitem.save()

    line_item_payloads = construct_charge_card_transaction_line_item_payload(
        workspace_id=workspace_id,
        charge_card_transaction=cct,
        charge_card_transaction_line_items=cct_lineitems
    )

    for payload in line_item_payloads:
        assert payload['taxEntries'][0]['purchasingTaxDetail']['id'] == 'TAX001'
