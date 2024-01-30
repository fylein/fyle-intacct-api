import logging
import traceback
from typing import List
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django_q.models import Schedule
from django_q.tasks import Chain

from sageintacctsdk.exceptions import WrongParamsError, InvalidTokenError, NoPrivilegeError

from fyle_integrations_platform_connector import PlatformConnector
from fyle_accounting_mappings.models import (
        Mapping, 
        ExpenseAttribute, 
        DestinationAttribute,
        CategoryMapping, 
        EmployeeMapping
    )

from fyle_intacct_api.exceptions import BulkError
from apps.fyle.models import ExpenseGroup, Reimbursement, Expense
from apps.tasks.models import TaskLog, Error
from apps.mappings.models import GeneralMapping
from apps.fyle.actions import update_expenses_in_progress, update_failed_expenses, update_complete_expenses
from apps.fyle.tasks import post_accounting_export_summary
from apps.workspaces.models import (
        SageIntacctCredential, 
        FyleCredential, 
        Configuration, 
        LastExportDetail,
        Workspace
    )
from apps.sage_intacct.models import (
        ExpenseReport, 
        ExpenseReportLineitem, 
        Bill,
        BillLineitem, 
        ChargeCardTransaction,
        ChargeCardTransactionLineitem, 
        APPayment, 
        APPaymentLineitem, 
        JournalEntry, 
        JournalEntryLineitem, 
        SageIntacctReimbursement,
        SageIntacctReimbursementLineitem
    )
from .utils import SageIntacctConnector

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def update_last_export_details(workspace_id):
    last_export_detail = LastExportDetail.objects.get(workspace_id=workspace_id)

    failed_exports = TaskLog.objects.filter(
        ~Q(type__in=['CREATING_REIMBURSEMENT', 'FETCHING_EXPENSES', 'CREATING_AP_PAYMENT']), workspace_id=workspace_id, status__in=['FAILED', 'FATAL']
    ).count()

    successful_exports = TaskLog.objects.filter(
        ~Q(type__in=['CREATING_REIMBURSEMENT', 'FETCHING_EXPENSES', 'CREATING_AP_PAYMENT']),
        workspace_id=workspace_id,
        status='COMPLETE',
        updated_at__gt=last_export_detail.last_exported_at
    ).count()

    last_export_detail.failed_expense_groups_count = failed_exports
    last_export_detail.successful_expense_groups_count = successful_exports
    last_export_detail.total_expense_groups_count = failed_exports + successful_exports
    last_export_detail.save()

    return last_export_detail


def load_attachments(sage_intacct_connection: SageIntacctConnector, key: str, expense_group: ExpenseGroup):
    """
    Get attachments from fyle
    :param sage_intacct_connection: Sage Intacct Connection
    :param key: expense report / bills key
    :param expense_group: Expense group
    """
    try:
        fyle_credentials = FyleCredential.objects.get(workspace_id=expense_group.workspace_id)
        file_ids = expense_group.expenses.values_list('file_ids', flat=True)
        platform = PlatformConnector(fyle_credentials)

        files_list = []
        attachments = []
        for file_id in file_ids:
            for id in file_id:
                file_object = {'id': id}
                files_list.append(file_object)

        if files_list:
            attachments = platform.files.bulk_generate_file_urls(files_list)

        supdoc_id = key
        return sage_intacct_connection.post_attachments(attachments, supdoc_id)

    except Exception:
        error = traceback.format_exc()
        logger.info(
            'Attachment failed for expense group id %s / workspace id %s Error: %s',
            expense_group.id, expense_group.workspace_id, {'error': error}
        )


