import logging
from datetime import datetime

from apps.mappings.models import GeneralMapping
from apps.workspaces.models import Configuration
from apps.sage_intacct.models import Bill, BillLineitem
from apps.sage_intacct.exports.helpers import get_tax_exclusive_amount, get_tax_solution_id_or_none

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def construct_bill_payload(
    workspace_id: int,
    bill: Bill,
    bill_lineitems: list[BillLineitem]
) -> dict:
    """
    Construct bill payload
    :param workspace_id: Workspace ID
    :param bill: Bill object
    :param bill_lineitems: BillLineitem objects
    :return: constructed bill payload
    """
    configuration = Configuration.objects.get(workspace_id=workspace_id)

    transaction_date = bill.transaction_date.strftime('%Y-%m-%d')
    current_date = datetime.today().strftime('%Y-%m-%d')

    bill_line_item_payload = construct_bill_line_item_payload(
        workspace_id=workspace_id,
        bill_line_items=bill_lineitems
    )

    bill_payload = {
        'createdDate': transaction_date,
        'vendor': {
            'id': bill.vendor_id
        },
        'billNumber': bill.memo,
        'dueDate': current_date,
        'currency': {
            'baseCurrency': bill.currency,
            'txnCurrency': bill.currency,
        },
        'attachment': {
            'id': bill.supdoc_id,
        },
        'lines': bill_line_item_payload
    }

    if configuration.import_tax_codes:
        bill_payload.update({
            'isTaxInclusive': False,
            'taxSolution': {
                'id': get_tax_solution_id_or_none(
                    workspace_id=workspace_id,
                    lineitems=bill_lineitems
                )
            }
        })

    logger.info("| Payload for the bill creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, BILL_PAYLOAD = {}}}".format(workspace_id, bill.expense_group.id, bill_payload))

    return bill_payload


def construct_bill_line_item_payload(
    workspace_id: int,
    bill_line_items: list[BillLineitem]
) -> dict:
    """
    Construct bill line item payload
    :param workspace_id: Workspace ID
    :param bill_line_items: BillLineitem objects
    :return: constructed bill line item payload
    """
    bill_line_item_payloads = []
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    for lineitem in bill_line_items:
        tax_exclusive_amount, _ = get_tax_exclusive_amount(
            workspace_id=workspace_id,
            amount=abs(lineitem.amount),
            default_tax_code_id=general_mappings.default_tax_code_id
        )

        bill_line_item_payload = {
            'glAccount': {
                'id': lineitem.gl_account_number
            },
            'txnAmount': str(lineitem.amount - lineitem.tax_amount if (lineitem.tax_code and lineitem.tax_amount) else tax_exclusive_amount),
            'totalTxnAmount': str(lineitem.amount),
            'memo': lineitem.memo,
            'allocation': {
                'id': lineitem.allocation_id
            },
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
                'customer': {
                    'id': lineitem.customer_id
                },
                'item': {
                    'id': lineitem.item_id
                },
                'task': {
                    'id': lineitem.task_id
                },
                'costType': {
                    'id': lineitem.cost_type_id
                },
                'class': {
                    'id': lineitem.class_id
                },
                **{
                    key: {'id': value}
                    for user_defined_dimensions in lineitem.user_defined_dimensions
                    for key, value in user_defined_dimensions.items()
                }
            },
            'project': {
                'isBillable': lineitem.billable
            },
            'taxEntries': [{
                'purchasingTaxDetail': {
                    'id': lineitem.tax_code if (lineitem.tax_code and lineitem.tax_amount) else general_mappings.default_tax_code_id
                }
            }]
        }

        # case of a refund
        if lineitem.amount < 0:
            bill_line_item_payload['txnAmount'] = str(round(-(abs(lineitem.amount) - abs(lineitem.tax_amount) if (lineitem.tax_code and lineitem.tax_amount) else tax_exclusive_amount), 2))

        bill_line_item_payloads.append(bill_line_item_payload)

    return bill_line_item_payloads
