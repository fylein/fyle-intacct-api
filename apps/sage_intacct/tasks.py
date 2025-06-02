import logging
import traceback
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.db.models.functions import Lower
from apps.fyle.helpers import patch_request

from apps.exceptions import ValueErrorWithResponse
from fyle_intacct_api.utils import invalidate_sage_intacct_credentials
from fyle_integrations_platform_connector import PlatformConnector
from sageintacctsdk.exceptions import (
    NoPrivilegeError,
    WrongParamsError,
    InvalidTokenError
)
from fyle_accounting_mappings.models import (
    Mapping,
    EmployeeMapping,
    CategoryMapping,
    ExpenseAttribute,
    DestinationAttribute,
)

from apps.tasks.models import TaskLog, Error
from apps.mappings.models import GeneralMapping
from apps.fyle.models import ExpenseGroup, Expense
from fyle_intacct_api.exceptions import BulkError
from fyle_intacct_api.logging_middleware import get_logger
from apps.sage_intacct.utils import SageIntacctConnector
from apps.fyle.actions import (
    update_expenses_in_progress,
    update_failed_expenses,
    update_complete_expenses,
    post_accounting_export_summary
)
from apps.workspaces.models import (
    SageIntacctCredential,
    FyleCredential,
    Configuration,
    LastExportDetail
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
from apps.sage_intacct.errors.helpers import (
    error_matcher,
    remove_support_id,
    get_entity_values,
    replace_destination_id_with_values
)

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def patch_integration_settings(workspace_id: int, errors: int = 0) -> None:
    """
    Patch integration settings
    """
    refresh_token = FyleCredential.objects.get(workspace_id=workspace_id).refresh_token
    url = '{}/integrations/'.format(settings.INTEGRATIONS_SETTINGS_API)
    payload = {
        'tpa_name': 'Fyle Sage Intacct Integration',
        'errors_count': errors
    }

    try:
        patch_request(url, payload, refresh_token)
    except Exception as error:
        logger.error(error, exc_info=True)


def update_last_export_details(workspace_id: int) -> LastExportDetail:
    """
    Update last export details
    :param workspace_id: Workspace Id
    :return: Last Export Detail
    """
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

    patch_integration_settings(workspace_id, errors=failed_exports)
    try:
        post_accounting_export_summary(workspace_id=workspace_id)
    except Exception as e:
        logger.error(f"Error posting accounting export summary: {e} for workspace id {workspace_id}")

    return last_export_detail


def load_attachments(sage_intacct_connection: SageIntacctConnector, expense_group: ExpenseGroup) -> str:
    """
    Get attachments from Fyle and upload them to Sage Intacct
    :param sage_intacct_connection: Sage Intacct Connection
    :param expense_group: Expense group
    :return: Final supdoc_id string if successful, else None
    """
    try:
        fyle_credentials = FyleCredential.objects.get(workspace_id=expense_group.workspace_id)
        file_ids_list = expense_group.expenses.values_list('file_ids', flat=True)
        platform = PlatformConnector(fyle_credentials)

        supdoc_base_id = expense_group.id
        attachment_number = 1
        final_supdoc_id = False

        for file_ids in file_ids_list:
            for file_id in file_ids:
                attachment = platform.files.bulk_generate_file_urls([{'id': file_id}])
                supdoc_id = sage_intacct_connection.post_attachments(attachment, supdoc_base_id, attachment_number)

                if supdoc_id and attachment_number == 1:
                    final_supdoc_id = supdoc_id

                attachment_number += 1

        return final_supdoc_id

    except Exception:
        error = traceback.format_exc()
        logger.info(
            'Attachment failed for expense group id %s / workspace id %s. Error: %s',
            expense_group.id, expense_group.workspace_id, {'error': error}
        )


def create_or_update_employee_mapping(
    expense_group: ExpenseGroup,
    sage_intacct_connection: SageIntacctConnector,
    auto_map_employees_preference: str,
    employee_field_mapping: str
) -> None:
    """
    Create or update employee mapping
    :param expense_group: Expense Group
    :param sage_intacct_connection: Sage Intacct Connection
    :param auto_map_employees_preference: Auto map employees preference
    :param employee_field_mapping: Employee field mapping
    """
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


def get_or_create_credit_card_vendor(workspace_id: int, configuration: Configuration, merchant: str = None, sage_intacct_connection: SageIntacctConnector = None) -> DestinationAttribute:
    """
    Get or create default vendor
    :param merchant: Fyle Expense Merchant
    :param workspace_id: Workspace Id
    :return: Destination Attribute for Vendor
    """
    if not sage_intacct_connection:
        sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, workspace_id)

    vendor = None

    if (
        merchant
        and configuration.corporate_credit_card_expenses_object
        and (
            configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION'
            or (
                configuration.corporate_credit_card_expenses_object == 'JOURNAL_ENTRY'
                and configuration.use_merchant_in_journal_line
            )
        )
    ):
        try:
            is_create = configuration.auto_create_merchants_as_vendors and not configuration.import_vendors_as_merchants
            vendor = sage_intacct_connection.get_or_create_vendor(merchant, create=is_create)
        except WrongParamsError as bad_request:
            logger.info(bad_request.response)

    if not vendor:
        vendor = sage_intacct_connection.get_or_create_vendor('Credit Card Misc', create=True)

    return vendor


def resolve_errors_for_exported_expense_group(expense_group: ExpenseGroup) -> None:
    """
    Resolve errors for exported expense group
    :param expense_group: Expense group
    """
    Error.objects.filter(workspace_id=expense_group.workspace_id, expense_group=expense_group, is_resolved=False).update(is_resolved=True, updated_at=datetime.now(timezone.utc))


