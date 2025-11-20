import logging
from datetime import datetime
from apps.sage_intacct.models import APPayment, APPaymentLineitem

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def construct_ap_payment_payload(workspace_id: int, ap_payment: APPayment, ap_payment_line_items: list[APPaymentLineitem]) -> dict:
    """
    Construct AP Payment payload
    :param workspace_id: Workspace ID
    :param ap_payment: APPayment object
    :param ap_payment_lineitems: APPaymentLineItem objects
    :return: constructed AP Payment payload
    """
    ap_payment_line_items_payloads = []

    today_date = datetime.today().strftime('%Y-%m-%d')

    for line_item in ap_payment_line_items:
        ap_payment_line_items_payload = {
            "financialEntity": {
                "id": ap_payment.payment_account_id
            },
            "paymentDate": today_date,
            "description": ap_payment.description,
            "baseCurrency": {
                "currency": ap_payment.currency
            },
            "txnCurrency": {
                "currency": ap_payment.currency
            },
            "paymentMethod": "Cash",
            "vendor": {
                "id": ap_payment.vendor_id
            },
            "details": [
                {
                    "txnCurrency": {
                        "paymentAmount": str(line_item.amount)
                    },
                    "bill": {
                        "key": line_item.record_key
                    }
                }
            ]
        }

        ap_payment_line_items_payloads.append(ap_payment_line_items_payload)

    logger.info("| Payload for the AP Payment creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, AP_PAYMENT_PAYLOAD = {}}}".format(workspace_id, ap_payment.expense_group.id, ap_payment_line_items_payloads))

    return ap_payment_line_items_payloads
