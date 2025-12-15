import logging
from datetime import datetime

from django.conf import settings

from fyle_accounting_mappings.models import DestinationAttribute

from apps.mappings.models import GeneralMapping
from apps.workspaces.models import Configuration
from apps.sage_intacct.enums import DestinationAttributeTypeEnum
from apps.sage_intacct.models import JournalEntry, JournalEntryLineitem
from apps.sage_intacct.exports.helpers import get_location_id_for_journal_entry, get_source_entity_id, get_tax_exclusive_amount

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def construct_journal_entry_payload(
    workspace_id: int,
    journal_entry: JournalEntry,
    journal_entry_line_items: list[JournalEntryLineitem]
) -> dict:
    """
    Construct journal entry payload
    :param workspace_id: Workspace ID
    :param journal_entry: JournalEntry object
    :param journal_entry_line_items: JournalEntryLineitem objects
    :return: constructed journal entry payload
    """
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    debit_line_payload = construct_debit_line_payload(
        workspace_id=workspace_id,
        line_items=journal_entry_line_items,
        general_mappings=general_mappings
    )

    credit_line_payload = construct_credit_line_payload(
        workspace_id=workspace_id,
        journal_entry=journal_entry,
        line_items=journal_entry_line_items,
        configuration=configuration,
        general_mappings=general_mappings
    )

    today_date = datetime.today().strftime('%Y-%m-%d')

    journal_entry_payload = {
        'glJournal': {
            'id': 'FYLE_JE' if settings.BRAND_ID == 'fyle' else 'EM_JOURNAL',
        },
        'postingDate': today_date,
        'description': journal_entry.memo,
        'attachment': {
            'id': str(journal_entry.supdoc_id) if journal_entry.supdoc_id else None,
        },
        'lines': debit_line_payload + credit_line_payload
    }

    if configuration.import_tax_codes:
        journal_entry_payload['tax'] = {
            'taxImplication': 'inbound'
        }

    # Add source entity for cross-entity journal entries with single credit line
    source_entity_id = get_source_entity_id(
        workspace_id=workspace_id,
        configuration=configuration,
        general_mappings=general_mappings,
        expense_group=journal_entry.expense_group
    )
    if source_entity_id:
        journal_entry_payload['baselocation_no'] = source_entity_id

    logger.info("| Payload for the journal entry report creation | Content : {{WORKSPACE_ID = {}, EXPENSE_GROUP_ID = {}, JOURNAL_ENTRY_PAYLOAD = {}}}".format(
        workspace_id, journal_entry.expense_group.id, journal_entry_payload
    ))

    return journal_entry_payload