def handle_sage_intacct_errors(exception: Exception, expense_group: ExpenseGroup, task_log: TaskLog, export_type: str) -> None:
    """
    Handle Sage Intacct errors
    :param exception: Exception
    :param expense_group: Expense Group
    :param task_log: Task Log
    :param export_type: Export Type
    :return: None
    """
    logger.info(exception.__dict__)

    errors = []
    is_parsed = False
    article_link = None
    attribute_type = None
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

    if 'Credit Card Misc vendor not found' in exception.response:
        brand_name = 'Fyle' if settings.BRAND_ID == 'fyle' else 'Expense Management'
        error_msg = '''Merchant from expense not found as a vendor in Sage Intacct. {0} couldn't auto-create the default vendor "Credit Card Misc". Please manually create this vendor in Sage Intacct, then retry.'''.format(brand_name)
        error_title = 'Vendor creation failed in Sage Intacct'

    error_msg = remove_support_id(error_msg)
    error_dict = error_matcher(error_msg)
    if error_dict:
        error_entity_values = get_entity_values(error_dict, expense_group.workspace_id)
        if error_entity_values:
            error_msg = replace_destination_id_with_values(error_msg, error_entity_values)
            is_parsed = True
            article_link = error_dict['article_link']
            attribute_type = error_dict['attribute_type']

    error, created = Error.objects.update_or_create(
        workspace_id=expense_group.workspace_id,
        expense_group=expense_group,
        defaults={
            'type': 'INTACCT_ERROR',
            'error_title': error_title,
            'error_detail': error_msg,
            'is_resolved': False,
            'is_parsed': is_parsed,
            'attribute_type': attribute_type,
            'article_link': article_link
        }
    )

    error.increase_repetition_count_by_one(created)

    task_log.status = 'FAILED'
    task_log.detail = None
    task_log.sage_intacct_errors = errors
    task_log.save()

    update_failed_expenses(expense_group.expenses.all(), False)
    post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)


def get_employee_mapping(employee_email: str, workspace_id: int, configuration: Configuration) -> EmployeeMapping:
    """
    Get employee mapping
    :param employee_email: Employee Email
    :param workspace_id: Workspace Id
    :param configuration: Configuration
    :return: Employee Mapping
    """
    entity = EmployeeMapping.objects.get(
        source_employee__value=employee_email,
        workspace_id=workspace_id
    )
    if configuration.employee_field_mapping == 'EMPLOYEE':
        return entity.destination_employee
    return entity.destination_vendor


def __validate_employee_mapping(expense_group: ExpenseGroup, configuration: Configuration) -> None:
    """
    Validate employee mapping
    :param expense_group: Expense Group
    :param configuration: Configuration
    :return: None
    """
    bulk_errors = []
    employee_email = expense_group.description.get('employee_email')
    workspace_id = expense_group.workspace_id
    employee_attribute = ExpenseAttribute.objects.filter(
        value=employee_email,
        workspace_id=workspace_id,
        attribute_type='EMPLOYEE'
    ).first()

    try:
        if expense_group.fund_source == 'PERSONAL':
            entity = get_employee_mapping(employee_email, workspace_id, configuration)
            if not entity:
                raise EmployeeMapping.DoesNotExist

        elif configuration.corporate_credit_card_expenses_object == 'JOURNAL_ENTRY':
            if settings.BRAND_ID == 'fyle' and not configuration.use_merchant_in_journal_line:
                entity = get_employee_mapping(employee_email, workspace_id, configuration)
                if not entity:
                    raise EmployeeMapping.DoesNotExist

        elif configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            entity = EmployeeMapping.objects.get(
                source_employee__value=employee_email,
                workspace_id=workspace_id
            )
            if not entity.destination_employee:
                raise EmployeeMapping.DoesNotExist

    except EmployeeMapping.DoesNotExist:
        bulk_errors.append({
            'row': None,
            'expense_group_id': expense_group.id,
            'value': employee_email,
            'type': 'Employee Mapping',
            'message': 'Employee Mapping not found'
        })

        if employee_attribute:
            error, created = Error.get_or_create_error_with_expense_group(expense_group, employee_attribute)
            error.increase_repetition_count_by_one(created)

    if bulk_errors:
        raise BulkError('Mappings are missing', bulk_errors)


def __validate_expense_group(expense_group: ExpenseGroup, configuration: Configuration) -> None:
    """
    Validate expense group
    :param expense_group: Expense Group
    :param configuration: Configuration
    :return: None
    """
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

    if expense_group.fund_source == 'CCC':
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
                error, created = Error.get_or_create_error_with_expense_group(expense_group, category_attribute)
                error.increase_repetition_count_by_one(created)

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


