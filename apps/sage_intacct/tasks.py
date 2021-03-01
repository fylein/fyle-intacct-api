import json
import logging
import traceback
from typing import List
from datetime import datetime, timedelta

from django.db import transaction
from django_q.models import Schedule
from django.db.models import Q
from django_q.tasks import Chain

from sageintacctsdk.exceptions import WrongParamsError

from fyle_accounting_mappings.models import Mapping, ExpenseAttribute, MappingSetting, DestinationAttribute

from fyle_intacct_api.exceptions import BulkError

from apps.fyle.models import ExpenseGroup, Reimbursement, Expense
from apps.tasks.models import TaskLog
from apps.mappings.models import GeneralMapping
from apps.workspaces.models import SageIntacctCredential, FyleCredential, WorkspaceGeneralSettings
from apps.fyle.utils import FyleConnector

from .models import ExpenseReport, ExpenseReportLineitem, Bill, BillLineitem, ChargeCardTransaction, \
    ChargeCardTransactionLineitem, APPayment, APPaymentLineitem, SageIntacctReimbursement, \
    SageIntacctReimbursementLineitem
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

def create_or_update_employee_mapping(expense_group: ExpenseGroup, sage_intacct_connection: SageIntacctConnector,
                                     auto_map_employees_preference: str):

    try:
        Mapping.objects.get(
            Q(destination_type='VENDOR') | Q(destination_type='EMPLOYEE'),
            source_type='EMPLOYEE',
            source__value=expense_group.description.get('employee_email'),
            workspace_id=expense_group.workspace_id
        )

    except Mapping.DoesNotExist:
        employee_mapping_setting = MappingSetting.objects.filter(
            Q(destination_field='VENDOR') | Q(destination_field='EMPLOYEE'),
            source_field='EMPLOYEE',
            workspace_id=expense_group.workspace_id
        ).first().destination_field
        
        source_employee = ExpenseAttribute.objects.get(
            workspace_id=expense_group.workspace_id,
            attribute_type='EMPLOYEE',
            value=expense_group.description.get('employee_email')
        )
        try:
            if employee_mapping_setting == 'EMPLOYEE':
                created_entity: DestinationAttribute = sage_intacct_connection.post_employees(
                    source_employee, auto_map_employees_preference
                )
            else:
                created_entity: DestinationAttribute = sage_intacct_connection.post_vendor(
                    source_employee, auto_map_employees_preference
                )

            mapping = Mapping.create_or_update_mapping(
                source_type='EMPLOYEE',
                source_value=expense_group.description.get('employee_email'),
                destination_type=employee_mapping_setting,
                destination_id=created_entity.destination_id,
                destination_value=created_entity.value,
                workspace_id=int(expense_group.workspace_id)
            )
            mapping.source.auto_mapped = True
            mapping.source.save(update_fields=['auto_mapped'])

        except WrongParamsError as exception:
            logger.error(exception.response)

            error_response = exception.response['error'][0]

            # This error code comes up when the vendor or employee already exists
            if error_response['errorno'] == 'PL05000104': 

                sage_intacct_entity = DestinationAttribute.objects.filter(
                    value=source_employee.detail['full_name'],
                    workspace_id=expense_group.workspace_id,
                    attribute_type=employee_mapping_setting
                ).first()

                if sage_intacct_entity:
                    mapping = Mapping.create_or_update_mapping(
                        source_type='EMPLOYEE',
                        source_value=expense_group.description.get('employee_email'),
                        destination_type=employee_mapping_setting,
                        destination_id=sage_intacct_entity.destination_id,
                        destination_value=sage_intacct_entity.value,
                        workspace_id=int(expense_group.workspace_id)
                    )
                    mapping.source.auto_mapped = True
                    mapping.source.save(update_fields=['auto_mapped'])


