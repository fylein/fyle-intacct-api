from datetime import datetime

from apps.sage_intacct.exports.ap_payments import construct_ap_payment_payload
from tests.test_sageintacct.fixtures import data


def test_construct_ap_payment_payload(db, create_ap_payment):
    """
    Test construct_ap_payment_payload creates correct payload
    """
    workspace_id = 1
    ap_payment, ap_payment_lineitems = create_ap_payment

    payloads = construct_ap_payment_payload(
        workspace_id=workspace_id,
        ap_payment=ap_payment,
        ap_payment_line_items=ap_payment_lineitems
    )

    assert payloads is not None
    assert len(payloads) == len(ap_payment_lineitems)

    for payload in payloads:
        for key in data['ap_payment_payload_expected_keys']:
            assert key in payload
        assert payload['financialEntity']['id'] == ap_payment.payment_account_id
        assert payload['baseCurrency']['currency'] == ap_payment.currency
        assert payload['txnCurrency']['currency'] == ap_payment.currency
        assert payload['paymentMethod'] == 'Cash'
        assert payload['vendor']['id'] == ap_payment.vendor_id


def test_construct_ap_payment_payload_details(db, create_ap_payment):
    """
    Test construct_ap_payment_payload creates correct details structure
    """
    workspace_id = 1
    ap_payment, ap_payment_lineitems = create_ap_payment

    payloads = construct_ap_payment_payload(
        workspace_id=workspace_id,
        ap_payment=ap_payment,
        ap_payment_line_items=ap_payment_lineitems
    )

    for i, payload in enumerate(payloads):
        details = payload['details']
        assert len(details) == 1

        detail = details[0]
        for key in data['ap_payment_detail_expected_keys']:
            assert key in detail
        assert detail['txnCurrency']['paymentAmount'] == str(ap_payment_lineitems[i].amount)
        assert detail['bill']['key'] == ap_payment_lineitems[i].record_key


def test_construct_ap_payment_payload_payment_date(db, create_ap_payment):
    """
    Test construct_ap_payment_payload has today's date as payment date
    """
    workspace_id = 1
    ap_payment, ap_payment_lineitems = create_ap_payment

    payloads = construct_ap_payment_payload(
        workspace_id=workspace_id,
        ap_payment=ap_payment,
        ap_payment_line_items=ap_payment_lineitems
    )

    today_date = datetime.today().strftime('%Y-%m-%d')

    for payload in payloads:
        assert payload['paymentDate'] == today_date


def test_construct_ap_payment_payload_multiple_line_items(db, create_ap_payment):
    """
    Test construct_ap_payment_payload with multiple line items
    """
    workspace_id = 1
    ap_payment, ap_payment_lineitems = create_ap_payment

    payloads = construct_ap_payment_payload(
        workspace_id=workspace_id,
        ap_payment=ap_payment,
        ap_payment_line_items=ap_payment_lineitems
    )

    assert len(payloads) == len(ap_payment_lineitems)

    for i, payload in enumerate(payloads):
        assert payload['details'][0]['bill']['key'] == ap_payment_lineitems[i].record_key