def create_journal_entry(expense_group: ExpenseGroup, task_log_id: int, last_export: bool, is_auto_export: bool) -> None:
    """
    Create journal entry
    :param expense_group: Expense Group
    :param task_log_id: Task Log Id
    :param last_export: Last Export
    :param is_auto_export: Is auto export
    :return: None
    """
    worker_logger = get_logger()
    task_log: TaskLog = TaskLog.objects.get(id=task_log_id)
    worker_logger.info('Creating Journal Entry for Expense Group %s, current state is %s', expense_group.id, task_log.status)

    if task_log.status not in ['IN_PROGRESS', 'COMPLETE']:
        task_log.status = 'IN_PROGRESS'
        task_log.save()
    else:
        return

    in_progress_expenses = []
    # Don't include expenses with previous export state as ERROR and it's an auto import/export run
    if not (is_auto_export and expense_group.expenses.first().previous_export_state == 'ERROR'):
        try:
            in_progress_expenses.extend(expense_group.expenses.all())
            update_expense_and_post_summary(in_progress_expenses, expense_group.workspace_id, expense_group.fund_source)
        except Exception as e:
            logger.error('Error while updating expenses for expense_group_id: %s and posting accounting export summary %s', expense_group.id, e)

    configuration = Configuration.objects.get(workspace_id=expense_group.workspace_id)

    last_export_failed = False

    try:
        __validate_expense_group(expense_group, configuration)
        logger.info('Validated Expense Group %s successfully', expense_group.id)
        sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(expense_group.workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

        if settings.BRAND_ID == 'fyle':
            if configuration.auto_map_employees and configuration.auto_create_destination_entity \
                and configuration.auto_map_employees != 'EMPLOYEE_CODE':
                create_or_update_employee_mapping(
                    expense_group, sage_intacct_connection, configuration.auto_map_employees,
                    configuration.employee_field_mapping
                )
        else:
            merchant = expense_group.expenses.first().vendor
            get_or_create_credit_card_vendor(expense_group.workspace_id, configuration, merchant, sage_intacct_connection)

        __validate_employee_mapping(expense_group, configuration)
        worker_logger.info('Validated Employee mapping %s successfully', expense_group.id)

        if not task_log.supdoc_id:
            supdoc_id = load_attachments(sage_intacct_connection, expense_group)
            if supdoc_id:
                task_log.supdoc_id = supdoc_id
                task_log.save()

        with transaction.atomic():

            journal_entry_object = JournalEntry.create_journal_entry(expense_group, task_log.supdoc_id)

            journal_entry_lineitem_object = JournalEntryLineitem.create_journal_entry_lineitems(expense_group, configuration, sage_intacct_connection)

            created_journal_entry = sage_intacct_connection.post_journal_entry(journal_entry_object, journal_entry_lineitem_object)
            worker_logger.info('Created Journal Entry with Expense Group %s successfully', expense_group.id)

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

        try:
            generate_export_url_and_update_expense(expense_group)
        except Exception as e:
            logger.error('Error while updating expenses for expense_group_id: %s and posting accounting export summary %s', expense_group.id, e)
        worker_logger.info('Updated Expense Group %s successfully', expense_group.id)

        if last_export:
            update_last_export_details(expense_group.workspace_id)

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

        if last_export:
            last_export_failed = True

    except BulkError as exception:
        logger.info(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail
        task_log.sage_intacct_errors = None

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)

        if last_export:
            last_export_failed = True

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Journal Entry')
        if last_export:
            last_export_failed = True

    except NoPrivilegeError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Journal Entry')
        if last_export:
            last_export_failed = True

    except InvalidTokenError as exception:
        invalidate_sage_intacct_credentials(expense_group.workspace_id, sage_intacct_credentials)
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Journal Entry')

        if last_export:
            last_export_failed = True

    except ValueErrorWithResponse as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Journal Entry')

        if last_export:
            last_export_failed = True

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)

    if last_export and last_export_failed:
        update_last_export_details(expense_group.workspace_id)


def create_expense_report(expense_group: ExpenseGroup, task_log_id: int, last_export: bool, is_auto_export: bool) -> None:
    """
    Create expense report
    :param expense_group: Expense Group
    :param task_log_id: Task Log Id
    :param last_export: Last Export
    :param is_auto_export: Is auto export
    :return: None
    """
    worker_logger = get_logger()
    task_log = TaskLog.objects.get(id=task_log_id)
    worker_logger.info('Creating Expense Report for Expense Group %s, current state is %s', expense_group.id, task_log.status)

    if task_log.status not in ['IN_PROGRESS', 'COMPLETE']:
        task_log.status = 'IN_PROGRESS'
        task_log.save()
    else:
        return

    in_progress_expenses = []
    # Don't include expenses with previous export state as ERROR and it's an auto import/export run
    if not (is_auto_export and expense_group.expenses.first().previous_export_state == 'ERROR'):
        try:
            in_progress_expenses.extend(expense_group.expenses.all())
            update_expense_and_post_summary(in_progress_expenses, expense_group.workspace_id, expense_group.fund_source)
        except Exception as e:
            logger.error('Error while updating expenses for expense_group_id: %s and posting accounting export summary %s', expense_group.id, e)

    configuration = Configuration.objects.get(workspace_id=expense_group.workspace_id)

    last_export_failed = False

    try:
        __validate_expense_group(expense_group, configuration)
        worker_logger.info('Validated Expense Group %s successfully', expense_group.id)
        sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(expense_group.workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

        if configuration.auto_map_employees and configuration.auto_create_destination_entity \
            and configuration.auto_map_employees != 'EMPLOYEE_CODE':
            create_or_update_employee_mapping(
                expense_group, sage_intacct_connection, configuration.auto_map_employees,
                configuration.employee_field_mapping
            )

        __validate_employee_mapping(expense_group, configuration)
        worker_logger.info('Validated Employee mapping %s successfully', expense_group.id)

        if not task_log.supdoc_id:
            supdoc_id = load_attachments(sage_intacct_connection, expense_group)
            if supdoc_id:
                task_log.supdoc_id = supdoc_id
                task_log.save()

        with transaction.atomic():

            expense_report_object = ExpenseReport.create_expense_report(expense_group, task_log.supdoc_id)

            expense_report_lineitems_objects = ExpenseReportLineitem.create_expense_report_lineitems(
                expense_group, configuration
            )

            sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(expense_group.workspace_id)

            sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

            created_expense_report = sage_intacct_connection.post_expense_report(
                expense_report_object, expense_report_lineitems_objects)
            worker_logger.info('Created Expense Report with Expense Group %s successfully', expense_group.id)

            record_no = created_expense_report['key']
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

        try:
            generate_export_url_and_update_expense(expense_group)
        except Exception as e:
            logger.error('Error while updating expenses for expense_group_id: %s and posting accounting export summary %s', expense_group.id, e)
        worker_logger.info('Updated Expense Group %s successfully', expense_group.id)

        if last_export:
            update_last_export_details(expense_group.workspace_id)

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
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)

        if last_export:
            last_export_failed = True

    except BulkError as exception:
        logger.info(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail
        task_log.sage_intacct_errors = None

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)

        if last_export:
            last_export_failed = True

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Expense Reports')

        if last_export:
            last_export_failed = True

    except NoPrivilegeError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Expense Reports')

        if last_export:
            last_export_failed = True

    except InvalidTokenError as exception:
        invalidate_sage_intacct_credentials(expense_group.workspace_id, sage_intacct_credentials)
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Expense Reports')

        if last_export:
            last_export_failed = True

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)

    if last_export:
        if last_export_failed:
            update_last_export_details(expense_group.workspace_id)

        if configuration.sync_fyle_to_sage_intacct_payments:
            create_sage_intacct_reimbursement(workspace_id=expense_group.workspace.id)


