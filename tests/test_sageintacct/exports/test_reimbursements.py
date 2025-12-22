import pytest
from datetime import datetime

from apps.sage_intacct.exports.reimbursements import construct_reimbursement_payload
from tests.test_sageintacct.fixtures import data


@pytest.mark.django_db
def test_construct_reimbursement_payload(create_sage_intacct_reimbursement):
    """
    Test construct_reimbursement_payload creates correct payload
    """
    workspace_id = 1
    reimbursement, reimbursement_lineitems = create_sage_intacct_reimbursement

    payload = construct_reimbursement_payload(
        workspace_id=workspace_id,
        reimbursement=reimbursement,
        reimbursement_line_items=reimbursement_lineitems
    )

    assert payload is not None
    for key in data['reimbursement_payload_expected_keys']:
        assert key in payload
    assert payload['bankaccountid'] == reimbursement.account_id
    assert payload['employeeid'] == reimbursement.employee_id
    assert payload['paymentmethod'] == 'Cash'
    assert 'year' in payload['paymentdate']
    assert 'month' in payload['paymentdate']
    assert 'day' in payload['paymentdate']
    assert 'eppaymentrequestitem' in payload['eppaymentrequestitems']


@pytest.mark.django_db
def test_construct_reimbursement_payload_line_items(create_sage_intacct_reimbursement):
    """
    Test construct_reimbursement_payload creates correct line item structure
    """
    workspace_id = 1
    reimbursement, reimbursement_lineitems = create_sage_intacct_reimbursement

    payload = construct_reimbursement_payload(
        workspace_id=workspace_id,
        reimbursement=reimbursement,
        reimbursement_line_items=reimbursement_lineitems
    )

    line_items = payload['eppaymentrequestitems']['eppaymentrequestitem']

    assert len(line_items) == len(reimbursement_lineitems)

    for i, line_item in enumerate(line_items):
        for key in data['reimbursement_line_item_expected_keys']:
            assert key in line_item
        assert line_item['key'] == reimbursement_lineitems[i].record_key
        assert line_item['paymentamount'] == reimbursement_lineitems[i].amount


@pytest.mark.django_db
def test_construct_reimbursement_payload_payment_date(create_sage_intacct_reimbursement):
    """
    Test construct_reimbursement_payload has correct payment date format
    """
    workspace_id = 1
    reimbursement, reimbursement_lineitems = create_sage_intacct_reimbursement

    payload = construct_reimbursement_payload(
        workspace_id=workspace_id,
        reimbursement=reimbursement,
        reimbursement_line_items=reimbursement_lineitems
    )

    today = datetime.now()
    assert payload['paymentdate']['year'] == today.strftime('%Y')
    assert payload['paymentdate']['month'] == today.strftime('%m')
    assert payload['paymentdate']['day'] == today.strftime('%d')
