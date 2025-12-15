from datetime import datetime
from typing import Optional, Union

from fyle_accounting_mappings.models import DestinationAttribute

from apps.fyle.models import ExpenseGroup, ExpenseGroupSettings
from apps.sage_intacct.enums import DestinationAttributeTypeEnum
from apps.mappings.models import GeneralMapping, LocationEntityMapping
from apps.workspaces.models import Configuration
from apps.sage_intacct.models import (
    BillLineitem,
    JournalEntryLineitem,
    ExpenseReportLineitem,
    ChargeCardTransactionLineitem
)


def format_transaction_date(transaction_date: Union[str, datetime]) -> str:
    """
    Format transaction date to 'YYYY-MM-DD' string.
    Handles both string and datetime inputs.
    :param transaction_date: Transaction date as string or datetime
    :return: Formatted date string
    """
    if isinstance(transaction_date, str):
        # Parse the string and format it
        return datetime.strptime(transaction_date, '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')
    return transaction_date.strftime('%Y-%m-%d')


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


def __is_integration_at_top_level(workspace_id: int) -> bool:
    """
    Check if the integration is connected at the top level.
    :param workspace_id: Workspace ID
    :return: True if integration is at top level, False otherwise
    """
    location_entity_mapping = LocationEntityMapping.objects.filter(
        workspace_id=workspace_id
    ).first()

    if location_entity_mapping and location_entity_mapping.destination_id == 'top_level':
        return True

    return False


def __is_expenses_grouped_by_report(expense_group: ExpenseGroup) -> bool:
    """
    Check if the expense group is grouped by expense report based on fund source.
    :param expense_group: ExpenseGroup object
    :return: True if grouped by report_id
    """
    expense_group_settings = ExpenseGroupSettings.objects.filter(
        workspace_id=expense_group.workspace_id
    ).first()

    if expense_group.fund_source == 'PERSONAL':
        return 'report_id' in expense_group_settings.reimbursable_expense_group_fields
    elif expense_group.fund_source == 'CCC':
        return 'report_id' in expense_group_settings.corporate_credit_card_expense_group_fields

    return False


def get_source_entity_id(
    workspace_id: int,
    configuration: Configuration,
    general_mappings: GeneralMapping,
    expense_group: ExpenseGroup
) -> Optional[str]:
    """
    Get the source entity ID for Journal Entry exports.

    The source entity field is required when:
    1. Integration is connected at the top level
    2. Expenses are grouped by expense report
    3. Single itemized credit line option is enabled
    4. A default location value is configured

    :param workspace_id: Workspace ID
    :param configuration: Configuration object
    :param general_mappings: GeneralMapping object
    :param expense_group: ExpenseGroup object
    :return: Source entity ID (default_location_id) or None
    """
    if (
        __is_integration_at_top_level(workspace_id)
        and __is_expenses_grouped_by_report(expense_group)
        and configuration.je_single_credit_line
        and general_mappings.default_location_id
    ):
        return general_mappings.default_location_id

    return None