def create_or_update_employee_mapping(expense_group: ExpenseGroup, sage_intacct_connection: SageIntacctConnector,
                                      auto_map_employees_preference: str, employee_field_mapping: str):
    try:
        mapping = EmployeeMapping.objects.get(
            source_employee__value=expense_group.description.get('employee_email'),
            workspace_id=expense_group.workspace_id
        )

        mapping = mapping.destination_employee if employee_field_mapping == 'EMPLOYEE' else mapping.destination_vendor

        if not mapping:
            raise EmployeeMapping.DoesNotExist

    except EmployeeMapping.DoesNotExist:
        source_employee = ExpenseAttribute.objects.get(
            workspace_id=expense_group.workspace_id,
            attribute_type='EMPLOYEE',
            value=expense_group.description.get('employee_email')
        )

        try:
            if auto_map_employees_preference == 'EMAIL':
                filters = {
                    'detail__email__iexact': source_employee.value,
                    'attribute_type': employee_field_mapping
                }

            elif auto_map_employees_preference == 'NAME':
                filters = {
                    'value__iexact': source_employee.detail['full_name'],
                    'attribute_type': employee_field_mapping
                }

            entity = DestinationAttribute.objects.filter(
                     workspace_id=expense_group.workspace_id,
                     **filters
                ).first()

            existing_employee_mapping = EmployeeMapping.objects.filter(
                source_employee=source_employee
            ).first()

            destination = {}
            if employee_field_mapping == 'EMPLOYEE':
                if entity is None:
                    entity: DestinationAttribute = sage_intacct_connection.get_or_create_employee(source_employee)
                    destination['destination_employee_id'] = entity.id
                elif existing_employee_mapping and existing_employee_mapping.destination_employee:
                    destination['destination_employee_id'] = existing_employee_mapping.destination_employee.id

            else:
                if entity is None:
                    entity: DestinationAttribute = sage_intacct_connection.get_or_create_vendor(
                        source_employee.detail['full_name'], source_employee.value, create=True
                    )
                    destination['destination_vendor_id'] = entity.id
                elif existing_employee_mapping and existing_employee_mapping.destination_vendor:
                    destination['destination_vendor_id'] = existing_employee_mapping.destination_vendor.id

            if existing_employee_mapping and existing_employee_mapping.destination_card_account:
                destination['destination_card_account_id'] = existing_employee_mapping.destination_card_account.id

            if 'destination_employee_id' not in destination or not destination['destination_employee_id']:
                destination['destination_employee_id'] = entity.id

            if 'destination_vendor_id' not in destination or not destination['destination_vendor_id']:
                destination['destination_vendor_id'] = entity.id

            mapping = EmployeeMapping.create_or_update_employee_mapping(
                source_employee_id=source_employee.id,
                workspace=expense_group.workspace,
                **destination
            )
            mapping.source_employee.auto_mapped = True
            mapping.source_employee.save()

            if employee_field_mapping == 'EMPLOYEE':
                mapping.destination_employee.auto_created = True
                mapping.destination_employee.save()
            elif employee_field_mapping == 'VENDOR':
                mapping.destination_vendor.auto_created = True
                mapping.destination_vendor.save()

        except WrongParamsError as exception:
            logger.info(exception.response)

            error_response = exception.response['error'][0]

            # This error code comes up when the employee already exists
            if error_response['errorno'] == 'BL34000061' or error_response['errorno'] == 'PL05000104':
                sage_intacct_display_name = source_employee.detail['full_name']

                sage_intacct_entity = DestinationAttribute.objects.filter(
                    value=sage_intacct_display_name,
                    workspace_id=expense_group.workspace_id,
                    attribute_type=employee_field_mapping
                ).first()

                if sage_intacct_entity:
                    mapping = Mapping.create_or_update_mapping(
                        source_type='EMPLOYEE',
                        source_value=expense_group.description.get('employee_email'),
                        destination_type=employee_field_mapping,
                        destination_id=sage_intacct_entity.destination_id,
                        destination_value=sage_intacct_entity.value,
                        workspace_id=int(expense_group.workspace_id)
                    )
                    mapping.source.auto_mapped = True
                    mapping.source.save()
                else:
                    logger.info(
                        'Destination Attribute with value %s not found in workspace %s',
                        source_employee.detail['full_name'],
                        expense_group.workspace_id
                    )


def get_or_create_credit_card_vendor(merchant: str, workspace_id: int):
    """
    Get or create default vendor
    :param merchant: Fyle Expense Merchant
    :param workspace_id: Workspace Id
    :return:
    """
    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, workspace_id)
    vendor = None

    if merchant:
        try:
            vendor = sage_intacct_connection.get_or_create_vendor(merchant, create=False)
        except WrongParamsError as bad_request:
            logger.info(bad_request.response)

    if not vendor:
        vendor = sage_intacct_connection.get_or_create_vendor('Credit Card Misc', create=True)

    return vendor






def resolve_errors_for_exported_expense_group(expense_group: ExpenseGroup):
    """
    Resolve errors for exported expense group
    :param expense_group: Expense group
    """
    Error.objects.filter(workspace_id=expense_group.workspace_id, expense_group=expense_group, is_resolved=False).update(is_resolved=True)


