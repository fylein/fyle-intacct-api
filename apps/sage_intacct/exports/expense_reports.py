import logging

from apps.mappings.models import GeneralMapping
from apps.sage_intacct.exports.helpers import format_transaction_date, get_tax_exclusive_amount
from apps.sage_intacct.models import ExpenseReport, ExpenseReportLineitem

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def construct_expense_report_payload(
    workspace_id: int,
    expense_report: ExpenseReport,
    expense_report_line_items: list[ExpenseReportLineitem]
) -> dict:
    """
    Construct Expense Report Payload
    :param workspace_id: Workspace ID
    :param expense_report: ExpenseReport object
    :param expense_report_line_items: ExpenseReportLineitem objects
    :return: constructed expense report payload
    """
    transaction_date = format_transaction_date(expense_report.transaction_date)

    expense_report_line_item_payload = construct_expense_report_line_item_payload(
        workspace_id=workspace_id,
        expense_report_line_items=expense_report_line_items
    )
    expense_report_payload = {
        'state': 'submitted',
        'createdDate': transaction_date,
        'description': expense_report.memo,
        'employee': {
            'id': expense_report.employee_id
        },
        'attachment': {
            'id': str(expense_report.supdoc_id) if expense_report.supdoc_id else None,
        },
        "basePayment": {
            "baseCurrency": expense_report.currency
        },
        "reimbursement": {
            "reimbursementCurrency": expense_report.currency
        },
        'lines': expense_report_line_item_payload
    }

    logger.info("| Payload for the expense report creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, EXPENSE_REPORT_PAYLOAD = {}}}".format(workspace_id, expense_report.expense_group.id, expense_report_payload))

    return expense_report_payload


def construct_expense_report_line_item_payload(
    workspace_id: int,
    expense_report_line_items: ExpenseReportLineitem
) -> dict:
    """
    Construct Expense Report Line Item Payload
    :param workspace_id: Workspace ID
    :param expense_report_line_items: ExpenseReportLineitem objects
    :return: constructed expense report line item payload
    """
    expense_report_lineitem_payloads = []
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    for lineitem in expense_report_line_items:
        transaction_date = format_transaction_date(lineitem.transaction_date)
        tax_exclusive_amount, _ = get_tax_exclusive_amount(
            workspace_id=workspace_id,
            amount=lineitem.amount,
            default_tax_code_id=general_mappings.default_tax_code_id
        )
        amount = lineitem.amount - lineitem.tax_amount if (lineitem.tax_code and lineitem.tax_amount) else tax_exclusive_amount
        amount = round(amount, 2)

        expense_type_id = None
        gl_account_number = None

        if lineitem.expense_type_id:
            expense_type_id = lineitem.expense_type_id
        else:
            gl_account_number = lineitem.gl_account_number

        expense_report_lineitem_payload = {
            'expenseType': {
                'id': expense_type_id
            },
            'glAccount': {
                'id': gl_account_number
            },
            'paymentType': {
                'id': lineitem.expense_payment_type
            },
            'isBillable': lineitem.billable,
            'txnAmount': str(amount),
            'entryDate': transaction_date,
            'paidTo': lineitem.memo,
            'dimensions': {
                'location': {
                    'id': lineitem.location_id
                },
                'department': {
                    'id': lineitem.department_id
                },
                'project': {
                    'id': lineitem.project_id
                },
                'task': {
                    'id': lineitem.task_id
                },
                'costType': {
                    'id': lineitem.cost_type_id
                },
                'item': {
                    'id': lineitem.item_id
                },
                'class': {
                    'id': lineitem.class_id
                },
                'customer': {
                    'id': lineitem.customer_id
                },
                'vendor': {
                    'id': lineitem.vendor_id
                },
                'employee': {
                    'id': lineitem.employee_id
                },
                **{
                    key: {'key': value}
                    for user_defined_dimensions in lineitem.user_defined_dimensions
                    for key, value in user_defined_dimensions.items()
                }
            }
        }

        expense_report_lineitem_payloads.append(expense_report_lineitem_payload)

    return expense_report_lineitem_payloads
