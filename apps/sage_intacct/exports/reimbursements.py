import logging
from datetime import datetime

from apps.sage_intacct.models import SageIntacctReimbursement, SageIntacctReimbursementLineitem

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def construct_reimbursement_payload(
    workspace_id: int,
    reimbursement: SageIntacctReimbursement,
    reimbursement_line_items: list[SageIntacctReimbursementLineitem]
) -> dict:
    """
    Construct Reimbursement payload
    :param workspace_id: Workspace ID
    :param reimbursement: SageIntacctReimbursement object
    :param reimbursement_line_items: SageIntacctReimbursementLineitem objects
    :return: constructed Reimbursement payload
    """
    reimbursement_line_items_payload = []

    for line_item in reimbursement_line_items:
        reimbursement_line_item_payload = {
            'key': line_item.record_key,
            'paymentamount': line_item.amount
        }

        reimbursement_line_items_payload.append(reimbursement_line_item_payload)

    reimbursement_payload = {
        'bankaccountid': reimbursement.account_id,
        'employeeid': reimbursement.employee_id,
        'memo': reimbursement.memo,
        'paymentmethod': 'Cash',
        'paymentdate': {
            'year': datetime.now().strftime('%Y'),
            'month': datetime.now().strftime('%m'),
            'day': datetime.now().strftime('%d')
        },
        'eppaymentrequestitems': {
            'eppaymentrequestitem': reimbursement_line_items_payload
        },
        'paymentdescription': reimbursement.payment_description
    }

    logger.info("| Payload for the reimbursement creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, REIMBURSEMENT_PAYLOAD = {}}}".format(workspace_id, reimbursement.expense_group.id, reimbursement_payload))

    return reimbursement_payload