def handle_sage_intacct_errors(exception, expense_group: ExpenseGroup, task_log: TaskLog, export_type: str):
    logger.info(exception.response)
    
    errors = []
    error_title = 'Failed to create {0} in your Sage Intacct account.'.format(export_type)
    error_msg = 'Something unexpected happened with the workspace'
    if 'error' in exception.response:
        sage_intacct_errors = exception.response['error']
        error_msg = 'Failed to create {0} in your Sage Intacct account.'.format(export_type)

        if isinstance(sage_intacct_errors, list):
            for error in sage_intacct_errors:
                errors.append({
                    'expense_group_id': expense_group.id,
                    'short_description': error['description'] \
                        if ('description' in error and error['description']) else '{0} error'.format(export_type),
                    'long_description': error['description2'] \
                        if ('description2' in error and error['description2']) \
                            else error_msg,
                    'correction': error['correction']\
                         if ('correction' in error and error['correction']) else 'Not available'
                })

        elif isinstance(sage_intacct_errors, dict):
            error = sage_intacct_errors
            errors.append({
                'expense_group_id': expense_group.id,
                'short_description': error['description'] \
                    if ('description' in error and error['description']) else '{0} error'.format(export_type),
                'long_description': error['description2'] if ('description2' in error and error['description2']) \
                    else error_msg,
                'correction': error['correction']\
                    if ('correction' in error and error['correction']) else 'Not available'
            })


    if errors:
        error_title = errors[0]['correction'] if (errors[0]['correction'] and errors[0]['correction'] != 'not available') else errors[0]['short_description']
        error_msg = errors[0]['long_description']
    else:
        errors.append(exception.response)

    Error.objects.update_or_create(
            workspace_id=expense_group.workspace_id,
            expense_group=expense_group,
            defaults={
                'type': 'INTACCT_ERROR',
                'error_title': error_title,
                'error_detail': error_msg,
                'is_resolved': False
            }
        )

    task_log.status = 'FAILED'
    task_log.detail = None
    task_log.sage_intacct_errors = errors
    task_log.save()

    update_failed_expenses(expense_group.expenses.all(), False)


