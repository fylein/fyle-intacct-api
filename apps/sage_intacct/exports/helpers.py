from fyle_accounting_mappings.models import DestinationAttribute

from apps.mappings.models import GeneralMapping
from apps.sage_intacct.enums import DestinationAttributeTypeEnum
from apps.sage_intacct.models import (
    BillLineitem,
    JournalEntryLineitem,
    ExpenseReportLineitem,
    ChargeCardTransactionLineitem
)


def get_tax_exclusive_amount(workspace_id: int, amount: float | int, default_tax_code_id: str) -> tuple:
    """
    Get Tax Exclusive Amount
    :param workspace_id: Workspace ID
    :param amount: Amount
    :param default_tax_code_id: Default Tax Code Id
    :return: Tax Exclusive Amount and Tax Amount
    """
    tax_attribute = DestinationAttribute.objects.filter(
        workspace_id=workspace_id,
        attribute_type=DestinationAttributeTypeEnum.TAX_DETAIL.value,
        destination_id=default_tax_code_id
    ).first()

    tax_exclusive_amount = amount
    tax_amount = None
    if tax_attribute:
        tax_rate = int(tax_attribute.detail['tax_rate'])
        tax_exclusive_amount = round((amount - (amount / (tax_rate + 1))), 2)
        tax_amount = round((amount - tax_exclusive_amount), 2)

    return tax_exclusive_amount, tax_amount


def get_tax_solution_id_or_none(
    workspace_id: int,
    lineitems: list[ExpenseReportLineitem | BillLineitem | JournalEntryLineitem | ChargeCardTransactionLineitem]
) -> str:
    """
    Get Tax Solution Id or None
    :param workspace_id: Workspace ID
    :param lineitems: List of lineitems
    :return: Tax Solution Id or None
    """
    general_mappings = GeneralMapping.objects.filter(workspace_id=workspace_id).first()

    if general_mappings.location_entity_id:
        return None
    else:
        tax_code = lineitems[0].tax_code

        if tax_code:
            destination_attribute = DestinationAttribute.objects.get(value=tax_code, workspace_id=workspace_id)
            tax_solution_id = destination_attribute.detail['tax_solution_id']
        else:
            destination_attribute = DestinationAttribute.objects.get(value=general_mappings.default_tax_code_name, workspace_id=workspace_id)
            tax_solution_id = destination_attribute.detail['tax_solution_id']

        return tax_solution_id
