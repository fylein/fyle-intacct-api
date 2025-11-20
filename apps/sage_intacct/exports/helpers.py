from typing import Optional

from fyle_accounting_mappings.models import DestinationAttribute

from apps.sage_intacct.enums import DestinationAttributeTypeEnum
from apps.mappings.models import GeneralMapping, LocationEntityMapping
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
    line_items: list[ExpenseReportLineitem | BillLineitem | JournalEntryLineitem | ChargeCardTransactionLineitem]
) -> str:
    """
    Get Tax Solution Id or None
    :param workspace_id: Workspace ID
    :param line_items: List of line_items
    :return: Tax Solution Id or None
    """
    general_mappings = GeneralMapping.objects.filter(workspace_id=workspace_id).first()

    if general_mappings.location_entity_id:
        return None
    else:
        tax_code = line_items[0].tax_code

        if tax_code:
            destination_attribute = DestinationAttribute.objects.get(value=tax_code, workspace_id=workspace_id)
            tax_solution_id = destination_attribute.detail['tax_solution_id']
        else:
            destination_attribute = DestinationAttribute.objects.get(value=general_mappings.default_tax_code_name, workspace_id=workspace_id)
            tax_solution_id = destination_attribute.detail['tax_solution_id']

        return tax_solution_id


def get_location_id_for_journal_entry(workspace_id: int) -> Optional[str]:
    """
    Get location ID based on configuration.
    :param workspace_id: Workspace ID
    :return: Location ID or None if not found
    """
    general_mapping = (
        GeneralMapping.objects
        .filter(workspace_id=workspace_id, default_location_id__isnull=False)
        .values('default_location_id')
        .first()
    )
    if general_mapping:
        return general_mapping['default_location_id']

    location_mapping = (
        LocationEntityMapping.objects
        .filter(workspace_id=workspace_id)
        .exclude(location_entity_name='Top Level')
        .values('location_entity_name', 'destination_id')
        .first()
    )
    if location_mapping:
        return location_mapping['destination_id']

    return None