def create_bill(expense_group: ExpenseGroup, task_log_id: int, last_export: bool, is_auto_export: bool) -> None:
    """
    Create bill
    :param expense_group: Expense Group
    :param task_log_id: Task Log Id
    :param last_export: Last Export
    :param is_auto_export: Is auto export
    :return: None
    """
    worker_logger = get_logger()
    task_log = TaskLog.objects.get(id=task_log_id)
    worker_logger.info('Creating Bill for Expense Group %s, current state is %s', expense_group.id, task_log.status)

    if task_log.status not in ['IN_PROGRESS', 'COMPLETE']:
        task_log.status = 'IN_PROGRESS'
        task_log.save()
    else:
        return

    in_progress_expenses = []
    # Don't include expenses with previous export state as ERROR and it's an auto import/export run
    if not (is_auto_export and expense_group.expenses.first().previous_export_state == 'ERROR'):
        try:
            in_progress_expenses.extend(expense_group.expenses.all())
            update_expense_and_post_summary(in_progress_expenses, expense_group.workspace_id, expense_group.fund_source)
        except Exception as e:
            logger.error('Error while updating expenses for expense_group_id: %s and posting accounting export summary %s', expense_group.id, e)

    configuration = Configuration.objects.get(workspace_id=expense_group.workspace_id)
    last_export_failed = False

    try:
        __validate_expense_group(expense_group, configuration)
        worker_logger.info('Validated Expense Group %s successfully', expense_group.id)
        sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(expense_group.workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

        if configuration.auto_map_employees and configuration.auto_create_destination_entity \
            and expense_group.fund_source == 'PERSONAL' and \
                configuration.auto_map_employees != 'EMPLOYEE_CODE':
            create_or_update_employee_mapping(
                expense_group, sage_intacct_connection, configuration.auto_map_employees,
                configuration.employee_field_mapping
            )

        __validate_employee_mapping(expense_group, configuration)
        worker_logger.info('Validated Employee mapping %s successfully', expense_group.id)

        if not task_log.supdoc_id:
            supdoc_id = load_attachments(sage_intacct_connection, expense_group)
            if supdoc_id:
                task_log.supdoc_id = supdoc_id
                task_log.save()

        with transaction.atomic():
            bill_object = Bill.create_bill(expense_group, task_log.supdoc_id)

            bill_lineitems_objects = BillLineitem.create_bill_lineitems(expense_group, configuration)

            created_bill = sage_intacct_connection.post_bill(bill_object, \
                                                             bill_lineitems_objects)
            worker_logger.info('Created Bill with Expense Group %s successfully', expense_group.id)

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

        try:
            generate_export_url_and_update_expense(expense_group)
        except Exception as e:
            logger.error('Error while updating expenses for expense_group_id: %s and posting accounting export summary %s', expense_group.id, e)
        if last_export:
            update_last_export_details(expense_group.workspace_id)

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
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)

        if last_export:
            last_export_failed = True

    except BulkError as exception:
        logger.info(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail
        task_log.sage_intacct_errors = None

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)

        if last_export:
            last_export_failed = True

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Bills')

        if last_export:
            last_export_failed = True

    except NoPrivilegeError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Bills')

        if last_export:
            last_export_failed = True

    except InvalidTokenError as exception:
        invalidate_sage_intacct_credentials(expense_group.workspace_id, sage_intacct_credentials)
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Bills')

        if last_export:
            last_export_failed = True

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)

    if last_export:
        if last_export_failed:
            update_last_export_details(expense_group.workspace_id)

        if configuration.sync_fyle_to_sage_intacct_payments:
            create_ap_payment(workspace_id=expense_group.workspace.id)