def construct_debit_line_payload(
    workspace_id: int,
    line_items: list[JournalEntryLineitem],
    general_mappings: GeneralMapping
) -> dict:
    """
    Construct debit line payload
    :param workspace_id: Workspace ID
    :param line_items: JournalEntryLineitem object
    :param general_mappings: GeneralMapping object
    :return: constructed debit line payload
    """
    debit_line_payloads = []

    for line_item in line_items:
        tax_inclusive_amount, tax_amount = get_tax_exclusive_amount(
            workspace_id=workspace_id,
            amount=abs(line_item.amount),
            default_tax_code_id=general_mappings.default_tax_code_id
        )

        amount = str(round((line_item.amount - line_item.tax_amount), 2) if (line_item.tax_code and line_item.tax_amount) else tax_inclusive_amount)
        txnTaxAmount = line_item.tax_amount if (line_item.tax_code and line_item.tax_amount) else tax_amount

        debit_line_payload = {
            'txnType': 'credit' if line_item.amount < 0 else 'debit',
            'txnAmount': amount if line_item.amount >= 0 else str(round(abs(line_item.amount), 2)),
            'isBillable': line_item.billable,
            'description': line_item.memo,
            'glAccount': {
                'id': line_item.gl_account_number
            },
            'allocation': {
                'id': line_item.allocation_id
            },
            'dimensions': {
                'department': {
                    'id': line_item.department_id
                },
                'location': {
                    'id': line_item.location_id
                },
                'project': {
                    'id': line_item.project_id
                },
                'customer': {
                    'id': line_item.customer_id
                },
                'vendor': {
                    'id': line_item.vendor_id
                },
                'employee': {
                    'id': line_item.employee_id
                },
                'item': {
                    'id': line_item.item_id
                },
                'class': {
                    'id': line_item.class_id
                },
                'task': {
                    'id': line_item.task_id
                },
                'costType': {
                    'id': line_item.cost_type_id
                },
                **{
                    key: {'key': value}
                    for user_defined_dimensions in line_item.user_defined_dimensions
                    for key, value in user_defined_dimensions.items()
                }
            },
            **(
                {
                    'taxEntries': [{
                        'txnTaxAmount': str(round(abs(txnTaxAmount), 2)) if txnTaxAmount else None,
                        'taxDetail': {
                            'id': line_item.tax_code if (line_item.tax_code and line_item.tax_amount) else general_mappings.default_tax_code_id
                        }
                    }]
                }
                if line_item.amount >= 0 else {}
            )
        }

        allocation = DestinationAttribute.objects.filter(
            workspace_id=workspace_id,
            attribute_type=DestinationAttributeTypeEnum.ALLOCATION.value,
            value=line_item.allocation_id
        ).first()

        if allocation:
            allocation_detail = allocation.detail
            for dimension_key, _ in allocation_detail.items():
                if dimension_key in debit_line_payload['dimensions'].keys():
                    debit_line_payload['dimensions'][dimension_key]['id'] = None

        debit_line_payloads.append(debit_line_payload)

    return debit_line_payloads


def construct_credit_line_payload(
    workspace_id: int,
    journal_entry: JournalEntry,
    line_items: list[JournalEntryLineitem],
    configuration: Configuration,
    general_mappings: GeneralMapping
) -> dict:
    """
    Construct credit line payload
    :param workspace_id: Workspace ID
    :param journal_entry: JournalEntry object
    :param line_items: list[JournalEntryLineitem] objects
    :param configuration: Configuration object
    :param general_mappings: GeneralMapping object
    :return: constructed credit line payload
    """
    if configuration.je_single_credit_line:
        return construct_single_itemized_credit_line(
            workspace_id=workspace_id,
            journal_entry=journal_entry,
            line_items=line_items,
            general_mappings=general_mappings
        )
    else:
        return construct_multiple_itemized_credit_line(
            workspace_id=workspace_id,
            journal_entry=journal_entry,
            line_items=line_items,
            configuration=configuration,
            general_mappings=general_mappings
        )


