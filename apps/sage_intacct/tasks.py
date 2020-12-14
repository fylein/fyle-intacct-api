import logging
import traceback
from typing import List
from datetime import datetime

from django.db import transaction
from django.db.models import Q
from django_q.tasks import Chain

from sageintacctsdk.exceptions import WrongParamsError

from fyle_accounting_mappings.models import Mapping

from fyle_intacct_api.exceptions import BulkError

from apps.fyle.models import ExpenseGroup
from apps.tasks.models import TaskLog
from apps.mappings.models import GeneralMapping
from apps.workspaces.models import SageIntacctCredential, FyleCredential, WorkspaceGeneralSettings
from apps.fyle.utils import FyleConnector

from .models import ExpenseReport, ExpenseReportLineitem, Bill, BillLineitem, \
    ChargeCardTransaction, ChargeCardTransactionLineitem
from .utils import SageIntacctConnector

logger = logging.getLogger(__name__)


def load_attachments(sage_intacct_connection: SageIntacctConnector, key: str, expense_group: ExpenseGroup):
    """
    Get attachments from fyle
    :param sage_intacct_connection: Sage Intacct Connection
    :param key: expense report / bills key
    :param expense_group: Expense group
    """
    try:
        fyle_credentials = FyleCredential.objects.get(workspace_id=expense_group.workspace_id)
        expense_ids = expense_group.expenses.values_list('expense_id', flat=True)
        fyle_connector = FyleConnector(fyle_credentials.refresh_token, expense_group.workspace_id)
        attachments = fyle_connector.get_attachments(expense_ids)
        supdoc_id = key
        return sage_intacct_connection.post_attachments(attachments, supdoc_id)
    except Exception:
        error = traceback.format_exc()
        logger.error(
            'Attachment failed for expense group id %s / workspace id %s Error: %s',
            expense_group.id, expense_group.workspace_id, {'error': error}
        )

def schedule_expense_reports_creation(workspace_id: int, expense_group_ids: List[str]):
    """
    Schedule expense reports creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    expense_groups = ExpenseGroup.objects.filter(
        workspace_id=workspace_id, id__in=expense_group_ids, expensereport__id__isnull=True
    ).all()

    chain = Chain(cached=True)

    for expense_group in expense_groups:
        task_log, _ = TaskLog.objects.update_or_create(
            workspace_id=expense_group.workspace_id,
            expense_group=expense_group,
            defaults={
                'status': 'IN_PROGRESS',
                'type': 'CREATING_EXPENSE_REPORTS'
            }
        )

        chain.append('apps.sage_intacct.tasks.create_expense_report', expense_group, task_log)
        task_log.save()

    if chain.length():
        chain.run()

def schedule_bills_creation(workspace_id: int, expense_group_ids: List[str]):
    """
    Schedule bill creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    expense_groups = ExpenseGroup.objects.filter(
        workspace_id=workspace_id, id__in=expense_group_ids, bill__id__isnull=True
    ).all()

    chain = Chain(cached=True)

    for expense_group in expense_groups:
        task_log, _ = TaskLog.objects.update_or_create(
            workspace_id=expense_group.workspace_id,
            expense_group=expense_group,
            defaults={
                'status': 'IN_PROGRESS',
                'type': 'CREATING_BILLS'
            }
        )

        chain.append('apps.sage_intacct.tasks.create_bill', expense_group, task_log)
        task_log.save()

    if chain.length():
        chain.run()