def create_charge_card_transaction(expense_group: ExpenseGroup, task_log_id: int, last_export: bool, is_auto_export: bool) -> None:
    """
    Create charge card transaction
    :param expense_group: Expense Group
    :param task_log_id: Task Log Id
    :param last_export: Last Export
    :param is_auto_export: Is auto export
    :return: None
    """
    worker_logger = get_logger()
    task_log = TaskLog.objects.get(id=task_log_id)
    worker_logger.info('Creating Charge Card Transaction for Expense Group %s, current state is %s', expense_group.id, task_log.status)

    if task_log.status not in ['IN_PROGRESS', 'COMPLETE']:
        task_log.status = 'IN_PROGRESS'
        task_log.save()
    else:
        return

    in_progress_expenses = []
    # Don't include expenses with previous export state as ERROR and it's an auto import/export run
    if not (is_auto_export and expense_group.expenses.first().previous_export_state == 'ERROR'):
        try:
            in_progress_expenses.extend(expense_group.expenses.all())
            update_expense_and_post_summary(in_progress_expenses, expense_group.workspace_id, expense_group.fund_source)
        except Exception as e:
            logger.error('Error while updating expenses for expense_group_id: %s and posting accounting export summary %s', expense_group.id, e)

    configuration = Configuration.objects.get(workspace_id=expense_group.workspace_id)

    last_export_failed = False

    try:
        __validate_expense_group(expense_group, configuration)
        worker_logger.info('Validated Expense Group %s successfully', expense_group.id)
        sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(expense_group.workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, expense_group.workspace_id)

        merchant = expense_group.expenses.first().vendor
        vendor = get_or_create_credit_card_vendor(expense_group.workspace_id, configuration, merchant, sage_intacct_connection)

        vendor_id = vendor.destination_id if vendor else None
        __validate_employee_mapping(expense_group, configuration)
        worker_logger.info('Validated Employee mapping %s successfully', expense_group.id)

        if not task_log.supdoc_id:
            supdoc_id = load_attachments(sage_intacct_connection, expense_group)
            if supdoc_id:
                task_log.supdoc_id = supdoc_id
                task_log.save()

        with transaction.atomic():

            charge_card_transaction_object = ChargeCardTransaction.create_charge_card_transaction(expense_group, vendor_id, task_log.supdoc_id)

            charge_card_transaction_lineitems_objects = ChargeCardTransactionLineitem. \
                create_charge_card_transaction_lineitems(expense_group, configuration)

            created_charge_card_transaction = sage_intacct_connection.post_charge_card_transaction(
                charge_card_transaction_object, charge_card_transaction_lineitems_objects)
            worker_logger.info('Created Charge Card Transaction with Expense Group %s successfully', expense_group.id)

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

        try:
            generate_export_url_and_update_expense(expense_group)
        except Exception as e:
            logger.error('Error while updating expenses for expense_group_id: %s and posting accounting export summary %s', expense_group.id, e)

        if last_export:
            update_last_export_details(expense_group.workspace_id)

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
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)

        if last_export:
            last_export_failed = True

    except BulkError as exception:
        logger.info(exception.response)
        detail = exception.response
        task_log.status = 'FAILED'
        task_log.detail = detail
        task_log.sage_intacct_errors = None

        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)

        if last_export:
            last_export_failed = True

    except WrongParamsError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Charge Card Transactions')

        if last_export:
            last_export_failed = True

    except NoPrivilegeError as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Charge Card Transactions')

        if last_export:
            last_export_failed = True

    except InvalidTokenError as exception:
        invalidate_sage_intacct_credentials(expense_group.workspace_id, sage_intacct_credentials)
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Charge Card Transactions')

        if last_export:
            last_export_failed = True

    except ValueErrorWithResponse as exception:
        handle_sage_intacct_errors(exception, expense_group, task_log, 'Charge Card Transactions')

        if last_export:
            last_export_failed = True

    except Exception:
        error = traceback.format_exc()
        task_log.detail = {
            'error': error
        }
        task_log.status = 'FATAL'
        task_log.save()
        update_failed_expenses(expense_group.expenses.all(), True)
        post_accounting_export_summary(workspace_id=expense_group.workspace_id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source, is_failed=True)
        logger.exception('Something unexpected happened workspace_id: %s %s', task_log.workspace_id, task_log.detail)

    if last_export and last_export_failed:
        update_last_export_details(expense_group.workspace_id)


def check_expenses_reimbursement_status(expenses: list[Expense], workspace_id: int, platform: PlatformConnector, filter_credit_expenses: bool) -> bool:
    """
    Check if expenses are reimbursed
    :param expenses: Expenses
    :param workspace_id: Workspace Id
    :param platform: Platform
    :param filter_credit_expenses: Filter Credit Expenses
    :return: True if reimbursed, False otherwise
    """
    if expenses.first().paid_on_fyle:
        return True

    report_id = expenses.first().report_id

    expenses = platform.expenses.get(
        source_account_type=['PERSONAL_CASH_ACCOUNT'],
        filter_credit_expenses=filter_credit_expenses,
        report_id=report_id
    )

    is_paid = False
    if expenses:
        is_paid = expenses[0]['state'] == 'PAID'

    if is_paid:
        Expense.objects.filter(workspace_id=workspace_id, report_id=report_id, paid_on_fyle=False).update(paid_on_fyle=True, updated_at=datetime.now(timezone.utc))

    return is_paid


def validate_for_skipping_payment(export_module: Bill | ExpenseReport, workspace_id: int, type: str) -> bool:
    """
    Validate for skipping payment
    :param export_module: Export Module
    :param workspace_id: Workspace Id
    :param type: Type
    :return: True if payment is to be skipped, False otherwise
    """
    task_log = TaskLog.objects.filter(task_id='PAYMENT_{}'.format(export_module.expense_group.id), workspace_id=workspace_id, type=type).first()
    if task_log:
        now = timezone.now()

        if now - relativedelta(months=2) > task_log.created_at:
            export_module.is_retired = True
            export_module.save()
            return True

        elif now - relativedelta(months=1) > task_log.created_at and now - relativedelta(months=2) < task_log.created_at:
            # if updated_at is within 1 months will be skipped
            if task_log.updated_at > now - relativedelta(months=1):
                return True
        # If created is within 1 month
        elif now - relativedelta(months=1) < task_log.created_at:
            # Skip if updated within the last week
            if task_log.updated_at > now - relativedelta(weeks=1):
                return True

    return False


def create_ap_payment(workspace_id: int) -> None:
    """
    Create AP Payment
    :param workspace_id: Workspace Id
    :return: None
    """
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)
    filter_credit_expenses = False

    bills = Bill.objects.filter(
        payment_synced=False, expense_group__workspace_id=workspace_id,
        expense_group__fund_source='PERSONAL', is_retired=False
    ).all()

    if bills:
        for bill in bills:
            expense_group_reimbursement_status = check_expenses_reimbursement_status(
                bill.expense_group.expenses.all(),
                workspace_id=workspace_id,
                platform=platform,
                filter_credit_expenses=filter_credit_expenses
            )

            if expense_group_reimbursement_status:
                skip_payment = validate_for_skipping_payment(export_module=bill, workspace_id=workspace_id, type='CREATING_AP_PAYMENT')

                if skip_payment:
                    continue

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

                        sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace_id)
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
                        'expense_group_id': bill.expense_group.id,
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

                    if exception.response and (
                        "Oops, we can't find this transaction; enter a valid" in str(exception.response)
                        or 'No line items found' in str(exception.response)
                        or 'There is no due on the bill' in str(exception.response)
                    ):
                        bill.payment_synced = True
                        bill.paid_on_sage_intacct = True
                        bill.save()

                        task_log.delete()
                    else:
                        task_log.save()

                except InvalidTokenError as exception:
                    invalidate_sage_intacct_credentials(task_log.workspace_id, sage_intacct_credentials)
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