def schedule_expense_reports_creation(workspace_id: int, expense_group_ids: List[str]):
    """
    Schedule expense reports creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :return: None
    """
    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            workspace_id=workspace_id, id__in=expense_group_ids, expensereport__id__isnull=True, exported_at__isnull=True
        ).all()
    else:
        expense_groups = ExpenseGroup.objects.filter(
            workspace_id=workspace_id, expensereport__id__isnull=True, exported_at__isnull=True
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
    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            workspace_id=workspace_id, id__in=expense_group_ids, bill__id__isnull=True, exported_at__isnull=True
        ).all()
    else:
        expense_groups = ExpenseGroup.objects.filter(
            workspace_id=workspace_id, bill__id__isnull=True, exported_at__isnull=True
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
    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            workspace_id=workspace_id, id__in=expense_group_ids, chargecardtransaction__id__isnull=True, exported_at__isnull=True
        ).all()
    else:
        expense_groups = ExpenseGroup.objects.filter(
            workspace_id=workspace_id, chargecardtransaction__id__isnull=True, exported_at__isnull=True
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


def __validate_expense_group(expense_group: ExpenseGroup, general_settings: WorkspaceGeneralSettings):
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
    general_settings = WorkspaceGeneralSettings.objects.get(workspace_id=expense_group.workspace_id)

    try:
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

        if general_settings.auto_map_employees and general_settings.auto_create_destination_entity:
            create_or_update_employee_mapping(expense_group, sage_intacct_connection, general_settings.auto_map_employees)

        with transaction.atomic():
            __validate_expense_group(expense_group, general_settings)

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
    general_settings = WorkspaceGeneralSettings.objects.get(workspace_id=expense_group.workspace_id)

    try:
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

        if expense_group.fund_source == 'PERSONAL' and general_settings.auto_map_employees \
                and general_settings.auto_create_destination_entity:
            create_or_update_employee_mapping(expense_group, sage_intacct_connection, general_settings.auto_map_employees)
            
        with transaction.atomic():
            __validate_expense_group(expense_group, general_settings)

            bill_object = Bill.create_bill(expense_group)

            bill_lineitems_objects = BillLineitem.create_bill_lineitems(expense_group)

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
    general_settings = WorkspaceGeneralSettings.objects.get(workspace_id=expense_group.workspace_id)
    try:
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

        if general_settings.auto_map_employees and general_settings.auto_create_destination_entity:
            create_or_update_employee_mapping(expense_group, sage_intacct_connection, general_settings.auto_map_employees)


        with transaction.atomic():
            __validate_expense_group(expense_group, general_settings)

            charge_card_transaction_object = ChargeCardTransaction.create_charge_card_transaction(expense_group)

            charge_card_transaction_lineitems_objects = ChargeCardTransactionLineitem. \
                create_charge_card_transaction_lineitems(expense_group)

            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)

            sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

            created_charge_card_transaction = sage_intacct_connection.post_charge_card_transaction( \
                charge_card_transaction_object, charge_card_transaction_lineitems_objects)

            created_attachment_id = load_attachments(sage_intacct_connection, \
                                                     created_charge_card_transaction['key'], expense_group)
            if created_attachment_id:
                try:
                    sage_intacct_connection.update_charge_card_transaction( \
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


def check_expenses_reimbursement_status(expenses):
    all_expenses_paid = True

    for expense in expenses:
        reimbursement = Reimbursement.objects.filter(settlement_id=expense.settlement_id).first()

        if reimbursement.state != 'COMPLETE':
            all_expenses_paid = False

    return all_expenses_paid


def create_ap_payment(workspace_id):
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    fyle_connector = FyleConnector(fyle_credentials.refresh_token, workspace_id)

    fyle_connector.sync_reimbursements()

    bills: List[Bill] = Bill.objects.filter(
        payment_synced=False, expense_group__workspace_id=workspace_id,
        expense_group__fund_source='PERSONAL'
    ).all()

    if bills:
        for bill in bills:
            expense_group_reimbursement_status = check_expenses_reimbursement_status(
                bill.expense_group.expenses.all())
            if expense_group_reimbursement_status:
                task_log, _ = TaskLog.objects.update_or_create(
                    workspace_id=workspace_id,
                    task_id='PAYMENT_{}'.format(bill.expense_group.id),
                    defaults={
                        'status': 'IN_PROGRESS',
                        'type': 'CREATING_AP_PAYMENT'
                    }
                )

                try:
                    with transaction.atomic():

                        ap_payment_object = APPayment.create_ap_payment(bill.expense_group)

                        bill_task_log = TaskLog.objects.get(expense_group=bill.expense_group)

                        record_key = bill_task_log.detail['data']['apbill']['RECORDNO']

                        ap_payment_lineitems_objects = APPaymentLineitem.create_ap_payment_lineitems(
                            ap_payment_object.expense_group, record_key
                        )

                        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)

                        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, workspace_id)

                        created_ap_payment = sage_intacct_connection.post_ap_payment(
                            ap_payment_object, ap_payment_lineitems_objects
                        )

                        bill.payment_synced = True
                        bill.paid_on_sage_intacct = True
                        bill.save(update_fields=['payment_synced', 'paid_on_sage_intacct'])

                        task_log.detail = created_ap_payment
                        task_log.ap_payment = ap_payment_object
                        task_log.status = 'COMPLETE'

                        task_log.save(update_fields=['detail', 'ap_payment', 'status'])

                except SageIntacctCredential.DoesNotExist:
                    logger.error(
                        'Sage-Intacct Credentials not found for workspace_id %s / expense group %s',
                        workspace_id,
                        bill.expense_group
                    )
                    detail = {
                        'expense_group_id': bill.expense_group,
                        'message': 'Sage-Intacct Account not connected'
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
                    logger.error(exception.response)
                    detail = json.loads(exception.response)
                    task_log.status = 'FAILED'
                    task_log.detail = detail

                    task_log.save(update_fields=['detail', 'status'])

                except Exception:
                    error = traceback.format_exc()
                    task_log.detail = {
                        'error': error
                    }
                    task_log.status = 'FATAL'
                    task_log.save(update_fields=['detail', 'status'])
                    logger.error('Something unexpected happened workspace_id: %s %s', task_log.workspace_id,
                                 task_log.detail)


def schedule_ap_payment_creation(sync_fyle_to_sage_intacct_payments, workspace_id):
    general_mappings: GeneralMapping = GeneralMapping.objects.filter(workspace_id=workspace_id).first()
    if general_mappings:
        if sync_fyle_to_sage_intacct_payments and general_mappings.payment_account_id:
            start_datetime = datetime.now()
            schedule, _ = Schedule.objects.update_or_create(
                func='apps.sage_intacct.tasks.create_ap_payment',
                args='{}'.format(workspace_id),
                defaults={
                    'schedule_type': Schedule.MINUTES,
                    'minutes': 24 * 60,
                    'next_run': start_datetime
                }
            )

        if not sync_fyle_to_sage_intacct_payments:
            schedule: Schedule = Schedule.objects.filter(
                func='apps.sage_intacct.tasks.create_ap_payment',
                args='{}'.format(workspace_id)
            ).first()

            if schedule:
                schedule.delete()


def create_sage_intacct_reimbursement(workspace_id):
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    fyle_connector = FyleConnector(fyle_credentials.refresh_token, workspace_id)

    fyle_connector.sync_reimbursements()

    expense_reports: List[ExpenseReport] = ExpenseReport.objects.filter(
        payment_synced=False, expense_group__workspace_id=workspace_id,
        expense_group__fund_source='PERSONAL'
    ).all()

    if expense_reports:
        for expense_report in expense_reports:
            expense_group_reimbursement_status = check_expenses_reimbursement_status(
                expense_report.expense_group.expenses.all())
            if expense_group_reimbursement_status:
                task_log, _ = TaskLog.objects.update_or_create(
                    workspace_id=workspace_id,
                    task_id='PAYMENT_{}'.format(expense_report.expense_group.id),
                    defaults={
                        'status': 'IN_PROGRESS',
                        'type': 'CREATING_REIMBURSEMENT'
                    }
                )

                try:
                    with transaction.atomic():

                        sage_intacct_reimbursement_object = SageIntacctReimbursement.\
                            create_sage_intacct_reimbursement(expense_report.expense_group)

                        expense_report_task_log = TaskLog.objects.get(expense_group=expense_report.expense_group)

                        record_key = expense_report_task_log.detail['key']

                        sage_intacct_reimbursement_lineitems_objects = SageIntacctReimbursementLineitem.\
                            create_sage_intacct_reimbursement_lineitems(sage_intacct_reimbursement_object.expense_group,
                                                                        record_key)

                        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)

                        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, workspace_id)

                        created__sage_intacct_reimbursement = sage_intacct_connection.post_sage_intacct_reimbursement(
                            sage_intacct_reimbursement_object, sage_intacct_reimbursement_lineitems_objects
                        )

                        expense_report.payment_synced = True
                        expense_report.paid_on_sage_intacct = True
                        expense_report.save(update_fields=['payment_synced', 'paid_on_sage_intacct'])

                        task_log.detail = created__sage_intacct_reimbursement
                        task_log.sage_intacct_reimbursement = sage_intacct_reimbursement_object
                        task_log.status = 'COMPLETE'

                        task_log.save(update_fields=['detail', 'sage_intacct_reimbursement', 'status'])

                except SageIntacctCredential.DoesNotExist:
                    logger.error(
                        'Sage-Intacct Credentials not found for workspace_id %s / expense group %s',
                        workspace_id,
                        expense_report.expense_group
                    )
                    detail = {
                        'expense_group_id': expense_report.expense_group,
                        'message': 'Sage-Intacct Account not connected'
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
                    logger.error(exception.response)
                    detail = json.loads(exception.response)
                    task_log.status = 'FAILED'
                    task_log.detail = detail

                    task_log.save(update_fields=['detail', 'status'])

                except Exception:
                    error = traceback.format_exc()
                    task_log.detail = {
                        'error': error
                    }
                    task_log.status = 'FATAL'
                    task_log.save(update_fields=['detail', 'status'])
                    logger.error('Something unexpected happened workspace_id: %s %s', task_log.workspace_id,
                                 task_log.detail)


def schedule_sage_intacct_reimbursement_creation(sync_fyle_to_sage_intacct_payments, workspace_id):
    general_mappings: GeneralMapping = GeneralMapping.objects.filter(workspace_id=workspace_id).first()
    if general_mappings:
        if sync_fyle_to_sage_intacct_payments and general_mappings.payment_account_id:
            start_datetime = datetime.now()
            schedule, _ = Schedule.objects.update_or_create(
                func='apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
                args='{}'.format(workspace_id),
                defaults={
                    'schedule_type': Schedule.MINUTES,
                    'minutes': 24 * 60,
                    'next_run': start_datetime
                }
            )

        if not sync_fyle_to_sage_intacct_payments:
            schedule: Schedule = Schedule.objects.filter(
                func='apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
                args='{}'.format(workspace_id)
            ).first()

            if schedule:
                schedule.delete()


def get_all_sage_intacct_bill_ids(sage_objects: Bill):
    sage_intacct_bill_details = {}

    expense_group_ids = [sage_object.expense_group_id for sage_object in sage_objects]

    task_logs = TaskLog.objects.filter(expense_group_id__in=expense_group_ids).all()

    for task_log in task_logs:
        sage_intacct_bill_details[task_log.expense_group.id] = {
            'expense_group': task_log.expense_group,
            'sage_object_id': task_log.detail['data']['apbill']['RECORDNO']
        }

    return sage_intacct_bill_details


def get_all_sage_intacct_expense_report_ids(sage_objects: ExpenseReport):
    sage_intacct_expense_report_details = {}

    expense_group_ids = [sage_object.expense_group_id for sage_object in sage_objects]

    task_logs = TaskLog.objects.filter(expense_group_id__in=expense_group_ids).all()

    for task_log in task_logs:
        sage_intacct_expense_report_details[task_log.expense_group.id] = {
            'expense_group': task_log.expense_group,
            'sage_object_id': task_log.detail['key']
        }
    return sage_intacct_expense_report_details


def check_sage_intacct_object_status(workspace_id):
    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)

    sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, workspace_id)

    bills = Bill.objects.filter(
        expense_group__workspace_id=workspace_id, paid_on_sage_intacct=False, expense_group__fund_source='PERSONAL'
    ).all()

    expense_reports = ExpenseReport.objects.filter(
        expense_group__workspace_id=workspace_id, paid_on_sage_intacct=False, expense_group__fund_source='PERSONAL'
    ).all()

    if bills:
        bill_ids = get_all_sage_intacct_bill_ids(bills)

        for bill in bills:
            bill_object = sage_intacct_connection.get_bill(bill_ids[bill.expense_group.id]['sage_object_id'])

            if bill_object['apbill']['STATE'] == 'Paid':
                line_items = BillLineitem.objects.filter(bill_id=bill.id)
                for line_item in line_items:
                    expense = line_item.expense
                    expense.paid_on_sage_intacct = True
                    expense.save(update_fields=['paid_on_sage_intacct'])

                bill.paid_on_sage_intacct = True
                bill.payment_synced = True
                bill.save(update_fields=['paid_on_sage_intacct', 'payment_synced'])

    if expense_reports:
        expense_report_ids = get_all_sage_intacct_expense_report_ids(expense_reports)

        for expense_report in expense_reports:
            expense_report_object = sage_intacct_connection.get_expense_report(
                expense_report_ids[expense_report.expense_group_id]['sage_object_id'])

            if expense_report_object['EEXPENSES']['STATE'] == 'Paid':
                line_items = ExpenseReportLineitem.objects.filter(expense_report_id=expense_report.id)
                for line_item in line_items:
                    expense = line_item.expense
                    expense.paid_on_sage_intacct = True
                    expense.save(update_fields=['paid_on_sage_intacct'])

                expense_report.paid_on_sage_intacct = True
                expense_report.payment_synced = True
                expense_report.save(update_fields=['paid_on_sage_intacct', 'payment_synced'])


