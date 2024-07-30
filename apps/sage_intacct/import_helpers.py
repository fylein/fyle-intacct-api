import logging

from django.utils.module_loading import import_string
from apps.workspaces.models import Configuration, SageIntacctCredential

from sageintacctsdk.exceptions import WrongParamsError

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def get_or_create_credit_card_vendor(workspace_id: int, configuration: Configuration, merchant: str = None):
    """
    Get or create default vendor
    :param merchant: Fyle Expense Merchant
    :param workspace_id: Workspace Id
    :return:
    """
    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = import_string('apps.sage_intacct.utils.SageIntacctConnector')(sage_intacct_credentials, workspace_id)

    vendor = None

    if (
        merchant
        and not configuration.import_vendors_as_merchants
        and configuration.corporate_credit_card_expenses_object
        and configuration.auto_create_merchants_as_vendors
        and (
            configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION'
            or (
                configuration.corporate_credit_card_expenses_object == 'JOURNAL_ENTRY'
                and configuration.use_merchant_in_journal_line
            )
        )
    ):
        try:
            vendor = sage_intacct_connection.get_or_create_vendor(merchant, create=True)
        except WrongParamsError as bad_request:
            logger.info(bad_request.response)

    if not vendor:
        vendor = sage_intacct_connection.get_or_create_vendor('Credit Card Misc', create=True)

    return vendor