def create_sage_intacct_reimbursement(workspace_id: int) -> None:
    """
    Create Sage Intacct Reimbursement
    :param workspace_id: Workspace Id
    :return: None
    """
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    platform = PlatformConnector(fyle_credentials=fyle_credentials)
    filter_credit_expenses = False

    expense_reports: list[ExpenseReport] = ExpenseReport.objects.filter(
        payment_synced=False, expense_group__workspace_id=workspace_id,
        expense_group__fund_source='PERSONAL', is_retired=False
    ).all()

    for expense_report in expense_reports:
        expense_group_reimbursement_status = check_expenses_reimbursement_status(
            expense_report.expense_group.expenses.all(), workspace_id=workspace_id, platform=platform, filter_credit_expenses=filter_credit_expenses)
        if expense_group_reimbursement_status:

            skip_reimbursement = validate_for_skipping_payment(export_module=expense_report, workspace_id=workspace_id, type='CREATING_REIMBURSEMENT')
            if skip_reimbursement:
                continue

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
                    sage_intacct_reimbursement_object = SageIntacctReimbursement.create_sage_intacct_reimbursement(expense_report.expense_group)
                    expense_report_task_log = TaskLog.objects.get(expense_group=expense_report.expense_group)
                    record_key = expense_report_task_log.detail['key']

                    sage_intacct_reimbursement_lineitems_objects = SageIntacctReimbursementLineitem.create_sage_intacct_reimbursement_lineitems(
                        sage_intacct_reimbursement_object.expense_group,
                        record_key
                    )

                    sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace_id)
                    sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, workspace_id)
                    created__sage_intacct_reimbursement = sage_intacct_connection.post_sage_intacct_reimbursement(
                        sage_intacct_reimbursement_object,
                        sage_intacct_reimbursement_lineitems_objects
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

                if exception.response and (
                    'exceeds total amount due ()' in str(exception.response)
                    or 'exceeds total amount due (0)' in str(exception.response)
                    or 'Payment cannot be processed because one or more bills are already paid' in str(exception.response)
                    or 'The payment cannot be processed because one or more bills were paid' in str(exception.response)
                ):
                    expense_report.payment_synced = True
                    expense_report.paid_on_sage_intacct = True
                    expense_report.save()

                    task_log.delete()
                else:
                    task_log.save()

            except InvalidTokenError as exception:
                invalidate_sage_intacct_credentials(task_log.workspace_id, sage_intacct_credentials)
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
                logger.exception(
                    'Something unexpected happened workspace_id: %s %s',
                    task_log.workspace_id,
                    task_log.detail
                )


def get_all_sage_intacct_bill_ids(sage_objects: Bill) -> dict:
    """
    Get all sage intacct bill ids
    :param sage_objects: Sage Objects
    :return: Sage Intacct Bill Details
    """
    sage_intacct_bill_details = {}
    expense_group_ids = [sage_object.expense_group_id for sage_object in sage_objects]
    task_logs = TaskLog.objects.filter(expense_group_id__in=expense_group_ids).all()

    for task_log in task_logs:
        sage_intacct_bill_details[task_log.detail['data']['apbill']['RECORDNO']] = task_log.expense_group.id

    return sage_intacct_bill_details


def get_all_sage_intacct_expense_report_ids(sage_objects: ExpenseReport) -> dict:
    """
    Get all sage intacct expense report ids
    :param sage_objects: Sage Objects
    :return: Sage Intacct Expense Report Details
    """
    sage_intacct_expense_report_details = {}
    expense_group_ids = [sage_object.expense_group_id for sage_object in sage_objects]
    task_logs = TaskLog.objects.filter(expense_group_id__in=expense_group_ids).all()

    for task_log in task_logs:
        sage_intacct_expense_report_details[task_log.detail['key']] = task_log.expense_group.id
    return sage_intacct_expense_report_details


def check_sage_intacct_object_status(workspace_id: int) -> None:
    """
    Check Sage Intacct Object Status
    :param workspace_id: Workspace Id
    :return: None
    """
    try:
        sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace_id)
        sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, workspace_id)
    except (SageIntacctCredential.DoesNotExist, NoPrivilegeError):
        logger.info('SageIntacct credentials does not exist - %s or Insufficient permission to access the requested module', workspace_id)
        return
    except InvalidTokenError:
        invalidate_sage_intacct_credentials(workspace_id, sage_intacct_credentials)
        logger.info('Invalid Sage Intact Token for workspace_id - %s', workspace_id)
        return

    bills = Bill.objects.filter(
        expense_group__workspace_id=workspace_id,
        paid_on_sage_intacct=False,
        expense_group__fund_source='PERSONAL'
    ).all()

    expense_reports = ExpenseReport.objects.filter(
        expense_group__workspace_id=workspace_id,
        paid_on_sage_intacct=False,
        expense_group__fund_source='PERSONAL'
    ).all()

    if bills:
        bill_ids = get_all_sage_intacct_bill_ids(bills)  # {'bill_id (sage side)': 'expense_group_id'}

        bill_ids_batches = [list(bill_ids.keys())[i:i + 50] for i in range(0, len(bill_ids), 50)]

        for batch in bill_ids_batches:
            bills_details = sage_intacct_connection.get_bills(bill_ids=batch)

            for bill_detail in bills_details:
                if bill_detail.get('STATE') == 'Paid':
                    expense_group_id = bill_ids[bill_detail['RECORDNO']]
                    bill = bills.filter(expense_group_id=expense_group_id).first()
                    line_items = BillLineitem.objects.filter(bill_id=bill.id)

                    expenses_to_update = []
                    for line_item in line_items:
                        expense = line_item.expense
                        expense.paid_on_sage_intacct = True
                        expense.updated_at = datetime.now(timezone.utc)
                        expenses_to_update.append(expense)

                    if expenses_to_update:
                        Expense.objects.bulk_update(expenses_to_update, ['paid_on_sage_intacct', 'updated_at'], batch_size=50)

                    bill.paid_on_sage_intacct = True
                    bill.payment_synced = True
                    bill.save()

    if expense_reports:
        expense_report_ids = get_all_sage_intacct_expense_report_ids(expense_reports)  # {'expense_report_id (sage side)': 'expense_group_id'}

        expense_report_ids_batches = [list(expense_report_ids.keys())[i:i + 50] for i in range(0, len(expense_report_ids), 50)]

        for batch in expense_report_ids_batches:
            expense_reports_details = sage_intacct_connection.get_expense_reports(expense_report_ids=batch)

            for expense_report_detail in expense_reports_details:
                if expense_report_detail.get('STATE') == 'Paid':
                    expense_group_id = expense_report_ids[expense_report_detail['RECORDNO']]
                    expense_report = expense_reports.filter(expense_group_id=expense_group_id).first()
                    line_items = ExpenseReportLineitem.objects.filter(expense_report_id=expense_report.id)

                    expenses_to_update = []
                    for line_item in line_items:
                        expense = line_item.expense
                        expense.paid_on_sage_intacct = True
                        expense.updated_at = datetime.now(timezone.utc)
                        expenses_to_update.append(expense)

                    if expenses_to_update:
                        Expense.objects.bulk_update(expenses_to_update, ['paid_on_sage_intacct', 'updated_at'], batch_size=50)

                    expense_report.paid_on_sage_intacct = True
                    expense_report.payment_synced = True
                    expense_report.save()