def schedule_charge_card_transaction_creation(workspace_id: int, expense_group_ids: List[str]):
    """
    Schedule charge card transaction creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    expense_groups = ExpenseGroup.objects.filter(
        workspace_id=workspace_id, id__in=expense_group_ids, chargecardtransaction__id__isnull=True
    ).all()

    chain = Chain(cached=True)

    for expense_group in expense_groups:
        task_log, _ = TaskLog.objects.update_or_create(
            workspace_id=expense_group.workspace_id,
            expense_group=expense_group,
            defaults={
                'status': 'IN_PROGRESS',
                'type': 'CREATING_CHARGE_CARD_TRANSACTIONS'
            }
        )

        chain.append('apps.sage_intacct.tasks.create_charge_card_transaction', expense_group, task_log)
        task_log.save()

    if chain.length():
        chain.run()

def handle_sage_intacct_errors(exception, expense_group: ExpenseGroup, task_log: TaskLog, export_type: str):
    logger.error(exception.response)
    sage_intacct_errors = exception.response['error']
    error_msg = 'Failed to create {0} in your Sage Intacct account.'.format(export_type)
    errors = []

    if isinstance(sage_intacct_errors, list):
        for error in sage_intacct_errors:
            errors.append({
                'expense_group_id': expense_group.id,
                'short_description': error['description'] if error['description'] else '{0} error'.format(export_type),
                'long_description': error['description2'] if error['description2'] \
                    else error_msg,
                'correction': error['correction'] if error['correction'] else 'Not available'
            })

    elif isinstance(sage_intacct_errors, dict):
        error = sage_intacct_errors
        errors.append({
            'expense_group_id': expense_group.id,
            'short_description': error['description'] if error['description'] else '{0} error'.format(export_type),
            'long_description': error['description2'] if error['description2'] \
                else error_msg,
            'correction': error['correction'] if error['correction'] else 'Not available'
        })

    task_log.status = 'FAILED'
    task_log.detail = None
    task_log.sage_intacct_errors = errors
    task_log.save(update_fields=['sage_intacct_errors', 'detail', 'status'])

def __validate_expense_group(expense_group: ExpenseGroup):
    bulk_errors = []
    row = 0

    general_mapping = None
    try:
        general_mapping = GeneralMapping.objects.get(workspace_id=expense_group.workspace_id)
    except GeneralMapping.DoesNotExist:
        bulk_errors.append({
            'row': None,
            'expense_group_id': expense_group.id,
            'value': 'general mappings',
            'type': 'General Mappings',
            'message': 'General mappings not found'
        })

    general_settings: WorkspaceGeneralSettings = WorkspaceGeneralSettings.objects.get(
        workspace_id=expense_group.workspace_id)

    if general_settings.corporate_credit_card_expenses_object:
        try:
            GeneralMapping.objects.get(workspace_id=expense_group.workspace_id)
        except GeneralMapping.DoesNotExist:
            bulk_errors.append({
                'row': None,
                'expense_group_id': expense_group.id,
                'value': expense_group.description.get('employee_email'),
                'type': 'General Mapping',
                'message': 'General Mapping not found'
            })

    try:
        if expense_group.fund_source == 'PERSONAL':
            error_message = 'Employee Mapping not found'
            Mapping.objects.get(
                Q(destination_type='VENDOR') | Q(destination_type='EMPLOYEE'),
                source_type='EMPLOYEE',
                source__value=expense_group.description.get('employee_email'),
                workspace_id=expense_group.workspace_id
            )

        elif expense_group.fund_source == 'CCC':
            if general_settings.corporate_credit_card_expenses_object == 'BILL':
                if general_mapping and not general_mapping.default_ccc_vendor_id:
                    bulk_errors.append({
                        'row': None,
                        'expense_group_id': expense_group.id,
                        'value': expense_group.description.get('employee_email'),
                        'type': 'General Mapping',
                        'message': 'Default Credit Card Vendor not found'
                    })

            elif general_settings.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
                if general_mapping and not general_mapping.default_charge_card_id:
                    bulk_errors.append({
                        'row': None,
                        'expense_group_id': expense_group.id,
                        'value': expense_group.description.get('employee_email'),
                        'type': 'General Mapping',
                        'message': 'Default Charge Card not found'
                    })

    except Mapping.DoesNotExist:
        bulk_errors.append({
            'row': None,
            'expense_group_id': expense_group.id,
            'value': expense_group.description.get('employee_email'),
            'type': 'Employee Mapping',
            'message': error_message
        })

    expenses = expense_group.expenses.all()

    for lineitem in expenses:
        category = lineitem.category if lineitem.category == lineitem.sub_category else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        if expense_group.fund_source == 'PERSONAL':
            error_message = 'Category Mapping Not Found'
            account = Mapping.objects.filter(
                Q(destination_type='ACCOUNT') | Q(destination_type='EXPENSE_TYPE'),
                source_type='CATEGORY',
                source__value=category,
                workspace_id=expense_group.workspace_id
            ).first()

        elif expense_group.fund_source == 'CCC':
            error_message = 'Credit Card Expense Account Mapping Not Found'
            account = Mapping.objects.filter(
                source_type='CATEGORY',
                source__value=category,
                destination_type='CCC_ACCOUNT',
                workspace_id=expense_group.workspace_id
            ).first()

        if category and not account:
            bulk_errors.append({
                'row': row,
                'expense_group_id': expense_group.id,
                'value': category,
                'type': 'Category Mapping',
                'message': error_message
            })

        row = row + 1

    if bulk_errors:
        raise BulkError('Mappings are missing', bulk_errors)

def create_expense_report(expense_group, task_log):
    try:
        with transaction.atomic():
            __validate_expense_group(expense_group)

            expense_report_object = ExpenseReport.create_expense_report(expense_group)

            expense_report_lineitems_objects = ExpenseReportLineitem.create_expense_report_lineitems(expense_group)

            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)

            sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

            created_expense_report = sage_intacct_connection.post_expense_report(expense_report_object, \
                expense_report_lineitems_objects)

            created_attachment_id = load_attachments(sage_intacct_connection, \
                created_expense_report['key'], expense_group)
            if created_attachment_id:
                try:
                    sage_intacct_connection.update_expense_report(created_expense_report['key'], created_attachment_id)
                    expense_report_object.supdoc_id = created_attachment_id
                    expense_report_object.save(update_fields=['supdoc_id'])
                except Exception:
                    error = traceback.format_exc()
                    logger.error(
                        'Updating Attachment failed for expense group id %s / workspace id %s Error: %s',
                        expense_group.id, expense_group.workspace_id, {'error': error}
                    )

            task_log.detail = created_expense_report
            task_log.expense_report = expense_report_object
            task_log.status = 'COMPLETE'

            task_log.save(update_fields=['detail', 'expense_report', 'status'])

            expense_group.exported_at = datetime.now()
            expense_group.save()

    except SageIntacctCredential.DoesNotExist:
        logger.exception(
            'Sage Intacct Credentials not found for workspace_id %s / expense group %s',
            expense_group.id,
            expense_group.workspace_id
        )
        detail = {
            'expense_group_id': expense_group.id,
            'message': 'Sage Intacct Account not connected'
        }
        task_log.status = 'FAILED'
        task_log.detail = detail

        task_log.save(update_fields=['detail', 'status'])

    except BulkError as exception:
        logger.error(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail

        task_log.save(update_fields=['detail', 'status'])

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Expense Reports')

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save(update_fields=['detail', 'status'])
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)


def create_bill(expense_group, task_log):
    try:
        with transaction.atomic():
            __validate_expense_group(expense_group)

            bill_object = Bill.create_bill(expense_group)

            bill_lineitems_objects = BillLineitem.create_bill_lineitems(expense_group)

            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)

            sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

            created_bill = sage_intacct_connection.post_bill(bill_object, \
                bill_lineitems_objects)

            created_attachment_id = load_attachments(sage_intacct_connection, \
                created_bill['data']['apbill']['RECORDNO'], expense_group)

            if created_attachment_id:
                try:
                    sage_intacct_connection.update_bill(created_bill['data']['apbill']['RECORDNO'], \
                        created_attachment_id)
                    bill_object.supdoc_id = created_attachment_id
                    bill_object.save(update_fields=['supdoc_id'])
                except Exception:
                    error = traceback.format_exc()
                    logger.error(
                        'Updating Attachment failed for expense group id %s / workspace id %s Error: %s',
                        expense_group.id, expense_group.workspace_id, {'error': error}
                    )

            task_log.detail = created_bill
            task_log.bill = bill_object
            task_log.status = 'COMPLETE'

            task_log.save(update_fields=['detail', 'bill', 'status'])

            expense_group.exported_at = datetime.now()
            expense_group.save()

    except SageIntacctCredential.DoesNotExist:
        logger.exception(
            'Sage Intacct Credentials not found for workspace_id %s / expense group %s',
            expense_group.id,
            expense_group.workspace_id
        )
        detail = {
            'expense_group_id': expense_group.id,
            'message': 'Sage Intacct Account not connected'
        }
        task_log.status = 'FAILED'
        task_log.detail = detail

        task_log.save(update_fields=['detail', 'status'])

    except BulkError as exception:
        logger.error(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail

        task_log.save(update_fields=['detail', 'status'])

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Bills')

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save(update_fields=['detail', 'status'])
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)

def create_charge_card_transaction(expense_group, task_log):
    try:
        with transaction.atomic():
            __validate_expense_group(expense_group)

            charge_card_transaction_object = ChargeCardTransaction.create_charge_card_transaction(expense_group)

            charge_card_transaction_lineitems_objects = ChargeCardTransactionLineitem.\
                create_charge_card_transaction_lineitems(expense_group)

            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)

            sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

            created_charge_card_transaction = sage_intacct_connection.post_charge_card_transaction(\
                charge_card_transaction_object, charge_card_transaction_lineitems_objects)

            created_attachment_id = load_attachments(sage_intacct_connection, \
                created_charge_card_transaction['key'], expense_group)
            if created_attachment_id:
                try:
                    sage_intacct_connection.update_charge_card_transaction(\
                        created_charge_card_transaction['key'], created_attachment_id)
                    charge_card_transaction_object.supdoc_id = created_attachment_id
                    charge_card_transaction_object.save(update_fields=['supdoc_id'])
                except Exception:
                    error = traceback.format_exc()
                    logger.error(
                        'Updating Attachment failed for expense group id %s / workspace id %s Error: %s',
                        expense_group.id, expense_group.workspace_id, {'error': error}
                    )

            task_log.detail = created_charge_card_transaction
            task_log.charge_card_transaction = charge_card_transaction_object
            task_log.status = 'COMPLETE'

            task_log.save(update_fields=['detail', 'charge_card_transaction', 'status'])

            expense_group.exported_at = datetime.now()
            expense_group.save()

    except SageIntacctCredential.DoesNotExist:
        logger.exception(
            'Sage Intacct Credentials not found for workspace_id %s / expense group %s',
            expense_group.id,
            expense_group.workspace_id
        )
        detail = {
            'expense_group_id': expense_group.id,
            'message': 'Sage Intacct Account not connected'
        }
        task_log.status = 'FAILED'
        task_log.detail = detail

        task_log.save(update_fields=['detail', 'status'])

    except BulkError as exception:
        logger.error(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail

        task_log.save(update_fields=['detail', 'status'])

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Charge Card Transactions')

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save(update_fields=['detail', 'status'])
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)