def __validate_expense_group(expense_group: ExpenseGroup, configuration: Configuration):
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

    
    employee_attribute = ExpenseAttribute.objects.filter(
        value=expense_group.description.get('employee_email'),
        workspace_id=expense_group.workspace_id,
        attribute_type='EMPLOYEE'
    ).first()

    try:
        if expense_group.fund_source == 'PERSONAL':
            error_message = 'Employee Mapping not found'
            entity = EmployeeMapping.objects.get(
                source_employee__value=expense_group.description.get('employee_email'),
                workspace_id=expense_group.workspace_id
            )

            if configuration.employee_field_mapping == 'EMPLOYEE':
                entity = entity.destination_employee
            else:
                entity = entity.destination_vendor

            if not entity:
                raise EmployeeMapping.DoesNotExist

        elif expense_group.fund_source == 'CCC':
            if configuration.corporate_credit_card_expenses_object == 'BILL':
                if general_mapping and not general_mapping.default_ccc_vendor_id:
                    bulk_errors.append({
                        'row': None,
                        'expense_group_id': expense_group.id,
                        'value': expense_group.description.get('employee_email'),
                        'type': 'General Mapping',
                        'message': 'Default Credit Card Vendor not found'
                    })

            elif configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
                if general_mapping and not general_mapping.default_charge_card_id:
                    bulk_errors.append({
                        'row': None,
                        'expense_group_id': expense_group.id,
                        'value': expense_group.description.get('employee_email'),
                        'type': 'General Mapping',
                        'message': 'Default Charge Card not found'
                    })

            elif configuration.corporate_credit_card_expenses_object == 'JOURNAL_ENTRY':
                if general_mapping and not general_mapping.default_credit_card_id:
                    bulk_errors.append({
                        'row': None,
                        'expense_group_id': expense_group.id,
                        'value': expense_group.description.get('employee_email'),
                        'type': 'General Mapping',
                        'message': 'Default Credit Card not found'
                    })
                error_message = 'Employee Mapping not found'
                entity = EmployeeMapping.objects.get(
                    source_employee__value=expense_group.description.get('employee_email'),
                    workspace_id=expense_group.workspace_id
                )
                if configuration.employee_field_mapping == 'EMPLOYEE':
                    entity = entity.destination_employee
                else:
                    entity = entity.destination_vendor

                if not entity:
                    raise EmployeeMapping.DoesNotExist

            elif configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
                error_message = 'Employee Mapping not found'
                entity = EmployeeMapping.objects.get(
                    source_employee__value=expense_group.description.get('employee_email'),
                    workspace_id=expense_group.workspace_id
                )

                if not entity.destination_employee:
                    raise EmployeeMapping.DoesNotExist

    except EmployeeMapping.DoesNotExist:
        bulk_errors.append({
            'row': None,
            'expense_group_id': expense_group.id,
            'value': expense_group.description.get('employee_email'),
            'type': 'Employee Mapping',
            'message': error_message
        })

        if employee_attribute:
            Error.objects.update_or_create(
                workspace_id=expense_group.workspace_id,
                expense_attribute=employee_attribute,
                defaults={
                    'type': 'EMPLOYEE_MAPPING',
                    'error_title': employee_attribute.value,
                    'error_detail': 'Employee mapping is missing',
                    'is_resolved': False
                }
            )

    expenses = expense_group.expenses.all()

    for lineitem in expenses:
        category = lineitem.category if (lineitem.category == lineitem.sub_category or lineitem.sub_category == None) else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        category_mapping = CategoryMapping.objects.filter(
            source_category__value=category,
            workspace_id=expense_group.workspace_id
        ).first()

        category_attribute = ExpenseAttribute.objects.filter(
            value=category,
            workspace_id=expense_group.workspace_id,
            attribute_type='CATEGORY'
        ).first()

        if category_mapping:
            if expense_group.fund_source == 'PERSONAL':
                if configuration.reimbursable_expenses_object == 'EXPENSE_REPORT':
                    category_mapping = category_mapping.destination_expense_head
                elif (configuration.reimbursable_expenses_object == 'BILL' or configuration.reimbursable_expenses_object == 'JOURNAL_ENTRY'):
                    category_mapping = category_mapping.destination_account
            else:
                if configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
                    category_mapping = category_mapping.destination_expense_head
                else:
                    category_mapping = category_mapping.destination_account

        if not category_mapping:
            bulk_errors.append({
                'row': row,
                'expense_group_id': expense_group.id,
                'value': category,
                'type': 'Category Mapping',
                'message': 'Category Mapping Not Found'
            })

            if category_attribute:
                Error.objects.update_or_create(
                    workspace_id=expense_group.workspace_id,
                    expense_attribute=category_attribute,
                    defaults={
                        'type': 'CATEGORY_MAPPING',
                        'error_title': category_attribute.value,
                        'error_detail': 'Category mapping is missing',
                        'is_resolved': False
                    }
                )


        if configuration.import_tax_codes:
            if general_mapping and not (general_mapping.default_tax_code_id or general_mapping.default_tax_code_name):
                bulk_errors.append({
                    'row': None,
                    'expense_group_id': expense_group.id,
                    'value': 'Default Tax Code',
                    'type': 'General Mapping',
                    'message': 'Default Tax Code not found'
                })

        row = row + 1

    if bulk_errors:
        raise BulkError('Mappings are missing', bulk_errors)