def process_fyle_reimbursements(workspace_id: int) -> None:
    """
    Process Fyle Reimbursements
    :param workspace_id: Workspace Id
    :return: None
    """
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    reports_to_be_marked = set()
    payloads = []

    report_ids = Expense.objects.filter(fund_source='PERSONAL', paid_on_fyle=False, workspace_id=workspace_id).values_list('report_id').distinct()
    for report_id in report_ids:
        report_id = report_id[0]
        expenses = Expense.objects.filter(fund_source='PERSONAL', report_id=report_id, workspace_id=workspace_id).all()
        paid_expenses = expenses.filter(paid_on_sage_intacct=True)

        all_expense_paid = False
        if len(expenses):
            all_expense_paid = len(expenses) == len(paid_expenses)

        if all_expense_paid:
            payloads.append({'id': report_id, 'paid_notify_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
            reports_to_be_marked.add(report_id)

    if payloads:
        mark_paid_on_fyle(platform, payloads, reports_to_be_marked, workspace_id)


def mark_paid_on_fyle(platform: PlatformConnector, payloads:dict, reports_to_be_marked: list, workspace_id: int, retry_num: int = 10) -> None:
    """
    Mark Paid on Fyle
    :param platform: Platform
    :param payloads: Payloads
    :param reports_to_be_marked: Reports to be marked
    :param workspace_id: Workspace Id
    :param retry_num: Retry Number
    :return: None
    """
    try:
        logger.info('Marking reports paid on fyle for report ids - %s', reports_to_be_marked)
        logger.info('Payloads- %s', payloads)
        platform.reports.bulk_mark_as_paid(payloads)
        Expense.objects.filter(report_id__in=list(reports_to_be_marked), workspace_id=workspace_id, paid_on_fyle=False).update(paid_on_fyle=True, updated_at=datetime.now(timezone.utc))
    except Exception as e:
        error = traceback.format_exc()
        target_messages = ['Report is not in APPROVED or PAYMENT_PROCESSING State', 'Permission denied to perform this action.']
        error_response = e.response
        to_remove = set()

        for item in error_response.get('data', []):
            if item.get('message') in target_messages:
                Expense.objects.filter(report_id=item['key'], workspace_id=workspace_id, paid_on_fyle=False).update(paid_on_fyle=True, updated_at=datetime.now(timezone.utc))
                to_remove.add(item['key'])

        for report_id in to_remove:
            payloads = [payload for payload in payloads if payload['id'] != report_id]
            reports_to_be_marked.remove(report_id)

        if retry_num > 0 and payloads:
            retry_num -= 1
            logger.info('Retrying to mark reports paid on fyle, retry_num=%d', retry_num)
            mark_paid_on_fyle(platform, payloads, reports_to_be_marked, workspace_id, retry_num)

        else:
            logger.info('Retry limit reached or no payloads left. Failed to process payloads - %s:', reports_to_be_marked)

        error = {
            'error': error
        }
        logger.exception(error)


def update_expense_and_post_summary(in_progress_expenses: list[Expense], workspace_id: int, fund_source: str) -> None:
    """
    Update expense and post accounting export summary
    :param in_progress_expenses: List of expenses
    :param workspace_id: Workspace ID
    :param fund_source: Fund source
    :return: None
    """
    update_expenses_in_progress(in_progress_expenses)
    post_accounting_export_summary(workspace_id=workspace_id, expense_ids=[expense.id for expense in in_progress_expenses], fund_source=fund_source)


def generate_export_url_and_update_expense(expense_group: ExpenseGroup) -> None:
    """
    Generate export url and update expense
    :param expense_group: Expense Group
    :return: None
    """
    try:
        export_id = expense_group.response_logs['url_id']
        url = 'https://www.intacct.com/ia/acct/ur.phtml?.r={export_id}'.format(
            export_id=export_id
        )
    except Exception as error:
        # Defaulting it to Intacct app url, worst case scenario if we're not able to parse it properly
        url = 'https://www.intacct.com'
        logger.error('Error while generating export url %s', error)

    expense_group.export_url = url
    expense_group.save()

    update_complete_expenses(expense_group.expenses.all(), url)
    post_accounting_export_summary(workspace_id=expense_group.workspace.id, expense_ids=[expense.id for expense in expense_group.expenses.all()], fund_source=expense_group.fund_source)


def search_and_upsert_vendors(workspace_id: int, configuration: Configuration, expense_group_filters: dict, fund_source: str) -> bool:
    """
    Search the vendors not present in Destination Attribute and upsert them
    :param workspace_id: Workspace ID
    :param configuration: Configuration
    :param expense_group_filters: filters for expense group in export queue
    :param fund_source: Fund Source
    :return: True if missing vendors are present else False
    """
    vendors_list = set()

    # CCC Vendors
    if fund_source == 'CCC' and configuration.corporate_credit_card_expenses_object:
        ccc_group_ids = list(get_filtered_expense_group_ids(expense_group_filters=expense_group_filters))

        if ccc_group_ids and (configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION' or (
            configuration.corporate_credit_card_expenses_object == 'JOURNAL_ENTRY' and configuration.use_merchant_in_journal_line
        )):
            vendors = Expense.objects.filter(
                workspace_id=workspace_id,
                expensegroup__id__in=ccc_group_ids,
                vendor__isnull=False
            ).values_list('vendor', flat=True)
            vendors_list.update(v for v in vendors if v)

        elif ccc_group_ids and configuration.corporate_credit_card_expenses_object == 'JOURNAL_ENTRY' and configuration.employee_field_mapping == 'VENDOR':
            employee_names = get_employee_as_vendors_name(workspace_id=workspace_id, expense_group_ids=ccc_group_ids)
            vendors_list.update(name for name in employee_names if name)

    # Reimbursable Vendors
    if fund_source == 'PERSONAL' and configuration.reimbursable_expenses_object in ['BILL', 'JOURNAL_ENTRY'] and configuration.employee_field_mapping == 'VENDOR':
        reimb_group_ids = list(get_filtered_expense_group_ids(expense_group_filters=expense_group_filters))

        employee_names = get_employee_as_vendors_name(workspace_id=workspace_id, expense_group_ids=reimb_group_ids)
        vendors_list.update(name for name in employee_names if name)

    # Final DB check for missing vendors
    if vendors_list:
        existing_vendors = DestinationAttribute.objects.filter(
            workspace_id=workspace_id,
            attribute_type='VENDOR',
        ).annotate(lower_value=Lower('value')).filter(
            lower_value__in=[vendor.lower() for vendor in vendors_list]
        ).values_list('value', flat=True)

        missing_vendors = list(set(vendors_list) - set(existing_vendors))

        if missing_vendors:
            try:
                sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace_id)
                sage_intacct_connection = SageIntacctConnector(sage_intacct_credentials, workspace_id)
                sage_intacct_connection.search_and_create_vendors(workspace_id=workspace_id, missing_vendors=missing_vendors)
                return True
            except SageIntacctCredential.DoesNotExist:
                logger.info('Sage Intacct credentials does not exist workspace_id - %s', workspace_id)
                return False

    return False


