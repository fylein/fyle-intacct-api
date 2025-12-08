import logging

from apps.mappings.models import GeneralMapping
from apps.workspaces.models import Configuration
from apps.sage_intacct.exports.helpers import format_transaction_date, get_tax_exclusive_amount
from apps.sage_intacct.models import ChargeCardTransaction, ChargeCardTransactionLineitem

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def construct_charge_card_transaction_payload(
    workspace_id: int,
    charge_card_transaction: ChargeCardTransaction,
    charge_card_transaction_line_items: list[ChargeCardTransactionLineitem]
) -> dict:
    """
    Construct charge card transaction payload
    :param workspace_id: Workspace ID
    :param charge_card_transaction: ChargeCardTransaction object
    :param charge_card_transaction_line_items: ChargeCardTransactionLineitem objects
    :return: constructed charge_card_transaction payload
    """
    configuration = Configuration.objects.get(workspace_id=workspace_id)

    transaction_date = format_transaction_date(charge_card_transaction.transaction_date)

    charge_card_transaction_lineitem_payload = construct_charge_card_transaction_line_item_payload(
        workspace_id=workspace_id,
        charge_card_transaction=charge_card_transaction,
        charge_card_transaction_line_items=charge_card_transaction_line_items
    )

    charge_card_transaction_payload = {
        'creditCardAccount': {
            'id': charge_card_transaction.charge_card_id
        },
        'txnDate': transaction_date,
        'referenceNumber': charge_card_transaction.reference_no,
        'payee': charge_card_transaction.payee,
        'description': charge_card_transaction.memo,
        'attachment': {
            'id': charge_card_transaction.supdoc_id
        },
        "currency": {
            "baseCurrency": charge_card_transaction.currency,
            "txnCurrency": charge_card_transaction.currency
        },
        'isInclusiveTax': True if configuration.import_tax_codes else False,
        'lines': charge_card_transaction_lineitem_payload,
    }

    logger.info("| Payload for the charge card transaction creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, CHARGE_CARD_TRANSACTION_PAYLOAD = {}}}".format(workspace_id, charge_card_transaction.expense_group.id, charge_card_transaction_payload))

    return charge_card_transaction_payload


def construct_charge_card_transaction_line_item_payload(
    workspace_id: int,
    charge_card_transaction: ChargeCardTransaction,
    charge_card_transaction_line_items: list[ChargeCardTransactionLineitem]
) -> dict:
    """
    Construct charge card transaction line item payload
    :param workspace_id: Workspace ID
    :param charge_card_transaction: ChargeCardTransaction object
    :param charge_card_transaction_line_items: ChargeCardTransactionLineitem objects
    :return: constructed charge card transaction line item payload
    """
    charge_card_transaction_lineitem_payloads = []
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    for lineitem in charge_card_transaction_line_items:
        tax_exclusive_amount, _ = get_tax_exclusive_amount(
            workspace_id=workspace_id,
            amount=lineitem.amount,
            default_tax_code_id=general_mappings.default_tax_code_id
        )

        charge_card_transaction_lineitem_payload = {
            'glAccount': {
                'id': lineitem.gl_account_number
            },
            'description': lineitem.memo,
            'txnAmount': str(lineitem.amount - lineitem.tax_amount if (lineitem.tax_code and lineitem.tax_amount) else tax_exclusive_amount),
            'totalTxnAmount': str(lineitem.amount),
            'dimensions': {
                'department': {
                    'id': lineitem.department_id
                },
                'location': {
                    'id': lineitem.location_id
                },
                'customer': {
                    'id': lineitem.customer_id
                },
                'vendor': {
                    'id': charge_card_transaction.vendor_id
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
                **{
                    key: {'id': value}
                    for user_defined_dimensions in lineitem.user_defined_dimensions
                    for key, value in user_defined_dimensions.items()
                }
            },
            "taxEntries": [
                {
                    "purchasingTaxDetail": {
                        "id": lineitem.tax_code if (lineitem.tax_code and lineitem.tax_amount) else general_mappings.default_tax_code_id
                    }
                }
            ],
            'isBillable': lineitem.billable
        }

        charge_card_transaction_lineitem_payloads.append(charge_card_transaction_lineitem_payload)

    return charge_card_transaction_lineitem_payloads
