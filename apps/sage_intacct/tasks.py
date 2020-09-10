import logging
import traceback
from typing import List

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from sageintacctsdk.exceptions import WrongParamsError

from fyle_accounting_mappings.models import Mapping

from fyle_intacct_api.exceptions import BulkError

from apps.fyle.models import ExpenseGroup
from apps.tasks.models import TaskLog
from apps.workspaces.models import SageIntacctCredential, FyleCredential
from apps.fyle.utils import FyleConnector

from .models import ExpenseReport, ExpenseReportLineitem, Bill, BillLineitem
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
        claim_number = expense_group.description.get('claim_number')
        attachments = fyle_connector.get_attachments(expense_ids)
        supdoc_id = '{0}-{1}'.format(key, claim_number)
        return sage_intacct_connection.post_attachments(attachments, supdoc_id)
    except Exception:
        error = traceback.format_exc()
        logger.error(
            'Attachment failed for expense group id %s / workspace id %s \n Error: %s',
            expense_group.id, expense_group.workspace_id, error
        )

def schedule_expense_reports_creation(workspace_id: int, expense_group_ids: List[str], user):
    """
    Schedule expense reports creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :param user: user email
    :return: None
    """
    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            workspace_id=workspace_id, id__in=expense_group_ids, expensereport__id__isnull=True
        ).all()
    else:
        expense_groups = ExpenseGroup.objects.filter(
            workspace_id=workspace_id, expensereport__id__isnull=True
        ).all()

    fyle_credentials = FyleCredential.objects.get(
        workspace_id=workspace_id)
    fyle_connector = FyleConnector(fyle_credentials.refresh_token, workspace_id)
    fyle_sdk_connection = fyle_connector.connection
    jobs = fyle_sdk_connection.Jobs
    user_profile = fyle_sdk_connection.Employees.get_my_profile()['data']

    for expense_group in expense_groups:
        task_log, _ = TaskLog.objects.update_or_create(
            workspace_id=expense_group.workspace_id,
            expense_group=expense_group,
            defaults={
                'status': 'IN_PROGRESS',
                'type': 'CREATING_EXPENSE_REPORTS'
            }
        )
        created_job = jobs.trigger_now(
            callback_url='{0}{1}'.format(settings.API_URL, \
                '/workspaces/{0}/sage_intacct/expense_reports/'.format(workspace_id)),
            callback_method='POST', object_id=task_log.id, payload={
                'expense_group_id': expense_group.id,
                'task_log_id': task_log.id
            }, job_description='Create Expense Report: Workspace id - {0}, user - {1}, expense group id - {2}'.format(
                workspace_id, user, expense_group.id
            ),
            org_user_id=user_profile['id']
        )
        task_log.task_id = created_job['id']
        task_log.save()

def schedule_bills_creation(workspace_id: int, expense_group_ids: List[str], user):
    """
    Schedule bill creation
    :param expense_group_ids: List of expense group ids
    :param workspace_id: workspace id
    :param user: user email
    :return: None
    """
    if expense_group_ids:
        expense_groups = ExpenseGroup.objects.filter(
            workspace_id=workspace_id, id__in=expense_group_ids, bill__id__isnull=True
        ).all()
    else:
        expense_groups = ExpenseGroup.objects.filter(
            workspace_id=workspace_id, bill__id__isnull=True
        ).all()

    fyle_credentials = FyleCredential.objects.get(
        workspace_id=workspace_id)
    fyle_connector = FyleConnector(fyle_credentials.refresh_token, workspace_id)
    fyle_sdk_connection = fyle_connector.connection
    jobs = fyle_sdk_connection.Jobs
    user_profile = fyle_sdk_connection.Employees.get_my_profile()['data']

    for expense_group in expense_groups:
        task_log, _ = TaskLog.objects.update_or_create(
            workspace_id=expense_group.workspace_id,
            expense_group=expense_group,
            defaults={
                'status': 'IN_PROGRESS',
                'type': 'CREATING_BILLS'
            }
        )
        created_job = jobs.trigger_now(
            callback_url='{0}{1}'.format(settings.API_URL, \
                '/workspaces/{0}/sage_intacct/bills/'.format(workspace_id)),
            callback_method='POST', object_id=task_log.id, payload={
                'expense_group_id': expense_group.id,
                'task_log_id': task_log.id
            }, job_description='Create Bill: Workspace id - {0}, user - {1}, expense group id - {2}'.format(
                workspace_id, user, expense_group.id
            ),
            org_user_id=user_profile['id']
        )
        task_log.task_id = created_job['id']
        task_log.save()

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

    try:
        Mapping.objects.get(
            Q(destination_type='VENDOR') | Q(destination_type='EMPLOYEE'),
            source_type='EMPLOYEE',
            source__value=expense_group.description.get('employee_email'),
            workspace_id=expense_group.workspace_id
        )
    except Mapping.DoesNotExist:
        bulk_errors.append({
            'row': None,
            'expense_group_id': expense_group.id,
            'value': expense_group.description.get('employee_email'),
            'type': 'Employee Mapping',
            'message': 'Employee mapping not found'
        })

    expenses = expense_group.expenses.all()

    for lineitem in expenses:
        category = lineitem.category if lineitem.category == lineitem.sub_category else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        account = Mapping.objects.filter(
            source_type='CATEGORY',
            source__value=category,
            workspace_id=expense_group.workspace_id
        ).first()

        if category and not account:
            bulk_errors.append({
                'row': row,
                'expense_group_id': expense_group.id,
                'value': category,
                'type': 'Category Mapping',
                'message': 'Category Mapping not found'
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
                        'Updating Attachment failed for expense group id %s / workspace id %s \n Error: %s',
                        expense_group.id, expense_group.workspace_id, error
                    )

            task_log.detail = created_expense_report
            task_log.expense_report = expense_report_object
            task_log.status = 'COMPLETE'

            task_log.save(update_fields=['detail', 'expense_report', 'status'])

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
        logger.exception('Something unexpected happened workspace_id: %s\n%s', task_log.workspace_id, error)


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
                        'Updating Attachment failed for expense group id %s / workspace id %s \n Error: %s',
                        expense_group.id, expense_group.workspace_id, error
                    )

            task_log.detail = created_bill
            task_log.bill = bill_object
            task_log.status = 'COMPLETE'

            task_log.save(update_fields=['detail', 'bill', 'status'])

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
        logger.exception('Something unexpected happened workspace_id: %s\n%s', task_log.workspace_id, error)
