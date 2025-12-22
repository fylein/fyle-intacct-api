import pytest

from apps.sage_intacct.exports.expense_reports import (
    construct_expense_report_payload,
    construct_expense_report_line_item_payload,
)
from tests.test_sageintacct.fixtures import data


@pytest.mark.django_db
def test_construct_expense_report_payload(create_expense_report):
    """
    Test construct_expense_report_payload creates correct payload
    """
    workspace_id = 1
    expense_report, expense_report_lineitems = create_expense_report

    payload = construct_expense_report_payload(
        workspace_id=workspace_id,
        expense_report=expense_report,
        expense_report_line_items=expense_report_lineitems
    )

    assert payload is not None
    for key in data['expense_report_payload_expected_keys']:
        assert key in payload
    assert payload['state'] == 'submitted'
    assert payload['employee']['id'] == expense_report.employee_id
    assert payload['basePayment']['baseCurrency'] == expense_report.currency
    assert len(payload['lines']) == len(expense_report_lineitems)


@pytest.mark.django_db
def test_construct_expense_report_payload_without_supdoc_id(create_expense_report):
    """
    Test construct_expense_report_payload when supdoc_id is None
    """
    workspace_id = 1
    expense_report, expense_report_lineitems = create_expense_report

    expense_report.supdoc_id = None
    expense_report.save()

    payload = construct_expense_report_payload(
        workspace_id=workspace_id,
        expense_report=expense_report,
        expense_report_line_items=expense_report_lineitems
    )

    assert payload['attachment']['id'] is None


@pytest.mark.django_db
def test_construct_expense_report_line_item_payload(create_expense_report):
    """
    Test construct_expense_report_line_item_payload creates correct line item payload
    """
    workspace_id = 1
    _, expense_report_lineitems = create_expense_report

    line_item_payloads = construct_expense_report_line_item_payload(
        workspace_id=workspace_id,
        expense_report_line_items=expense_report_lineitems
    )

    assert line_item_payloads is not None
    assert len(line_item_payloads) == len(expense_report_lineitems)

    for payload in line_item_payloads:
        for key in data['expense_report_line_item_expected_keys']:
            assert key in payload
        for key in data['expense_report_dimensions_expected_keys']:
            assert key in payload['dimensions']


@pytest.mark.django_db
def test_construct_expense_report_line_item_payload_with_expense_type(create_expense_report):
    """
    Test construct_expense_report_line_item_payload with expense_type_id
    """
    workspace_id = 1
    _, expense_report_lineitems = create_expense_report

    for lineitem in expense_report_lineitems:
        lineitem.expense_type_id = 'EXP_TYPE_001'
        lineitem.gl_account_number = None
        lineitem.save()

    line_item_payloads = construct_expense_report_line_item_payload(
        workspace_id=workspace_id,
        expense_report_line_items=expense_report_lineitems
    )

    for payload in line_item_payloads:
        assert payload['expenseType']['id'] == 'EXP_TYPE_001'
        assert payload['glAccount']['id'] is None


@pytest.mark.django_db
def test_construct_expense_report_line_item_payload_with_gl_account(create_expense_report):
    """
    Test construct_expense_report_line_item_payload with gl_account_number
    """
    workspace_id = 1
    _, expense_report_lineitems = create_expense_report

    for lineitem in expense_report_lineitems:
        lineitem.expense_type_id = None
        lineitem.gl_account_number = 'GL_ACC_001'
        lineitem.save()

    line_item_payloads = construct_expense_report_line_item_payload(
        workspace_id=workspace_id,
        expense_report_line_items=expense_report_lineitems
    )

    for payload in line_item_payloads:
        assert payload['expenseType']['id'] is None
        assert payload['glAccount']['id'] == 'GL_ACC_001'


@pytest.mark.django_db
def test_construct_expense_report_line_item_payload_with_tax(create_expense_report):
    """
    Test construct_expense_report_line_item_payload with tax code and amount
    """
    workspace_id = 1
    _, expense_report_lineitems = create_expense_report

    for lineitem in expense_report_lineitems:
        lineitem.tax_code = 'TAX001'
        lineitem.tax_amount = 10.0
        lineitem.save()

    line_item_payloads = construct_expense_report_line_item_payload(
        workspace_id=workspace_id,
        expense_report_line_items=expense_report_lineitems
    )

    assert line_item_payloads is not None
    assert len(line_item_payloads) > 0