def create_journal_entry(expense_group: ExpenseGroup, task_log_id: int, last_export: bool):
    task_log = TaskLog.objects.get(id=task_log_id)
    if task_log.status not in ['IN_PROGRESS', 'COMPLETE']:
        task_log.status = 'IN_PROGRESS'
        task_log.save()
    else:
        return

    configuration = Configuration.objects.get(workspace_id=expense_group.workspace_id)

    try:
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

        if configuration.auto_map_employees and configuration.auto_create_destination_entity \
            and configuration.auto_map_employees != 'EMPLOYEE_CODE':
            create_or_update_employee_mapping(
                expense_group, sage_intacct_connection, configuration.auto_map_employees,
                configuration.employee_field_mapping
            )

        __validate_expense_group(expense_group, configuration)

        created_attachment_id = None
        with transaction.atomic():

            journal_entry_object = JournalEntry.create_journal_entry(expense_group)

            journal_entry_lineitem_object = JournalEntryLineitem.create_journal_entry_lineitems(expense_group, configuration)

            created_journal_entry = sage_intacct_connection.post_journal_entry(journal_entry_object,journal_entry_lineitem_object)

            task_log.journal_entry = journal_entry_object
            task_log.sage_intacct_errors = None
            task_log.status = 'COMPLETE'

            task_log.save()

            expense_group.exported_at = datetime.now()
            expense_group.export_type = 'JOURNAL_ENTRY'
            expense_group.save()

            journal_entry = sage_intacct_connection.get_journal_entry(created_journal_entry['data']['glbatch']['RECORDNO'], ['RECORD_URL'])
            url_id = journal_entry['glbatch']['RECORD_URL'].split('?.r=', 1)[1]
            created_journal_entry['url_id'] = url_id

            task_log.detail = created_journal_entry

            task_log.save()

            expense_group.exported_at = datetime.now()
            expense_group.response_logs = created_journal_entry
            expense_group.export_type = 'JOURNAL_ENTRY'
            expense_group.save()
            resolve_errors_for_exported_expense_group(expense_group)
        
        generate_export_url_and_update_expense(expense_group)

        created_attachment_id = load_attachments(sage_intacct_connection, created_journal_entry['data']['glbatch']['RECORDNO'], expense_group)

        if created_attachment_id:
            try:
                sage_intacct_connection.update_journal_entry(journal_entry_object, journal_entry_lineitem_object, created_attachment_id, created_journal_entry['data']['glbatch']['RECORDNO'])
                journal_entry_object.supdoc_id = created_attachment_id
                journal_entry_object.save()
            except Exception:
                error = traceback.format_exc()
                logger.info(
                    'Updating Attachment failed for expense group id %s / workspace id %s Error: %s',
                    expense_group.id, expense_group.workspace_id, {'error': error}
                )
    
    except SageIntacctCredential.DoesNotExist:
        logger.info(
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

        task_log.save()

    except BulkError as exception:
        logger.info(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail
        task_log.sage_intacct_errors = None

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Journal Entry')
    
    except (InvalidTokenError, NoPrivilegeError) as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Journal Entry')

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save()
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)

    if last_export:
        update_last_export_details(expense_group.workspace_id)


def create_expense_report(expense_group: ExpenseGroup, task_log_id: int, last_export: bool):
    task_log = TaskLog.objects.get(id=task_log_id)
    if task_log.status not in ['IN_PROGRESS', 'COMPLETE']:
        task_log.status = 'IN_PROGRESS'
        task_log.save()
    else:
        return

    configuration = Configuration.objects.get(workspace_id=expense_group.workspace_id)

    try:
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

        if configuration.auto_map_employees and configuration.auto_create_destination_entity \
            and configuration.auto_map_employees != 'EMPLOYEE_CODE':
            create_or_update_employee_mapping(
                expense_group, sage_intacct_connection, configuration.auto_map_employees,
                configuration.employee_field_mapping
            )

        __validate_expense_group(expense_group, configuration)

        with transaction.atomic():

            expense_report_object = ExpenseReport.create_expense_report(expense_group)

            expense_report_lineitems_objects = ExpenseReportLineitem.create_expense_report_lineitems(
                expense_group, configuration
            )

            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)

            sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

            created_expense_report = sage_intacct_connection.post_expense_report(
                expense_report_object, expense_report_lineitems_objects)

            record_no = created_expense_report['data']['eexpenses']['RECORDNO']
            expense_report = sage_intacct_connection.get_expense_report(record_no, ['RECORD_URL'])
            url_id = expense_report['eexpenses']['RECORD_URL'].split('?.r=', 1)[1]

            details = {
                'key': record_no,
                'url_id': url_id
            }
            task_log.detail = details
            task_log.expense_report = expense_report_object
            task_log.sage_intacct_errors = None
            task_log.status = 'COMPLETE'

            task_log.save()

            expense_group.exported_at = datetime.now()
            expense_group.response_logs = details
            expense_group.export_type = 'EXPENSE_REPORT'
            expense_group.save()
            resolve_errors_for_exported_expense_group(expense_group)

        generate_export_url_and_update_expense(expense_group)

        created_attachment_id = load_attachments(sage_intacct_connection, record_no, expense_group)
        if created_attachment_id:
            try:
                sage_intacct_connection.update_expense_report(record_no, created_attachment_id)
                expense_report_object.supdoc_id = created_attachment_id
                expense_report_object.save()
            except Exception:
                error = traceback.format_exc()
                logger.info(
                    'Updating Attachment failed for expense group id %s / workspace id %s Error: %s',
                    expense_group.id, expense_group.workspace_id, {'error': error}
                )
    except SageIntacctCredential.DoesNotExist:
        logger.info(
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

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)

    except BulkError as exception:
        logger.info(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail
        task_log.sage_intacct_errors = None

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Expense Reports')

    except (InvalidTokenError, NoPrivilegeError) as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Expense Reports')   

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save()
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)

    if last_export:
        update_last_export_details(expense_group.workspace_id)