def schedule_sage_intacct_objects_status_sync(sync_sage_to_fyle_payments, workspace_id):
    if sync_sage_to_fyle_payments:
        start_datetime = datetime.now()
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.sage_intacct.tasks.check_sage_intacct_object_status',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.sage_intacct.tasks.check_sage_intacct_object_status',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()


def process_fyle_reimbursements(workspace_id):
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    fyle_connector = FyleConnector(fyle_credentials.refresh_token, workspace_id)

    fyle_connector.sync_reimbursements()

    reimbursements = Reimbursement.objects.filter(state='PENDING', workspace_id=workspace_id).all()

    reimbursement_ids = []

    if reimbursements:
        for reimbursement in reimbursements:
            expenses = Expense.objects.filter(settlement_id=reimbursement.settlement_id, fund_source='PERSONAL').all()
            paid_expenses = expenses.filter(paid_on_sage_intacct=True)

            all_expense_paid = False
            if len(expenses):
                all_expense_paid = len(expenses) == len(paid_expenses)

            if all_expense_paid:
                reimbursement_ids.append(reimbursement.reimbursement_id)

    if reimbursement_ids:
        fyle_connector.post_reimbursement(reimbursement_ids)
        fyle_connector.sync_reimbursements()


def schedule_fyle_reimbursements_sync(sync_sage_intacct_to_fyle_payments, workspace_id):
    if sync_sage_intacct_to_fyle_payments:
        start_datetime = datetime.now() + timedelta(hours=12)
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.sage_intacct.tasks.process_fyle_reimbursements',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.sage_intacct.tasks.process_fyle_reimbursements',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()
