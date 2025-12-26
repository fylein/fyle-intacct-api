from apps.workspaces.models import Configuration
from apps.sage_intacct.exports.bills import (
    construct_bill_payload,
    construct_bill_line_item_payload,
)
from tests.test_sageintacct.fixtures import data


def test_construct_bill_payload(db, create_bill):
    """
    Test construct_bill_payload creates correct payload
    """
    workspace_id = 1
    bill, bill_lineitems = create_bill

    payload = construct_bill_payload(
        workspace_id=workspace_id,
        bill=bill,
        bill_line_items=bill_lineitems
    )

    assert payload is not None
    for key in data['bill_payload_expected_keys']:
        assert key in payload
    assert payload['vendor']['id'] == bill.vendor_id
    assert payload['currency']['baseCurrency'] == bill.currency
    assert payload['currency']['txnCurrency'] == bill.currency
    assert len(payload['lines']) == len(bill_lineitems)


def test_construct_bill_payload_with_tax_codes(db, create_bill):
    """
    Test construct_bill_payload with import_tax_codes enabled
    """
    workspace_id = 1
    bill, bill_lineitems = create_bill

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.import_tax_codes = True
    configuration.save()

    payload = construct_bill_payload(
        workspace_id=workspace_id,
        bill=bill,
        bill_line_items=bill_lineitems
    )

    assert payload is not None
    assert 'isTaxInclusive' in payload
    assert payload['isTaxInclusive'] is False
    assert 'taxSolution' in payload


def test_construct_bill_payload_without_supdoc_id(db, create_bill):
    """
    Test construct_bill_payload when supdoc_id is None
    """
    workspace_id = 1
    bill, bill_lineitems = create_bill

    bill.supdoc_id = None
    bill.save()

    payload = construct_bill_payload(
        workspace_id=workspace_id,
        bill=bill,
        bill_line_items=bill_lineitems
    )

    assert payload['attachment']['id'] is None


def test_construct_bill_line_item_payload(db, create_bill):
    """
    Test construct_bill_line_item_payload creates correct line item payload
    """
    workspace_id = 1
    _, bill_lineitems = create_bill

    line_item_payloads = construct_bill_line_item_payload(
        workspace_id=workspace_id,
        bill_line_items=bill_lineitems
    )

    assert line_item_payloads is not None
    assert len(line_item_payloads) == len(bill_lineitems)

    for payload in line_item_payloads:
        for key in data['bill_line_item_expected_keys']:
            assert key in payload
        for key in data['bill_dimensions_expected_keys']:
            assert key in payload['dimensions']


def test_construct_bill_line_item_payload_with_tax_code(db, create_bill):
    """
    Test construct_bill_line_item_payload with tax code in line item
    """
    workspace_id = 1
    _, bill_lineitems = create_bill

    for lineitem in bill_lineitems:
        lineitem.tax_code = 'TAX001'
        lineitem.tax_amount = 10.0
        lineitem.save()

    line_item_payloads = construct_bill_line_item_payload(
        workspace_id=workspace_id,
        bill_line_items=bill_lineitems
    )

    assert line_item_payloads is not None
    for payload in line_item_payloads:
        assert payload['taxEntries'][0]['purchasingTaxDetail']['id'] == 'TAX001'


def test_construct_bill_line_item_payload_refund_case(db, create_bill):
    """
    Test construct_bill_line_item_payload for refund (negative amount)
    """
    workspace_id = 1
    _, bill_lineitems = create_bill

    for lineitem in bill_lineitems:
        lineitem.amount = -50.0
        lineitem.save()

    line_item_payloads = construct_bill_line_item_payload(
        workspace_id=workspace_id,
        bill_line_items=bill_lineitems
    )

    assert line_item_payloads is not None
    for payload in line_item_payloads:
        assert float(payload['txnAmount']) <= 0