def create_bill(expense_group: ExpenseGroup, task_log_id: int, last_export: bool):
    task_log = TaskLog.objects.get(id=task_log_id)
    if task_log.status not in ['IN_PROGRESS', 'COMPLETE']:
        task_log.status = 'IN_PROGRESS'
        task_log.save()
    else:
        return

    configuration = Configuration.objects.get(workspace_id=expense_group.workspace_id)

    try:
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

        if configuration.auto_map_employees and configuration.auto_create_destination_entity \
            and expense_group.fund_source == 'PERSONAL' and \
                configuration.auto_map_employees != 'EMPLOYEE_CODE':
            create_or_update_employee_mapping(
                expense_group, sage_intacct_connection, configuration.auto_map_employees,
                configuration.employee_field_mapping
            )

        __validate_expense_group(expense_group, configuration)

        with transaction.atomic():
            bill_object = Bill.create_bill(expense_group)

            bill_lineitems_objects = BillLineitem.create_bill_lineitems(expense_group, configuration)

            created_bill = sage_intacct_connection.post_bill(bill_object, \
                                                             bill_lineitems_objects)

            bill = sage_intacct_connection.get_bill(created_bill['data']['apbill']['RECORDNO'], ['RECORD_URL'])
            url_id = bill['apbill']['RECORD_URL'].split('?.r=', 1)[1]
            created_bill['url_id'] = url_id

            task_log.detail = created_bill
            task_log.bill = bill_object
            task_log.sage_intacct_errors = None
            task_log.status = 'COMPLETE'

            task_log.save()

            expense_group.exported_at = datetime.now()
            expense_group.response_logs = created_bill
            expense_group.export_type = 'BILL'
            expense_group.save()
            resolve_errors_for_exported_expense_group(expense_group)
        
        generate_export_url_and_update_expense(expense_group)

        created_attachment_id = load_attachments(sage_intacct_connection, created_bill['data']['apbill']['RECORDNO'], expense_group)
        if created_attachment_id:
            try:
                sage_intacct_connection.update_bill(created_bill['data']['apbill']['RECORDNO'], created_attachment_id)
                bill_object.supdoc_id = created_attachment_id
                bill_object.save()
            except Exception:
                error = traceback.format_exc()
                logger.info(
                    'Updating Attachment failed for expense group id %s / workspace id %s Error: %s',
                    expense_group.id, expense_group.workspace_id, {'error': error}
                )

    except SageIntacctCredential.DoesNotExist:
        logger.info(
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

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)
    
    except BulkError as exception:
        logger.info(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail
        task_log.sage_intacct_errors = None

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Bills')
    
    except (InvalidTokenError, NoPrivilegeError) as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Bills')

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save()
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)
    
    if last_export:
        update_last_export_details(expense_group.workspace_id)