def get_filtered_expense_group_ids(expense_group_filters: dict) -> list:
    """
    Get expense group ids
    :param fund_source: Fund Source
    :param expense_group_filters: Expense group filter
    """
    return ExpenseGroup.objects.filter(
        **expense_group_filters
    ).values_list('id', flat=True)


def get_employee_as_vendors_name(workspace_id: int, expense_group_ids: list) -> list:
    """
    Get employee as vendors
    :param workspace_id: Workspace ID
    :param expense_group_ids: Expense Group ID
    """
    employee_email_list = Expense.objects.filter(
        workspace_id=workspace_id,
        expensegroup__id__in=expense_group_ids,
        employee_email__isnull=False
    ).values_list('employee_email', flat=True)

    employee_attr_ids = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id,
        attribute_type='EMPLOYEE',
        value__in=employee_email_list
    ).values_list('id', flat=True)

    mapped_expense_attribute_ids = EmployeeMapping.objects.filter(
        workspace_id=workspace_id,
        destination_vendor_id__isnull=False,
        source_employee_id__in=employee_attr_ids
    ).values_list('source_employee_id', flat=True)

    unmapped_employee_ids = set(employee_attr_ids) - set(mapped_expense_attribute_ids)

    unmapped_employee_names = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id,
        attribute_type='EMPLOYEE',
        id__in=unmapped_employee_ids
    ).values_list('detail__full_name', flat=True)

    return unmapped_employee_names


def check_cache_and_search_vendors(workspace_id: int, fund_source: str) -> None:
    """
    Check cache and search vendors in Intacct
    :param workspace_id: Workspace ID
    :param expense_group_ids: Expense Group ID
    :param fund source: CCC/PERSONAL
    """
    expense_group_filters = {
        'workspace_id': workspace_id,
        'exported_at__isnull': True,
        'fund_source': fund_source
    }

    configuration = Configuration.objects.filter(workspace_id=workspace_id).first()

    vendor_cache_key = f"{fund_source}_vendor_cache_{workspace_id}"

    vendor_cache_timestamp = cache.get(key=vendor_cache_key)

    is_upserted = False

    if not vendor_cache_timestamp:
        logger.info("Vendor Cache not found for Workspace %s", workspace_id)
        is_upserted = search_and_upsert_vendors(
            workspace_id=workspace_id,
            configuration=configuration,
            expense_group_filters=expense_group_filters,
            fund_source=fund_source
        )

    if is_upserted:
        logger.info("Setting Vendor Cache for Workspace %s", workspace_id)
        cache.set(key=vendor_cache_key, value=datetime.now(timezone.utc), timeout=86400)
    elif vendor_cache_timestamp and not is_upserted:
        logger.info("Vendor Cache found for Workspace %s, last cached at %s", workspace_id, vendor_cache_timestamp)