def construct_multiple_itemized_credit_line(
    workspace_id: int,
    journal_entry: JournalEntry,
    line_items: list[JournalEntryLineitem],
    configuration: Configuration,
    general_mappings: GeneralMapping
) -> dict:
    """
    Construct multiple itemized credit line payload
    :param workspace_id: Workspace ID
    :param journal_entry: JournalEntry object
    :param line_items: list[JournalEntryLineitem] objects
    :param configuration: Configuration object
    :param general_mappings: GeneralMapping object
    :return: constructed multiple itemized credit line payload
    """
    credit_line_payloads = []

    for line_item in line_items:
        tax_inclusive_amount, tax_amount = get_tax_exclusive_amount(
            workspace_id=workspace_id,
            amount=abs(line_item.amount),
            default_tax_code_id=general_mappings.default_tax_code_id
        )

        amount = str(round(line_item.amount - abs(line_item.tax_amount) if (line_item.tax_code and line_item.tax_amount) else tax_inclusive_amount, 2))
        txnTaxAmount = line_item.tax_amount if (line_item.tax_code and line_item.tax_amount) else tax_amount

        credit_line_payload = {
            'txnType': 'debit' if line_item.amount < 0 else 'credit',
            'txnAmount': amount if line_item.amount < 0 else str(round(abs(line_item.amount), 2)),
            'isBillable': line_item.billable if configuration.is_journal_credit_billable else None,
            'description': line_item.memo,
            'glAccount': {
                'id': general_mappings.default_credit_card_id if journal_entry.expense_group.fund_source == 'CCC' else general_mappings.default_gl_account_id
            },
            'allocation': {
                'id': line_item.allocation_id
            },
            'dimensions': {
                'department': {
                    'id': line_item.department_id
                },
                'location': {
                    'id': line_item.location_id
                },
                'project': {
                    'id': line_item.project_id
                },
                'customer': {
                    'id': line_item.customer_id
                },
                'vendor': {
                    'id': line_item.vendor_id
                },
                'employee': {
                    'id': line_item.employee_id
                },
                'item': {
                    'id': line_item.item_id
                },
                'class': {
                    'id': line_item.class_id
                },
                'task': {
                    'id': line_item.task_id
                },
                'costType': {
                    'id': line_item.cost_type_id
                },
                **{
                    key: {'key': value}
                    for user_defined_dimensions in line_item.user_defined_dimensions
                    for key, value in user_defined_dimensions.items()
                }
            },
            **(
                {
                    'taxEntries': [{
                        'txnTaxAmount': str(round(abs(txnTaxAmount), 2)) if txnTaxAmount else None,
                        'taxDetail': {
                            'id': line_item.tax_code if (line_item.tax_code and line_item.tax_amount) else general_mappings.default_tax_code_id
                        }
                    }]
                }
                if line_item.amount < 0 else {}
            )
        }

        allocation = DestinationAttribute.objects.filter(
            workspace_id=workspace_id,
            attribute_type=DestinationAttributeTypeEnum.ALLOCATION.value,
            value=line_item.allocation_id
        ).first()

        if allocation:
            allocation_detail = allocation.detail
            for dimension_key, _ in allocation_detail.items():
                if dimension_key in credit_line_payload['dimensions'].keys():
                    credit_line_payload['dimensions'][dimension_key]['id'] = None

        credit_line_payloads.append(credit_line_payload)

    return credit_line_payloads


def construct_single_itemized_credit_line(
    workspace_id: int,
    journal_entry: JournalEntry,
    line_items: list[JournalEntryLineitem],
    general_mappings: GeneralMapping
) -> dict:
    """
    Construct single itemized credit line payload
    :param workspace_id: Workspace ID
    :param journal_entry: JournalEntry object
    :param line_items: list[JournalEntryLineitem] objects
    :param general_mappings: GeneralMapping object
    :return: constructed single itemized credit line payload
    """
    credit_line_payloads = []
    vendor_groups = {}

    for line_item in line_items:
        vendor_id = line_item.vendor_id
        if vendor_id not in vendor_groups:
            vendor_groups[vendor_id] = []

        vendor_groups[vendor_id].append(line_item)

    for vendor_id, line_items in vendor_groups.items():
        total_amount = sum(line_item.amount for line_item in line_items)

        # Skip if total amount is zero
        if total_amount == 0:
            continue

        # Handle refund case
        txnType = 'debit' if total_amount < 0 else 'credit'
        amount = abs(total_amount)

        credit_line_payload = {
            'txnType': txnType,
            'txnAmount': str(round(amount, 2)),
            'glAccount': {
                'id': general_mappings.default_credit_card_id if journal_entry.expense_group.fund_source == 'CCC' else general_mappings.default_gl_account_id
            },
            'description': 'Total Credit Line',
            'dimensions': {
                'vendor': {
                    'id': vendor_id
                },
                'location': {
                    'id': get_location_id_for_journal_entry(workspace_id=workspace_id)
                },
                'employee': {
                    'id': line_items[0].employee_id
                }
            }
        }
        credit_line_payloads.append(credit_line_payload)

    return credit_line_payloads