def create_charge_card_transaction(expense_group: ExpenseGroup, task_log_id: int, last_export: bool):
    task_log = TaskLog.objects.get(id=task_log_id)
    if task_log.status not in ['IN_PROGRESS', 'COMPLETE']:
        task_log.status = 'IN_PROGRESS'
        task_log.save()
    else:
        return

    configuration = Configuration.objects.get(workspace_id=expense_group.workspace_id)
    try:
        merchant = expense_group.expenses.first().vendor
        get_or_create_credit_card_vendor(merchant, expense_group.workspace_id)
        __validate_expense_group(expense_group, configuration)
        with transaction.atomic():

            charge_card_transaction_object = ChargeCardTransaction.create_charge_card_transaction(expense_group)

            charge_card_transaction_lineitems_objects = ChargeCardTransactionLineitem. \
                create_charge_card_transaction_lineitems(expense_group, configuration)

            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=expense_group.workspace_id)

            sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

            created_charge_card_transaction = sage_intacct_connection.post_charge_card_transaction(
                charge_card_transaction_object, charge_card_transaction_lineitems_objects)

            charge_card_transaction = sage_intacct_connection.get_charge_card_transaction(
                created_charge_card_transaction['key'], ['RECORD_URL'])
            url_id = charge_card_transaction['cctransaction']['RECORD_URL'].split('?.r=', 1)[1]
            created_charge_card_transaction['url_id'] = url_id

            task_log.detail = created_charge_card_transaction
            task_log.charge_card_transaction = charge_card_transaction_object
            task_log.sage_intacct_errors = None
            task_log.status = 'COMPLETE'

            task_log.save()

            expense_group.exported_at = datetime.now()
            expense_group.response_logs = created_charge_card_transaction
            expense_group.export_type = 'CHARGE_CARD_TRANSACTION'
            expense_group.save()
            resolve_errors_for_exported_expense_group(expense_group)

        generate_export_url_and_update_expense(expense_group)

        created_attachment_id = load_attachments(sage_intacct_connection, created_charge_card_transaction['key'], expense_group)
        if created_attachment_id:
            try:
                sage_intacct_connection.update_charge_card_transaction(created_charge_card_transaction['key'], created_attachment_id)
                charge_card_transaction_object.supdoc_id = created_attachment_id
                charge_card_transaction_object.save()
            except Exception:
                error = traceback.format_exc()
                logger.info(
                    'Updating Attachment failed for expense group id %s / workspace id %s Error: %s',
                    expense_group.id, expense_group.workspace_id, {'error': error}
                )
    except SageIntacctCredential.DoesNotExist:
        logger.info(
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

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)

    except BulkError as exception:
        logger.info(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail
        task_log.sage_intacct_errors = None

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Charge Card Transactions')
    
    except (InvalidTokenError, NoPrivilegeError) as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Charge Card Transactions')

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save()
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)

    if last_export:
        update_last_export_details(expense_group.workspace_id)


def check_expenses_reimbursement_status(expenses):
    all_expenses_paid = True

    for expense in expenses:
        reimbursement = Reimbursement.objects.filter(settlement_id=expense.settlement_id).first()

        if reimbursement.state != 'COMPLETE':
            all_expenses_paid = False

    return all_expenses_paid


def create_ap_payment(workspace_id):
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    platform = PlatformConnector(fyle_credentials=fyle_credentials)
    platform.reimbursements.sync()

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
                        bill.save()

                        task_log.detail = created_ap_payment
                        task_log.ap_payment = ap_payment_object
                        task_log.sage_intacct_errors = None
                        task_log.status = 'COMPLETE'

                        task_log.save()

                except SageIntacctCredential.DoesNotExist:
                    logger.info(
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

                    task_log.save()

                except BulkError as exception:
                    logger.info(exception.response)
                    detail = exception.response
                    task_log.status = 'FAILED'
                    task_log.detail = detail
                    task_log.sage_intacct_errors = None

                    task_log.save()

                except WrongParamsError as exception:
                    logger.info(exception.response)
                    task_log.status = 'FAILED'
                    task_log.detail = exception.response

                    task_log.save()

                except InvalidTokenError as exception:
                    logger.info(exception.response)
                    task_log.status = 'FAILED'
                    task_log.detail = exception.response

                    task_log.save()

                except NoPrivilegeError as exception:
                    logger.info(exception.response)
                    task_log.status = 'FAILED'
                    task_log.detail = exception.response

                    task_log.save()

                except Exception:
                    error = traceback.format_exc()
                    task_log.detail = {
                        'error': error
                    }
                    task_log.status = 'FATAL'
                    task_log.save()
                    logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id,
                                 task_log.detail)


def create_sage_intacct_reimbursement(workspace_id):
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    platform = PlatformConnector(fyle_credentials=fyle_credentials)
    platform.reimbursements.sync()

    expense_reports: List[ExpenseReport] = ExpenseReport.objects.filter(
        payment_synced=False, expense_group__workspace_id=workspace_id,
        expense_group__fund_source='PERSONAL'
    ).all()

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
                    expense_report.save()

                    task_log.detail = created__sage_intacct_reimbursement
                    task_log.sage_intacct_reimbursement = sage_intacct_reimbursement_object
                    task_log.sage_intacct_errors = None
                    task_log.status = 'COMPLETE'

                    task_log.save()

            except SageIntacctCredential.DoesNotExist:
                logger.info(
                    'Sage-Intacct Credentials not found for workspace_id %s / expense group %s',
                    workspace_id,
                    expense_report.expense_group
                )
                detail = {
                    'expense_group_id': expense_report.expense_group.id,
                    'message': 'Sage-Intacct Account not connected'
                }
                task_log.status = 'FAILED'
                task_log.detail = detail

                task_log.save()

            except BulkError as exception:
                logger.info(exception.response)
                detail = exception.response
                task_log.status = 'FAILED'
                task_log.detail = detail
                task_log.sage_intacct_errors = None

                task_log.save()

            except WrongParamsError as exception:
                logger.info(exception.response)
                task_log.status = 'FAILED'
                task_log.detail = exception.response

                task_log.save()
            
            except InvalidTokenError as exception:
                logger.info(exception.response)
                task_log.status = 'FAILED'
                task_log.detail = exception.response

                task_log.save()
            
            except NoPrivilegeError as exception:
                logger.info(exception.response)
                task_log.status = 'FAILED'
                task_log.detail = exception.response

                task_log.save()

            except Exception:
                error = traceback.format_exc()
                task_log.detail = {
                    'error': error
                }
                task_log.status = 'FATAL'
                task_log.save()
                logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id,
                                task_log.detail)


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
    try:
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)

        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, workspace_id)
    except (SageIntacctCredential.DoesNotExist, InvalidTokenError, NoPrivilegeError):
        logger.info('Invalid Token or SageIntacct credentials does not exist - %s or Insufficient permission to access the requested module', workspace_id)
        return 

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

            if 'apbill' in bill_object and bill_object['apbill']['STATE'] == 'Paid':
                line_items = BillLineitem.objects.filter(bill_id=bill.id)
                for line_item in line_items:
                    expense = line_item.expense
                    expense.paid_on_sage_intacct = True
                    expense.save()

                bill.paid_on_sage_intacct = True
                bill.payment_synced = True
                bill.save()

    if expense_reports:
        expense_report_ids = get_all_sage_intacct_expense_report_ids(expense_reports)

        for expense_report in expense_reports:
            expense_report_object = sage_intacct_connection.get_expense_report(
                expense_report_ids[expense_report.expense_group_id]['sage_object_id'])

            if 'eexpenses' in expense_report_object and expense_report_object['eexpenses']['STATE'] == 'Paid':
                line_items = ExpenseReportLineitem.objects.filter(expense_report_id=expense_report.id)
                for line_item in line_items:
                    expense = line_item.expense
                    expense.paid_on_sage_intacct = True
                    expense.save()

                expense_report.paid_on_sage_intacct = True
                expense_report.payment_synced = True
                expense_report.save()




def process_fyle_reimbursements(workspace_id):
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    platform.reimbursements.sync()

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
        reimbursements_list = []
        for reimbursement_id in reimbursement_ids:
            reimbursement_object = {'id': reimbursement_id}
            reimbursements_list.append(reimbursement_object)

        platform.reimbursements.bulk_post_reimbursements(reimbursements_list)
        platform.reimbursements.sync()


def update_expense_and_post_summary(in_progress_expenses: List[Expense], workspace_id: int, fund_source: str) -> None:
    """
    Update expense and post accounting export summary
    :param in_progress_expenses: List of expenses
    :param workspace_id: Workspace ID
    :param fund_source: Fund source
    :return: None
    """
    fyle_org_id = Workspace.objects.get(pk=workspace_id).fyle_org_id
    update_expenses_in_progress(in_progress_expenses)
    post_accounting_export_summary(fyle_org_id, workspace_id, fund_source)


def generate_export_url_and_update_expense(expense_group: ExpenseGroup) -> None:
    """
    Generate export url and update expense
    :param expense_group: Expense Group
    :return: None
    """
    try:
        export_id = expense_group.response_logs['data']['url_id']
        url = '{intacct_app_url}/ia/acct/ur.phtml?.r={export_id}'.format(
            intacct_app_url=settings.INTACCT_APP_URL,
            export_id=export_id
        )
    except Exception as error:
        # Defaulting it to Intacct app url, worst case scenario if we're not able to parse it properly
        url = settings.INTACCT_APP_URL
        logger.error('Error while generating export url %s', error)

    update_complete_expenses(expense_group.expenses.all(), url)
