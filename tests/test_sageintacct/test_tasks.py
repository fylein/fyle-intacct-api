import logging
import random
from datetime import datetime, timedelta, timezone
from unittest import mock

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone as django_timezone
from django_q.models import Schedule
from fyle.platform.exceptions import InvalidTokenError as FyleInvalidTokenError
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from fyle_accounting_mappings.models import DestinationAttribute, EmployeeMapping, ExpenseAttribute
from sageintacctsdk.exceptions import InvalidTokenError, NoPrivilegeError, WrongParamsError

from apps.exceptions import ValueErrorWithResponse
from apps.fyle.models import Expense, ExpenseGroup, Reimbursement
from apps.mappings.models import GeneralMapping
from apps.sage_intacct.actions import update_last_export_details
from apps.sage_intacct.helpers import schedule_payment_sync
from apps.sage_intacct.models import (
    Bill,
    BillLineitem,
    ChargeCardTransaction,
    ExpenseReport,
    ExpenseReportLineitem,
    JournalEntry,
    SageIntacctReimbursement,
)
from apps.sage_intacct.queue import (
    handle_skipped_exports,
    schedule_bills_creation,
    schedule_charge_card_transaction_creation,
    schedule_expense_reports_creation,
    schedule_journal_entries_creation,
)
from apps.sage_intacct.tasks import (
    __validate_employee_mapping,
    __validate_expense_group,
    check_cache_and_search_vendors,
    check_sage_intacct_object_status,
    create_ap_payment,
    create_bill,
    create_charge_card_transaction,
    create_expense_report,
    create_journal_entry,
    create_or_update_employee_mapping,
    create_sage_intacct_reimbursement,
    get_employee_as_vendors_name,
    get_or_create_credit_card_vendor,
    handle_sage_intacct_errors,
    load_attachments,
    mark_paid_on_fyle,
    process_fyle_reimbursements,
    search_and_upsert_vendors,
    validate_for_skipping_payment,
)
from apps.sage_intacct.utils import SageIntacctConnector
from apps.tasks.models import Error, TaskLog
from apps.workspaces.models import Configuration, LastExportDetail, SageIntacctCredential
from fyle_intacct_api.exceptions import BulkError
from tests.test_sageintacct.fixtures import data

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def test_handle_intacct_errors(db):
    """
    Test handle_intacct_errors
    """
    task_log = TaskLog.objects.filter(workspace_id=1).first()

    expense_group = ExpenseGroup.objects.get(id=1)

    handle_sage_intacct_errors(
        exception=InvalidTokenError(
            msg='Some Parameters are wrong',
            response={
                'error': 'invalid_grant'
            }
        ),
        expense_group=expense_group,
        task_log=task_log,
        export_type='Bill'
    )
    assert task_log.sage_intacct_errors[0]['error'] == 'invalid_grant'

    handle_sage_intacct_errors(
        exception=InvalidTokenError(
            msg='Some Parameters are wrong',
            response={
                'error': {
                    'errorno': 'UJPP0002',
                    'description': 'Sign-in information is incorrect. Please check your request.'
                }
            }
        ),
        expense_group=expense_group,
        task_log=task_log,
        export_type='Bill'
    )

    assert task_log.sage_intacct_errors[0]['short_description'] == 'Sign-in information is incorrect. Please check your request.'
    assert task_log.status == 'FAILED'

    handle_sage_intacct_errors(
        exception=WrongParamsError(
            msg='Some Parameters are wrong',
            response={
                'error': {
                    'errorno': 'invalidRequest',
                    'description': 'Invalid Request'
                }
            }
        ),
        expense_group=expense_group,
        task_log=task_log,
        export_type='Bill'
    )

    assert task_log.sage_intacct_errors[0]['short_description'] == 'Invalid Request'
    assert task_log.status == 'FAILED'

    handle_sage_intacct_errors(
        exception=WrongParamsError(
            msg='Some Parameters are wrong',
            response={
                'error': [
                    {
                        'errorno': 'BL01001973',
                        'description': None,
                        'description2': "Invalid Project '10064' specified. [Support ID: nHh88EB032~Y1JFVP0J5xA-qTZWkbX7zwAAAAY]",
                        'correction': None
                    },
                    {
                        'errorno': 'BL01001973',
                        'description': None,
                        'description2': 'Could not create cctransaction record!',
                        'correction': None
                    },
                    {
                        'errorno': 'BL01001973',
                        'description': None,
                        'description2': "Currently, we can't create the transaction",
                        'correction': 'Check the transaction for errors or inconsistencies, then try again.'
                    }
                ]
            }
        ),
        expense_group=expense_group,
        task_log=task_log,
        export_type='Bill'
    )

    error = Error.objects.filter(workspace_id=1).first()

    assert error.error_detail == "Invalid Project '10064 => Direct Mail Campaign' specified."
    assert error.is_parsed == True
    assert error.attribute_type == 'PROJECT'
    assert error.article_link == settings.HELP_ARTICLE_DOMAIN + '/en/articles/9317068-project-related-sage-intacct-errors'

    assert len(task_log.sage_intacct_errors) == 3
    assert task_log.sage_intacct_errors[0]['short_description'] == 'Bill error'
    assert task_log.sage_intacct_errors[0]['long_description'] == 'Invalid Project \'10064\' specified. [Support ID: nHh88EB032~Y1JFVP0J5xA-qTZWkbX7zwAAAAY]'

    handle_sage_intacct_errors(
        exception=WrongParamsError(
            msg='Some Parameters are wrong',
            response={
                'blewblew': 'invalid_grant'
            }
        ),
        expense_group=expense_group,
        task_log=task_log,
        export_type='Bill'
    )

    assert 'error' not in task_log.sage_intacct_errors


def test_get_or_create_error_with_expense_group_create_new(db):
    """
    Test creating a new error record
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.get(id=1)

    expense_attribute = ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='EMPLOYEE',
        display_name='Employee',
        value='john.doe@fyle.in',
        source_id='test123'
    )

    error, created = Error.get_or_create_error_with_expense_group(
        expense_group,
        expense_attribute
    )

    assert created == True
    assert error.workspace_id == workspace_id
    assert error.type == 'EMPLOYEE_MAPPING'
    assert error.error_title == 'john.doe@fyle.in'
    assert error.error_detail == 'Employee mapping is missing'
    assert error.is_resolved == False
    assert error.mapping_error_expense_group_ids == [expense_group.id]


def test_get_or_create_error_with_expense_group_update_existing(db):
    """
    Test updating an existing error record with new expense group ID
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.get(id=1)

    expense_attribute = ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='EMPLOYEE',
        display_name='Employee',
        value='john.doe@fyle.in',
        source_id='test123'
    )

    # Create initial error
    error1, created1 = Error.get_or_create_error_with_expense_group(
        expense_group,
        expense_attribute
    )

    # Get another expense group
    expense_group2 = ExpenseGroup.objects.get(id=2)

    # Try to create error with same attribute but different expense group
    error2, created2 = Error.get_or_create_error_with_expense_group(
        expense_group2,
        expense_attribute
    )

    assert created2 == False
    assert error2.id == error1.id
    assert set(error2.mapping_error_expense_group_ids) == {expense_group.id, expense_group2.id}


def test_get_or_create_error_with_expense_group_category_mapping(db):
    """
    Test creating category mapping error
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.get(id=1)

    category_attribute = ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        display_name='Category',
        value='Travel Test',
        source_id='test456'
    )

    error, created = Error.get_or_create_error_with_expense_group(
        expense_group,
        category_attribute
    )

    assert created == True
    assert error.type == 'CATEGORY_MAPPING'
    assert error.error_title == 'Travel Test'
    assert error.error_detail == 'Category mapping is missing'
    assert error.mapping_error_expense_group_ids == [expense_group.id]


def test_get_or_create_error_with_expense_group_duplicate_expense_group(db):
    """
    Test that adding same expense group ID twice doesn't create duplicate
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.get(id=1)

    expense_attribute = ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='EMPLOYEE',
        display_name='Employee',
        value='john.doe@fyle.in',
        source_id='test123'
    )

    # Create initial error
    error1, _ = Error.get_or_create_error_with_expense_group(
        expense_group,
        expense_attribute
    )

    # Try to add same expense group again
    error2, created2 = Error.get_or_create_error_with_expense_group(
        expense_group,
        expense_attribute
    )

    assert created2 == False
    assert error2.id == error1.id
    assert len(error2.mapping_error_expense_group_ids) == 1
    assert error2.mapping_error_expense_group_ids == [expense_group.id]


def test_get_or_create_credit_card_vendor(mocker, db):
    """
    Test get_or_create_credit_card_vendor
    """
    workspace_id = 1
    mock_get_or_create_vendor = mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor'
    )

    vendor = DestinationAttribute.objects.create(
        value='Credit Card Misc',
        attribute_type='VENDOR',
        display_name='Vendor',
        workspace_id=workspace_id,
        active=True,
        detail={
            'email': 'vendor123@fyle.in'
        }
    )

    mock_get_or_create_vendor.return_value = vendor

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.auto_create_merchants_as_vendors = True
    configuration.save()

    contact = get_or_create_credit_card_vendor(workspace_id, configuration, 'samp_merchant')
    assert contact.value == 'Credit Card Misc'

    contact = get_or_create_credit_card_vendor(workspace_id, configuration, '')
    assert contact.value == 'Credit Card Misc'

    configuration.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    configuration.import_vendors_as_merchants = False
    configuration.save()

    vendor.value = 'samp_merchant'
    vendor.save()

    contact = get_or_create_credit_card_vendor(workspace_id, configuration, 'samp_merchant')
    assert contact.value == 'samp_merchant'

    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()

    vendor.value = 'samp_merchant_2'
    vendor.save()

    contact = get_or_create_credit_card_vendor(workspace_id, configuration, 'samp_merchant_2')
    assert contact.value == 'samp_merchant_2'

    try:
        with mock.patch('apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor') as mock_call:
            mock_call.side_effect = WrongParamsError(msg='wrong parameters', response='wrong parameters')
            contact = get_or_create_credit_card_vendor(workspace_id, configuration, 'samp_merchant')

            mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
            contact = get_or_create_credit_card_vendor(workspace_id, configuration, 'samp_merchant')
    except Exception:
        logger.info('wrong parameters')


def test_create_or_update_employee_mapping(mocker, db):
    """
    Test create_or_update_employee_mapping
    """
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor',
        return_value=DestinationAttribute.objects.get(value='Joanna')
    )
    mocker.patch(
        'sageintacctsdk.apis.Employees.get',
        return_value=[]
    )
    mocker.patch(
        'sageintacctsdk.apis.Employees.post',
        return_value={'data': {'employee': data['get_employee'][0]}}
    )
    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    expense_group = ExpenseGroup.objects.get(id=1)

    expense_group.description.update({'employee_email': 'user4@fyleforgotham.in'})
    expense_group.save()

    create_or_update_employee_mapping(expense_group=expense_group, sage_intacct_connection=sage_intacct_connection, auto_map_employees_preference='EMAIL', employee_field_mapping = 'EMPLOYEE')

    with mock.patch('fyle_accounting_mappings.models.DestinationAttribute.save') as mock_call:
        employee_mapping = EmployeeMapping.objects.get(source_employee__value='user4@fyleforgotham.in')
        employee_mapping.delete()

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': '6240', 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'errorno': 'BL34000061'}],
                'type': 'Invalid_params'
            })
        try:
            create_or_update_employee_mapping(expense_group=expense_group, sage_intacct_connection=sage_intacct_connection, auto_map_employees_preference='NAME', employee_field_mapping = 'VENDOR')
        except Exception:
            logger.info('Employee mapping not found')


def test_post_bill_success(mocker, create_task_logs, db):
    """
    Test post_bill success
    """
    mocker.patch(
        'sageintacctsdk.apis.Bills.post',
        return_value=data['bill_response']
    )
    mocker.patch(
        'sageintacctsdk.apis.Bills.get',
        return_value=data['bill_response']['data']
    )
    mocker.patch(
        'apps.sage_intacct.tasks.load_attachments',
        return_value=('sdfgh', False)
    )
    mocker.patch(
        'sageintacctsdk.apis.Bills.update_attachment',
        return_value=data['bill_response']
    )

    mocker.patch(
        'apps.sage_intacct.tasks.create_ap_payment',
    )

    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()

    expense_group.expenses.set(expenses)

    create_bill(expense_group.id, task_log.id, True, False)

    task_log = TaskLog.objects.get(pk=task_log.id)
    bill = Bill.objects.get(expense_group_id=expense_group.id)
    assert task_log.status == 'COMPLETE'
    assert bill.currency == 'USD'
    assert bill.vendor_id == 'Ashwin'
    assert task_log.is_attachment_upload_failed is False

    task_log.status = 'READY'
    task_log.supdoc_id = None
    task_log.save()

    mocker.patch('apps.sage_intacct.tasks.load_attachments', return_value=(None, True))
    create_bill(expense_group.id, task_log.id, True, False)

    task_log = TaskLog.objects.get(pk=task_log.id)
    assert task_log.is_attachment_upload_failed is True

    task_log.status = 'READY'
    task_log.save()

    with mock.patch('apps.sage_intacct.utils.SageIntacctConnector.update_bill') as mock_call:
        mock_call.side_effect = Exception()
        create_bill(expense_group.id, task_log.id, True, False)

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_bill(expense_group.id, task_log.id, True, False)


def test_create_bill_exceptions(mocker, db, create_task_logs):
    """
    Test create_bill exceptions
    """
    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.type = 'CREATING_BILL'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()

    expense_group.expenses.set(expenses)

    mocker.patch(
        'apps.sage_intacct.tasks.create_ap_payment',
    )

    with mock.patch('apps.sage_intacct.models.Bill.create_bill') as mock_call:
        mock_call.side_effect = SageIntacctCredential.DoesNotExist()
        create_bill(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_bill(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = Exception()
        create_bill(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FATAL'

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            }
        )
        create_bill(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            }
        )
        create_bill(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_bill(expense_group.id, task_log.id, True, False)


def test_post_sage_intacct_reimbursements_success(mocker, create_task_logs, db, create_expense_report):
    """
    Test post_sage_intacct_reimbursements success
    """
    mocker.patch(
        'sageintacctsdk.apis.Reimbursements.post',
        return_value=data['reimbursements']
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Reimbursements.sync',
        return_value=None
    )

    mocker.patch(
        'apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
    )

    mocker.patch('fyle_integrations_platform_connector.apis.Expenses.get', return_value=data['expense'])

    workspace_id = 1

    expense_report, expense_report_lineitems = create_expense_report

    task_log = TaskLog.objects.get(expense_group=expense_report.expense_group)
    task_log.status = 'READY'
    task_log.detail = {'key': 'sdfghjk'}
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()
        reimbursement = Reimbursement.objects.filter(settlement_id=expense.settlement_id).first()
        reimbursement.state = 'COMPLETE'
        reimbursement.save()

    expense_group.expenses.set(expenses)
    expense_group.save()

    create_sage_intacct_reimbursement(workspace_id)

    sage_intacct_reimbursement = SageIntacctReimbursement.objects.all().first()

    assert sage_intacct_reimbursement.account_id == '400_CHK'
    assert sage_intacct_reimbursement.employee_id == 'Joanna'


def test_post_sage_intacct_reimbursements_exceptions(mocker, db, create_expense_report):
    """
    Test post_sage_intacct_reimbursements exceptions
    """
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Reimbursements.sync',
        return_value=None
    )

    mocker.patch(
        'apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
    )

    mocker.patch('fyle_integrations_platform_connector.apis.Expenses.get', return_value=data['expense'])

    workspace_id = 1

    expense_report, expense_report_lineitems = create_expense_report

    task_log = TaskLog.objects.get(expense_group=expense_report.expense_group)
    task_log.status = 'READY'
    task_log.detail = {'key': 'sdfghjksamplekey'}
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    for expense in expenses:
        reimbursement = Reimbursement.objects.filter(settlement_id=expense.settlement_id).first()
        reimbursement.state = 'COMPLETE'
        reimbursement.save()

    with mock.patch('apps.workspaces.models.SageIntacctCredential.objects.get') as mock_call:
        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_sage_intacct_reimbursement(workspace_id)

        task_log = TaskLog.objects.get(task_id='PAYMENT_{}'.format(expense_report.expense_group.id))
        assert task_log.status == 'FAILED'

        now = datetime.now().replace(tzinfo=timezone.utc)
        updated_at = now - timedelta(days=10)

        mock_call.side_effect = Exception()
        TaskLog.objects.filter(task_id='PAYMENT_{}'.format(expense_report.expense_group.id)).update(updated_at=updated_at)
        create_sage_intacct_reimbursement(workspace_id)

        task_log = TaskLog.objects.get(task_id='PAYMENT_{}'.format(expense_report.expense_group.id))
        assert task_log.status == 'FATAL'

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            }
        )

        TaskLog.objects.filter(task_id='PAYMENT_{}'.format(expense_report.expense_group.id)).update(updated_at=updated_at)
        create_sage_intacct_reimbursement(workspace_id)

        task_log = TaskLog.objects.get(task_id='PAYMENT_{}'.format(expense_report.expense_group.id))
        assert task_log.status == 'FAILED'

        TaskLog.objects.filter(task_id='PAYMENT_{}'.format(expense_report.expense_group.id)).update(updated_at=updated_at)
        mock_call.side_effect = SageIntacctCredential.DoesNotExist()
        create_sage_intacct_reimbursement(workspace_id)

        task_log = TaskLog.objects.get(task_id='PAYMENT_{}'.format(expense_report.expense_group.id))
        assert task_log.status == 'FAILED'

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_sage_intacct_reimbursement(workspace_id)

    with mock.patch('apps.sage_intacct.utils.SageIntacctConnector.post_sage_intacct_reimbursement') as mock_call:
        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            }
        )

        TaskLog.objects.filter(task_id='PAYMENT_{}'.format(expense_report.expense_group.id)).update(updated_at=updated_at)
        create_sage_intacct_reimbursement(workspace_id)

        task_log = TaskLog.objects.get(task_id='PAYMENT_{}'.format(expense_report.expense_group.id))
        assert task_log.status == 'FAILED'

    SageIntacctCredential.objects.filter(workspace_id=workspace_id).update(is_expired=False)

    with mock.patch('apps.sage_intacct.models.SageIntacctReimbursement.create_sage_intacct_reimbursement') as mock_call:
        expense_report.expense_group.expenses.all().update(paid_on_fyle=True)
        assert expense_report.paid_on_sage_intacct == False
        assert expense_report.payment_synced == False
        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': "exceeds total amount due ()", 'correction': ''}],
                'type': 'Invalid_params'
            }
        )

        now = datetime.now().replace(tzinfo=timezone.utc)
        updated_at = now - timedelta(days=10)
        TaskLog.objects.filter(task_id='PAYMENT_{}'.format(expense_report.expense_group.id)).update(updated_at=updated_at)
        create_sage_intacct_reimbursement(workspace_id)
        expense_report = ExpenseReport.objects.get(id=expense_report.id)

        assert expense_report.paid_on_sage_intacct == True
        assert expense_report.payment_synced == True


def test_create_sage_intacct_reimbursement_invalid_token(mocker, db):
    """
    Test create_sage_intacct_reimbursement invalid token
    """
    workspace_id = 1
    with mock.patch('fyle_integrations_platform_connector.fyle_integrations_platform_connector.PlatformConnector.__init__') as mock_init:
        mock_init.side_effect = FyleInvalidTokenError('Invalid refresh token')
        create_sage_intacct_reimbursement(workspace_id)


def test_post_charge_card_transaction_success(mocker, create_task_logs, db):
    """
    Test post_charge_card_transaction success
    """
    mocker.patch(
        'sageintacctsdk.apis.ChargeCardTransactions.post',
        return_value=data['credit_card_response']
    )
    mocker.patch(
        'sageintacctsdk.apis.ChargeCardTransactions.update_attachment',
        return_value=data['credit_card_response']
    )
    mocker.patch(
        'sageintacctsdk.apis.ChargeCardTransactions.get',
        return_value=data['credit_card_response']['data']
    )
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor',
        return_value=DestinationAttribute.objects.get(id=633)
    )
    mocker.patch(
        'apps.sage_intacct.tasks.load_attachments',
        return_value=('sdfgh', False)
    )
    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=2)
    expense_group.description.update({'employee_email': 'user4444@fyleforgotham.in'})
    expense_group.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_charge_card_id = 'sample'
    general_mappings.save()

    create_charge_card_transaction(expense_group.id, task_log.id, True, False)

    task_log = TaskLog.objects.get(pk=task_log.id)
    charge_card_transaction = ChargeCardTransaction.objects.get(expense_group_id=expense_group.id)

    assert task_log.status == 'COMPLETE'
    assert charge_card_transaction.currency == 'USD'
    assert task_log.is_attachment_upload_failed is False

    task_log.status = 'READY'
    task_log.supdoc_id = None
    task_log.save()

    mocker.patch('apps.sage_intacct.tasks.load_attachments', return_value=(None, True))
    create_charge_card_transaction(expense_group.id, task_log.id, True, False)

    task_log = TaskLog.objects.get(pk=task_log.id)
    assert task_log.is_attachment_upload_failed is True

    task_log.status = 'READY'
    task_log.save()

    with mock.patch('sageintacctsdk.apis.ChargeCardTransactions.update_attachment') as mock_call:
        mock_call.side_effect = Exception()
        create_charge_card_transaction(expense_group.id, task_log.id, True, False)

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_charge_card_transaction(expense_group.id, task_log.id, True, False)


def test_post_credit_card_exceptions(mocker, create_task_logs, db):
    """
    Test post_credit_card_transaction exceptions
    """
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor',
        return_value=DestinationAttribute.objects.get(id=633)
    )
    mocker.patch(
        'apps.workspaces.models.SageIntacctCredential.get_active_sage_intacct_credentials',
        return_value=SageIntacctCredential.objects.get(id=1)
    )

    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=2)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()

    expense_group.expenses.set(expenses)

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION'
    configuration.save()

    with mock.patch('apps.sage_intacct.models.ChargeCardTransaction.create_charge_card_transaction') as mock_call:
        mock_call.side_effect = SageIntacctCredential.DoesNotExist()
        create_charge_card_transaction(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_charge_card_transaction(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = Exception()
        create_charge_card_transaction(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FATAL'

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            }
        )

        create_charge_card_transaction(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            }
        )

        create_charge_card_transaction(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_charge_card_transaction(expense_group.id, task_log.id, True, False)

        mock_call.side_effect = ValueErrorWithResponse(message='Something Went Wrong', response='Credit Card Misc vendor not found')
        create_charge_card_transaction(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        error = Error.objects.filter(expense_group=expense_group).first()
        brand_name = 'Fyle' if settings.BRAND_ID == 'fyle' else 'Expense Management'
        assert error.error_detail == '''Merchant from expense not found as a vendor in Sage Intacct. {0} couldn't auto-create the default vendor "Credit Card Misc". Please manually create this vendor in Sage Intacct, then retry.'''.format(brand_name)
        assert error.error_title == 'Vendor creation failed in Sage Intacct'


def test_post_journal_entry_success(mocker, create_task_logs, db):
    """
    Test post_journal_entry success
    """
    mocker.patch(
        'sageintacctsdk.apis.JournalEntries.post',
        return_value=data['journal_entry_response']
    )
    mocker.patch(
        'sageintacctsdk.apis.JournalEntries.update',
        return_value=data['journal_entry_response']
    )
    mocker.patch(
        'sageintacctsdk.apis.JournalEntries.get',
        return_value=data['journal_entry_response']['data']
    )
    mocker.patch(
        'apps.sage_intacct.tasks.load_attachments',
        return_value=('sdfgh', False)
    )
    mocker.patch(
        'apps.sage_intacct.tasks.get_journal_entry_record_number',
        return_value='6679'

    )

    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=3)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()

    expense_group.expenses.set(expenses)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.currency = 'GBP'
        expense.save()

    expense_group.expenses.set(expenses)
    expense_group.save()

    create_journal_entry(expense_group.id, task_log.id, True, False)

    task_log = TaskLog.objects.get(id=task_log.id)
    journal_entry = JournalEntry.objects.get(expense_group_id=expense_group.id)

    assert task_log.status == 'COMPLETE'
    assert journal_entry.currency == 'GBP'
    assert task_log.is_attachment_upload_failed is False

    task_log.status = 'READY'
    task_log.supdoc_id = None
    task_log.save()

    mocker.patch('apps.sage_intacct.tasks.load_attachments', return_value=(None, True))
    create_journal_entry(expense_group.id, task_log.id, True, False)

    task_log = TaskLog.objects.get(id=task_log.id)
    assert task_log.is_attachment_upload_failed is True

    task_log.status = 'READY'
    task_log.save()

    with mock.patch('sageintacctsdk.apis.JournalEntries.update') as mock_call:
        mock_call.side_effect = Exception()
        create_journal_entry(expense_group.id, task_log.id, True, False)

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_journal_entry(expense_group.id, task_log.id, True, False)


def test_post_create_journal_entry_exceptions(mocker, create_task_logs, db):
    """
    Test post_create_journal_entry exceptions
    """
    mocker.patch(
        'apps.workspaces.models.SageIntacctCredential.get_active_sage_intacct_credentials',
        return_value=SageIntacctCredential.objects.get(id=1)
    )
    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=3)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()

    expense_group.expenses.set(expenses)
    expense_group.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.corporate_credit_card_expenses_object == 'JOURNAL_ENTRY'
    configuration.save()

    with mock.patch('apps.sage_intacct.models.JournalEntry.create_journal_entry') as mock_call:
        mock_call.side_effect = SageIntacctCredential.DoesNotExist()
        create_journal_entry(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_journal_entry(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = Exception()
        create_journal_entry(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FATAL'

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            }
        )

        create_journal_entry(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': {'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''},
                'type': 'Invalid_params'
            }
        )

        create_journal_entry(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = NoPrivilegeError(msg='Insufficient Permission', response="Insufficient Permission")
        create_journal_entry(expense_group.id, task_log.id, True, False)

        mock_call.side_effect = ValueErrorWithResponse(message='Something Went Wrong', response='Credit Card Misc vendor not found')
        create_journal_entry(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        error = Error.objects.filter(expense_group=expense_group).first()
        brand_name = 'Fyle' if settings.BRAND_ID == 'fyle' else 'Expense Management'
        assert error.error_detail == '''Merchant from expense not found as a vendor in Sage Intacct. {0} couldn't auto-create the default vendor "Credit Card Misc". Please manually create this vendor in Sage Intacct, then retry.'''.format(brand_name)
        assert error.error_title == 'Vendor creation failed in Sage Intacct'


def test_post_expense_report_success(mocker, create_task_logs, db):
    """
    Test post_expense_report success
    """
    mocker.patch(
        'sageintacctsdk.apis.ExpenseReports.post',
        return_value=data['expense_report_post_response']
    )
    mocker.patch(
        'sageintacctsdk.apis.ExpenseReports.update_attachment',
        return_value=data['expense_report_response']
    )
    mocker.patch(
        'sageintacctsdk.apis.ExpenseReports.get',
        return_value=data['expense_report_response']['data']
    )
    mocker.patch(
        'apps.sage_intacct.tasks.load_attachments',
        return_value=('sdfgh', False)
    )

    mocker.patch(
        'apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
    )

    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    create_expense_report(expense_group.id, task_log.id, True, False)

    task_log = TaskLog.objects.get(id=task_log.id)
    expense_report = ExpenseReport.objects.get(expense_group_id=expense_group.id)

    assert task_log.status == 'COMPLETE'
    assert expense_report.currency == 'USD'
    assert task_log.is_attachment_upload_failed is False

    task_log.status = 'READY'
    task_log.supdoc_id = None
    task_log.save()

    mocker.patch('apps.sage_intacct.tasks.load_attachments', return_value=(None, True))
    create_expense_report(expense_group.id, task_log.id, True, False)

    task_log = TaskLog.objects.get(id=task_log.id)
    assert task_log.is_attachment_upload_failed is True

    task_log.status = 'READY'
    task_log.save()

    with mock.patch('sageintacctsdk.apis.ExpenseReports.update_attachment') as mock_call:
        mock_call.side_effect = Exception()
        create_expense_report(expense_group.id, task_log.id, True, False)

        mock_call.side_effect = NoPrivilegeError(msg='Insufficient Permission', response="Insufficient Permission")
        create_expense_report(expense_group.id, task_log.id, True, False)


def test_post_create_expense_report_exceptions(mocker, create_task_logs, db):
    """
    Test post_create_expense_report exceptions
    """
    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=3)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()

    expense_group.expenses.set(expenses)
    expense_group.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT'
    configuration.save()

    mocker.patch(
        'apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
    )
    mocker.patch('apps.sage_intacct.models.import_string', return_value=lambda *args, **kwargs: None)

    with mock.patch('apps.sage_intacct.utils.SageIntacctConnector.post_expense_report') as mock_call:
        mock_call.side_effect = SageIntacctCredential.DoesNotExist()
        create_expense_report(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_expense_report(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = Exception()
        create_expense_report(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FATAL'

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            }
        )

        create_expense_report(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            }
        )

        create_expense_report(expense_group.id, task_log.id, True, False)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = NoPrivilegeError(msg='Insufficient Permission', response="Insufficient Permission")
        create_expense_report(expense_group.id, task_log.id, True, False)


def test_create_ap_payment(mocker, db):
    """
    Test create_ap_payment
    """
    mocker.patch(
        'sageintacctsdk.apis.Bills.post',
        return_value=data['bill_response']
    )
    mocker.patch(
        'sageintacctsdk.apis.Bills.get',
        return_value=data['bill_response']['data']
    )
    mocker.patch(
        'sageintacctsdk.apis.APPayments.post',
        return_value=data['reimbursements']
    )
    mocker.patch(
        'apps.sage_intacct.tasks.load_attachments',
        return_value=('sdfgh', False)
    )
    mocker.patch(
        'sageintacctsdk.apis.Reimbursements.post',
        return_value=data['reimbursements']
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Reimbursements.sync',
        return_value=None
    )
    mocker.patch(
        'sageintacctsdk.apis.Bills.update_attachment',
        return_value=data['bill_response']
    )

    mocker.patch('fyle_integrations_platform_connector.apis.Expenses.get', return_value=[])

    workspace_id = 1
    task_log = TaskLog.objects.filter(expense_group__workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    for expense in expenses:
        reimbursement = Reimbursement.objects.filter(settlement_id=expense.settlement_id).first()
        reimbursement.state = 'COMPLETE'
        reimbursement.save()

    create_bill(expense_group.id, task_log.id, True, False)

    bill = Bill.objects.get(expense_group__workspace_id=workspace_id)

    task_log = TaskLog.objects.get(expense_group=bill.expense_group)
    task_log.detail = data['bill_response']
    task_log.save()

    create_ap_payment(workspace_id)
    assert task_log.status == 'COMPLETE'


def test_create_ap_payment_exceptions(mocker, db):
    """
    Test create_ap_payment exceptions
    """
    # Mock necessary functions and classes
    mocker.patch('sageintacctsdk.apis.Bills.post', return_value=data['bill_response'])
    mocker.patch('sageintacctsdk.apis.Bills.get', return_value=data['bill_response']['data'])
    mocker.patch('sageintacctsdk.apis.APPayments.post', return_value=data['reimbursements'])
    mocker.patch('apps.sage_intacct.tasks.load_attachments', return_value=('sdfgh', False))
    mocker.patch('sageintacctsdk.apis.Reimbursements.post', return_value=data['reimbursements'])
    mocker.patch('fyle_integrations_platform_connector.apis.Reimbursements.sync', return_value=None)
    mocker.patch('sageintacctsdk.apis.Bills.update_attachment', return_value=data['bill_response'])
    mocker.patch('fyle_integrations_platform_connector.apis.Expenses.get', return_value=[])

    workspace_id = 1
    expense_group = ExpenseGroup.objects.get(id=1)
    task_log = TaskLog.objects.filter(expense_group__workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    create_bill(expense_group.id, task_log.id, True, False)

    bill = Bill.objects.get(expense_group__workspace_id=workspace_id)
    bill.payment_synced = False
    bill.save()

    for expense in bill.expense_group.expenses.all():
        expense.paid_on_fyle = True
        expense.save()

    # Mock exceptions to be raised during the `create_ap_payment` call
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_ap_payment', side_effect=SageIntacctCredential.DoesNotExist)
    # Test SageIntacctCredential.DoesNotExist
    create_ap_payment(workspace_id)
    task_log = TaskLog.objects.filter(
        workspace_id=workspace_id,
        task_id='PAYMENT_{}'.format(bill.expense_group.id)
    ).first()

    assert task_log.status == 'FAILED'
    assert 'Sage-Intacct Account not connected' in task_log.detail['message']

    # Test BulkError
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_ap_payment', side_effect=BulkError(msg="Bulk error", response="Bulk error occurred"))
    create_ap_payment(workspace_id)
    task_log = TaskLog.objects.filter(
        workspace_id=workspace_id,
        task_id='PAYMENT_{}'.format(bill.expense_group.id)
    ).first()

    assert task_log.status == 'FAILED'

    # Test WrongParamsError
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_ap_payment', side_effect=WrongParamsError(msg="Invalid Parameters", response="Invalid parameters"))
    create_ap_payment(workspace_id)
    task_log.refresh_from_db()
    assert task_log.status == 'FAILED'

    # Test InvalidTokenError
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_ap_payment', side_effect=InvalidTokenError(msg="Invalid token", response="Invalid token"))
    create_ap_payment(workspace_id)
    task_log.refresh_from_db()
    assert task_log.status == 'FAILED'

    # Test NoPrivilegeError
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_ap_payment', side_effect=NoPrivilegeError(msg="No privilege", response="No privilege"))
    create_ap_payment(workspace_id)
    task_log.refresh_from_db()
    assert task_log.status == 'FAILED'


def test_validate_for_skipping_payment(mocker, db):
    """
    Test validate_for_skipping_payment
    """
    mock_task_log = mocker.Mock(spec=TaskLog)
    mock_task_log.created_at = datetime.now().replace(tzinfo=timezone.utc) - relativedelta(months=3)
    mock_task_log.updated_at = datetime.now().replace(tzinfo=timezone.utc) - relativedelta(months=3)

    mock_queryset = mocker.Mock()
    mock_queryset.first.return_value = mock_task_log

    mocker.patch('apps.tasks.models.TaskLog.objects.filter', return_value=mock_queryset)

    mock_export_module = mocker.Mock(spec=Bill)
    mock_export_module.expense_group.id = 1

    result = validate_for_skipping_payment(mock_export_module, workspace_id=1, type='BILL')
    assert result is True


def test_post_ap_payment_exceptions(mocker, db):
    """
    Test post_ap_payment exceptions
    """
    mocker.patch(
        'sageintacctsdk.apis.Bills.post',
        return_value=data['bill_response']
    )
    mocker.patch(
        'sageintacctsdk.apis.Bills.get',
        return_value=data['bill_response']['data']
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Reimbursements.sync',
        return_value=None
    )

    mocker.patch('fyle_integrations_platform_connector.apis.Expenses.get', return_value=[])

    workspace_id = 1
    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()
        reimbursement = Reimbursement.objects.filter(settlement_id=expense.settlement_id).first()
        reimbursement.state = 'COMPLETE'
        reimbursement.save()

    expense_group.expenses.set(expenses)
    expense_group.save()

    create_bill(expense_group.id, task_log.id, True, False)

    bill = Bill.objects.last()
    task_log = TaskLog.objects.get(id=task_log.id)
    task_log.expense_group = bill.expense_group
    task_log.save()

    with mock.patch('apps.sage_intacct.models.APPayment.create_ap_payment') as mock_call:
        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_ap_payment(workspace_id)

        mock_call.side_effect = Exception()
        create_ap_payment(workspace_id)

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            }
        )

        create_ap_payment(workspace_id)

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': {'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''},
                'type': 'Invalid_params'
            }
        )
        create_ap_payment(workspace_id)

        mock_call.side_effect = NoPrivilegeError(msg="insufficient permission", response="insufficient permission")
        create_ap_payment(workspace_id)

        try:
            mock_call.side_effect = SageIntacctCredential.DoesNotExist()
            create_ap_payment(workspace_id)
        except Exception:
            logger.info('Intacct credentials not found')

    with mock.patch('apps.sage_intacct.models.APPayment.create_ap_payment') as mock_call:
        bill.expense_group.expenses.all().update(paid_on_fyle=True)
        assert bill.paid_on_sage_intacct == False
        assert bill.payment_synced == False
        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': "Oops, we can't find this transaction; enter a valid", 'correction': ''}],
                'type': 'Invalid_params'
            }
        )
        create_ap_payment(workspace_id)
        bill = Bill.objects.get(id=bill.id)

        assert bill.paid_on_sage_intacct == True
        assert bill.payment_synced == True


def test_schedule_ap_payment_creation(db):
    """
    Test schedule_ap_payment_creation
    """
    workspace_id = 1
    workspace_configuration = Configuration.objects.get(workspace_id=workspace_id)

    schedule_payment_sync(configuration=workspace_configuration)
    schedule = Schedule.objects.filter(func='apps.sage_intacct.queue.trigger_sync_payments').count()

    assert schedule == 1


def test_check_sage_intacct_object_status(mocker, db):
    """
    Test check_sage_intacct_object_status
    """
    mocker.patch(
        'sageintacctsdk.apis.Bills.get_by_query',
        return_value=data['get_by_query']
    )
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_expense_reports',
        return_value=data['expense_report_get_bulk']
    )
    workspace_id = 1
    expense_group = ExpenseGroup.objects.get(id=1)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    bill = Bill.create_bill(expense_group)
    _ = BillLineitem.create_bill_lineitems(expense_group, workspace_general_settings)

    task_log = TaskLog.objects.filter(expense_group_id=expense_group.id).first()
    task_log.expense_group = bill.expense_group
    task_log.detail = data['bill_response']
    task_log.bill = bill
    task_log.status = 'COMPLETE'
    task_log.save()

    check_sage_intacct_object_status(workspace_id)
    bills = Bill.objects.filter(expense_group__workspace_id=workspace_id)

    for bill in bills:
        assert bill.paid_on_sage_intacct == True
        assert bill.payment_synced == True

    expense_report = ExpenseReport.create_expense_report(expense_group)
    _ = ExpenseReportLineitem.create_expense_report_lineitems(expense_group, workspace_general_settings)

    task_log = TaskLog.objects.filter(expense_group_id=expense_group.id).first()
    task_log.expense_group = expense_report.expense_group
    task_log.detail = {'key': '3032'}
    task_log.expense_report = expense_report
    task_log.status = 'COMPLETE'
    task_log.save()

    check_sage_intacct_object_status(workspace_id)
    expense_reports = ExpenseReport.objects.filter(expense_group__workspace_id=workspace_id)

    for expense_report in expense_reports:
        assert expense_report.paid_on_sage_intacct == True
        assert expense_report.payment_synced == True

    with mock.patch('apps.sage_intacct.utils.SageIntacctConnector.get_expense_reports') as mock_call:
        mock_call.side_effect = NoPrivilegeError(msg="insufficient permission", response="insufficient permission")
        check_sage_intacct_object_status(workspace_id)

    with mock.patch('apps.sage_intacct.utils.SageIntacctConnector.__init__') as mock_init:
        mock_init.side_effect = WrongParamsError(msg="Some of the parameters are wrong", response="wrong params")
        check_sage_intacct_object_status(workspace_id)


def test_process_fyle_reimbursements(db, mocker):
    """
    Test process_fyle_reimbursements
    """
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Reports.bulk_mark_as_paid',
        return_value=[]
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Reimbursements.sync',
        return_value=[],
    )
    workspace_id = 1

    expenses = Expense.objects.filter(fund_source='PERSONAL')
    for expense in expenses:
        expense.paid_on_sage_intacct = True
        expense.save()

    reimbursement = Reimbursement.objects.filter(workspace_id=workspace_id).first()
    reimbursement.state = 'PENDING'
    reimbursement.save()

    process_fyle_reimbursements(workspace_id)

    reimbursement = Reimbursement.objects.filter(workspace_id=workspace_id).count()

    assert reimbursement == 258

    with mock.patch('fyle_integrations_platform_connector.fyle_integrations_platform_connector.PlatformConnector.__init__') as mock_init:
        mock_init.side_effect = FyleInvalidTokenError('Invalid refresh token')
        process_fyle_reimbursements(workspace_id)


def test_schedule_sage_intacct_objects_status_sync(db):
    """
    Test schedule_sage_intacct_objects_status_sync
    """
    workspace_id = 1
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    schedule_payment_sync(configuration=configuration)

    schedule_count = Schedule.objects.filter(func='apps.sage_intacct.queue.trigger_sync_payments', args=workspace_id).count()
    assert schedule_count == 1


def test_schedule_journal_entries_creation(mocker, db):
    """
    Test schedule_journal_entries_creation
    """
    workspace_id = 1

    schedule_journal_entries_creation(workspace_id, [1], False, 1, triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC, run_in_rabbitmq_worker=False)

    TaskLog.objects.filter(type='CREATING_JOURNAL_ENTRIES').count() != 0


def test_schedule_expense_reports_creation(mocker, db):
    """
    Test schedule_expense_reports_creation
    """
    workspace_id = 1

    schedule_expense_reports_creation(workspace_id, [1], False, 1, triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC, run_in_rabbitmq_worker=False)

    TaskLog.objects.filter(type='CREATING_EXPENSE_REPORTS').count() != 0


def test_schedule_bills_creation(mocker, db):
    """
    Test schedule_bills_creation
    """
    workspace_id = 1

    schedule_bills_creation(workspace_id, [1], False, 1, triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC, run_in_rabbitmq_worker=False)

    TaskLog.objects.filter(type='CREATING_BILLS').count() != 0


def test_schedule_charge_card_transaction_creation(mocker, db):
    """
    Test schedule_charge_card_transaction_creation
    """
    workspace_id = 1

    schedule_charge_card_transaction_creation(workspace_id, [2], False, 1, triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC, run_in_rabbitmq_worker=False)

    TaskLog.objects.filter(type='CREATING_CHARGE_CARD_TRANSACTIONS').count() != 0


def test_schedule_sage_intacct_reimbursement_creation(mocker, db):
    """
    Test schedule_sage_intacct_reimbursement_creation
    """
    workspace_id = 1
    workspace_configuration = Configuration.objects.get(workspace_id=workspace_id)
    workspace_configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    schedule_payment_sync(configuration=workspace_configuration)

    schedule_count = Schedule.objects.filter(func='apps.sage_intacct.queue.trigger_sync_payments', args=workspace_id).count()
    assert schedule_count == 1


def test_schedule_creation_with_no_expense_groups(db):
    """
    Test schedule_creation_with_no_expense_groups
    """
    workspace_id = 1

    expense_group_1 = ExpenseGroup.objects.get(id=1)
    expense_group_1.exported_at = django_timezone.now()
    expense_group_1.save()

    expense_group_2 = ExpenseGroup.objects.get(id=2)
    expense_group_2.exported_at = django_timezone.now()
    expense_group_2.save()

    initial_task_log_count = TaskLog.objects.filter(workspace_id=workspace_id).count()

    schedule_journal_entries_creation(workspace_id, [1], False, 1, triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC, run_in_rabbitmq_worker=False)
    assert TaskLog.objects.filter(workspace_id=workspace_id).count() == initial_task_log_count

    schedule_expense_reports_creation(workspace_id, [1], False, 1, triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC, run_in_rabbitmq_worker=False)
    assert TaskLog.objects.filter(workspace_id=workspace_id).count() == initial_task_log_count

    schedule_bills_creation(workspace_id, [1], False, 1, triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC, run_in_rabbitmq_worker=False)
    assert TaskLog.objects.filter(workspace_id=workspace_id).count() == initial_task_log_count

    schedule_charge_card_transaction_creation(workspace_id, [2], False, 1, triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC, run_in_rabbitmq_worker=False)
    assert TaskLog.objects.filter(workspace_id=workspace_id).count() == initial_task_log_count


def test__validate_expense_group(mocker, db):
    """
    Test __validate_expense_group
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    expense_group.description.update({'employee_email': 'user4@fyleforgotham.in'})
    expense_group.save()

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.employee_field_mapping = 'EMPLOYEE'
    configuration.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    configuration.save()

    general_mapping = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mapping.default_charge_card_id = None
    general_mapping.default_ccc_vendor_id = None
    general_mapping.default_tax_code_id = None
    general_mapping.default_tax_code_name = None
    general_mapping.save()

    try:
        __validate_expense_group(expense_group, configuration)
    except Exception:
        logger.info('Mappings are missing')

    configuration.corporate_credit_card_expenses_object = 'BILL'
    configuration.save()

    try:
        __validate_expense_group(expense_group, configuration)
    except Exception:
        logger.info('Mappings are missing')

    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()
    expense_group.description.update({'employee_email': 'ashwin.t@fyle.in'})
    expense_group.save()

    try:
        __validate_expense_group(expense_group, configuration)
    except Exception:
        logger.info('Mappings are missing')

    configuration.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    try:
        __validate_expense_group(expense_group, configuration)
    except Exception:
        logger.info('Mappings are missing')

    configuration.employee_field_mapping = 'VENDOR'
    configuration.save()

    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()

    general_mapping.default_credit_card_id = None
    general_mapping.save()

    try:
        __validate_expense_group(expense_group, configuration)
    except BulkError as exception:
        logger.info(exception.response)

    expense_group = ExpenseGroup.objects.get(id=1)

    expense_group.description.update({'employee_email': 'user48888@fyleforgotham.in'})
    expense_group.save()

    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.employee_field_mapping = 'EMPLOYEE'
    configuration.save()

    try:
        __validate_expense_group(expense_group, configuration)
    except BulkError as exception:
        logger.info(exception.response)

    general_mapping.delete()
    try:
        __validate_expense_group(expense_group, configuration)
    except BulkError as exception:
        logger.info(exception.response)


def test_load_attachments(mocker, db):
    """
    Test load_attachments
    """
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Files.bulk_generate_file_urls',
        return_value=[{'id': 'file123', 'name': 'test.pdf', 'download_url': 'https://example.com/file.pdf'}]
    )
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.post_attachments',
        return_value='2'
    )

    workspace_id = 1

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    expense_group = ExpenseGroup.objects.get(id=2)
    expenses = expense_group.expenses.all()

    for expense in expenses:
        expense.file_ids = ['sdfghjkl']
        expense.save()

    expense_group.expenses.set(expenses)
    expense_group.save()

    supdoc_id, is_failed = load_attachments(sage_intacct_connection, expense_group)
    assert supdoc_id == '2'
    assert is_failed is False

    with mock.patch('fyle_integrations_platform_connector.apis.Files.bulk_generate_file_urls') as mock_call:
        mock_call.side_effect = Exception()
        supdoc_id, is_failed = load_attachments(sage_intacct_connection, expense_group)
        assert supdoc_id is None
        assert is_failed is True


def test_update_last_export_details(mocker, db):
    """
    Test update_last_export_details
    """
    workspace_id = 1
    last_export_detail = update_last_export_details(workspace_id)
    assert last_export_detail.export_mode == 'MANUAL'

    # `update_last_export_details` when called with failed task logs
    # should call patch_integration_settings to update the `errors_count`

    mocked_patch_integration_settings = mocker.patch('apps.workspaces.tasks.patch_integration_settings')

    LastExportDetail.objects.update(
        workspace_id=workspace_id,
        last_exported_at=datetime.now(tz=timezone.utc)
    )

    TaskLog.objects.all().delete()

    mock_task_logs = data['task_logs']
    for task_log in mock_task_logs:
        TaskLog.objects.create(workspace_id=workspace_id, type=task_log['type'], status=task_log['status'])

    update_last_export_details(workspace_id)

    failed_count = len([i for i in mock_task_logs if i['status'] in ('FAILED', 'FATAL')])

    # Verify patch_integration_settings was called with the correct arguments
    mocked_patch_integration_settings.assert_called_once_with(workspace_id, errors=failed_count)


def test__validate_employee_mapping(mocker, db):
    """
    Test __validate_employee_mapping
    """
    workspace_id = 1

    # Set up the expense group with necessary details
    expense_group = ExpenseGroup.objects.get(id=2)
    expense_group.description.update({'employee_email': 'user4@fyleforgotham.in'})
    expense_group.save()

    # Set up the configuration
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.reimbursable_expenses_object = 'JOURNAL_ENTRY'
    configuration.use_merchant_in_journal_line = False
    configuration.employee_field_mapping = 'EMPLOYEE'
    configuration.save()

    # Mock the settings
    mocker.patch('django.conf.settings.BRAND_ID', 'fyle')

    # Case: EmployeeMapping does not exist
    mocker.patch('apps.sage_intacct.tasks.EmployeeMapping.objects.get', side_effect=EmployeeMapping.DoesNotExist)
    try:
        __validate_employee_mapping(expense_group, configuration)
    except BulkError:
        logger.info('Employee mapping not found')

    # Case: EmployeeMapping exists, but entity is None
    employee_mapping = mocker.patch('fyle_accounting_mappings.models.EmployeeMapping.objects.get').return_value
    employee_mapping.destination_employee = None
    employee_mapping.destination_vendor = None

    mocker.patch('fyle_accounting_mappings.models.EmployeeMapping.objects.get', side_effect=employee_mapping)

    mocker.patch('fyle_accounting_mappings.models.EmployeeMapping.DoesNotExist', side_effect=EmployeeMapping.DoesNotExist)

    try:
        __validate_employee_mapping(expense_group, configuration)
    except BulkError as exception:
        logger.info(exception.response)

    # Case: Corporate Credit Card and configuration.use_merchant_in_journal_line is True
    configuration.use_merchant_in_journal_line = True
    configuration.save()

    mocker.patch('fyle_accounting_mappings.models.EmployeeMapping.objects.get', side_effect=employee_mapping)

    mocker.patch('fyle_accounting_mappings.models.EmployeeMapping.DoesNotExist', side_effect=EmployeeMapping.DoesNotExist)

    try:
        __validate_employee_mapping(expense_group, configuration)
    except BulkError as exception:
        logger.info(exception.response)

    # Case: Fund source is PERSONAL
    expense_group.fund_source = 'PERSONAL'
    expense_group.save()

    mocker.patch('fyle_accounting_mappings.models.EmployeeMapping.objects.get', side_effect=employee_mapping)

    try:
        __validate_employee_mapping(expense_group, configuration)
    except BulkError as exception:
        logger.info(exception.response)

    # Case: Fund source is CCC and corporate_credit_card_expenses_object is EXPENSE_REPORT
    expense_group.fund_source = 'CCC'
    configuration.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    expense_group.save()
    configuration.save()

    mocker.patch('fyle_accounting_mappings.models.EmployeeMapping.objects.get', side_effect=employee_mapping)

    try:
        __validate_employee_mapping(expense_group, configuration)
    except BulkError as exception:
        logger.info(exception.response)


def test_skipping_create_ap_payment(mocker, db):
    """
    Test skipping create_ap_payment
    """
    mocker.patch(
        'sageintacctsdk.apis.Bills.post',
        return_value=data['bill_response']
    )
    mocker.patch(
        'sageintacctsdk.apis.Bills.get',
        return_value=data['bill_response']['data']
    )
    mocker.patch(
        'sageintacctsdk.apis.APPayments.post',
        return_value=data['reimbursements']
    )
    mocker.patch(
        'apps.sage_intacct.tasks.load_attachments',
        return_value=('sdfgh', False)
    )
    mocker.patch(
        'sageintacctsdk.apis.Reimbursements.post',
        return_value=data['reimbursements']
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Reimbursements.sync',
        return_value=None
    )
    mocker.patch(
        'sageintacctsdk.apis.Bills.update_attachment',
        return_value=data['bill_response']
    )

    mocker.patch('fyle_integrations_platform_connector.apis.Expenses.get', return_value=[])

    workspace_id = 1
    task_log = TaskLog.objects.filter(expense_group__workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    for expense in expenses:
        reimbursement = Reimbursement.objects.filter(settlement_id=expense.settlement_id).first()
        reimbursement.state = 'COMPLETE'
        reimbursement.save()

    create_bill(expense_group.id, task_log.id, True, False)

    bill = Bill.objects.get(expense_group__workspace_id=workspace_id)

    task_log = TaskLog.objects.get(expense_group=bill.expense_group)
    task_log.detail = data['bill_response']
    task_log.save()

    bill.expense_group.expenses.all().update(paid_on_fyle=True)

    with mock.patch('apps.sage_intacct.models.APPayment.create_ap_payment') as mock_call:
        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_ap_payment(workspace_id)

    now = datetime.now().replace(tzinfo=timezone.utc)
    updated_at = now - timedelta(days=25)
    # Update created_at to more than 2 months ago (more than 60 days)
    TaskLog.objects.filter(task_id='PAYMENT_{}'.format(bill.expense_group.id)).update(
        created_at=now - timedelta(days=61),  # More than 2 months ago
        updated_at=updated_at  # Updated within the last 1 month
    )

    task_log = TaskLog.objects.get(task_id='PAYMENT_{}'.format(bill.expense_group.id))

    create_ap_payment(workspace_id)
    task_log.refresh_from_db()

    assert task_log.updated_at == updated_at

    updated_at = now - timedelta(days=25)
    # Update created_at to between 1 and 2 months ago (between 30 and 60 days)
    TaskLog.objects.filter(task_id='PAYMENT_{}'.format(bill.expense_group.id)).update(
        created_at=now - timedelta(days=45),  # Between 1 and 2 months ago
        updated_at=updated_at  # Updated within the last 1 month
    )
    create_ap_payment(workspace_id)
    task_log.refresh_from_db()
    assert task_log.updated_at == updated_at

    updated_at = now - timedelta(days=5)
    # Update created_at to within the last 1 month (less than 30 days)
    TaskLog.objects.filter(task_id='PAYMENT_{}'.format(bill.expense_group.id)).update(
        created_at=now - timedelta(days=25),  # Within the last 1 month
        updated_at=updated_at  # Updated within the last week
    )
    create_ap_payment(workspace_id)
    task_log.refresh_from_db()
    assert task_log.updated_at == updated_at


def test_mark_paid_on_fyle(db, mocker):
    """
    Test mark paid on fyle
    """
    workspace_id = 1
    reports_to_be_marked = {'rp123', 'rp456'}

    report_id = 'rp123'

    payloads = [{'id': report_id}]

    Expense.objects.filter(workspace_id=workspace_id).update(paid_on_fyle=False, report_id=report_id)

    # Mock platform connector
    mock_platform = mock.Mock()
    mock_platform.reports.bulk_mark_as_paid = mock.Mock()

    # Test successful case
    mark_paid_on_fyle(mock_platform, payloads, reports_to_be_marked, workspace_id)
    mock_platform.reports.bulk_mark_as_paid.assert_called_once_with(payloads)
    assert not Expense.objects.filter(report_id__in=reports_to_be_marked, workspace_id=workspace_id, paid_on_fyle=False).exists()

    # Reset test data
    Expense.objects.filter(report_id__in=reports_to_be_marked).update(paid_on_fyle=False)

    # Test error case with permission denied
    error_response = {
        'data': [
            {'key': 'rp123', 'message': 'Permission denied to perform this action.'}
        ]
    }
    mock_platform.reports.bulk_mark_as_paid.side_effect = Exception()
    mock_platform.reports.bulk_mark_as_paid.side_effect.response = error_response

    mark_paid_on_fyle(mock_platform, payloads, reports_to_be_marked, workspace_id, retry_num=1)

    # Verify expenses are marked as paid despite the error
    assert not Expense.objects.filter(report_id__in=reports_to_be_marked, workspace_id=workspace_id, paid_on_fyle=False).exists()


def test_check_cache_and_search_vendors(db, mocker):
    """
    Test check_cache_and_search_vendors
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()
    fund_source = expense_group.fund_source

    cache.delete(f"{fund_source}_vendor_cache_{workspace_id}")

    mock_search_and_upsert_vendors = mocker.patch(
        'apps.sage_intacct.tasks.search_and_upsert_vendors'
    )

    check_cache_and_search_vendors(workspace_id, fund_source)

    assert mock_search_and_upsert_vendors.call_count == 1

    cache.set(f"{fund_source}_vendor_cache_{workspace_id}", datetime.now(tz=timezone.utc))

    check_cache_and_search_vendors(workspace_id, fund_source)

    assert mock_search_and_upsert_vendors.call_count == 1


def test_get_filtered_expense_group_ids(db):
    """
    Test get_filtered_expense_group_ids
    """
    expense_group_filters = {
        'fund_source': 'PERSONAL',
        'workspace_id': 1
    }

    expense_group = ExpenseGroup.objects.filter(**expense_group_filters).first()

    assert expense_group.workspace.id == 1
    assert expense_group.fund_source == 'PERSONAL'


def test_get_employee_as_vendors_name(db):
    """
    Test get_employee_as_vendors_name
    """
    workspace_id = 1
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).last()
    expense_group_ids = [expense_group.id]
    expense_group.expenses.update(workspace_id=workspace_id, employee_email='hrishabh.test@test.com')
    expense_group.save()

    employee = ExpenseAttribute.objects.filter(value='ashwin.t@fyle.in').first()

    employee.id = 10
    employee.value = 'hrishabh.test@test.com'
    employee.workspace_id = workspace_id
    employee.detail = {'full_name': 'Ashwin T'}
    employee.save()

    employee_as_vendors = get_employee_as_vendors_name(workspace_id, expense_group_ids)

    assert list(employee_as_vendors) == ['Ashwin T']


def test_search_and_upsert_vendors_ccc(db, mocker):
    """
    Test search_and_upsert_vendors ccc
    """
    workspace_id = 1
    configuration = Configuration.objects.filter(workspace_id=workspace_id).first()
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()

    configuration.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    configuration.save()

    expense_group.fund_source = 'CCC'
    expense_group.expenses.update(vendor='Test Vendor', workspace_id=workspace_id)
    expense_group.save()

    mock_search_and_create_vendors = mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.search_and_create_vendors')
    mocker.patch('apps.sage_intacct.tasks.get_filtered_expense_group_ids', return_value=[expense_group.id])
    mocker.patch('apps.sage_intacct.tasks.get_employee_as_vendors_name', return_value=['Ashwin T'])

    search_and_upsert_vendors(workspace_id=workspace_id, configuration=configuration, expense_group_filters={}, fund_source='CCC')

    assert mock_search_and_create_vendors.call_count == 1

    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.use_merchant_in_journal_line = False
    configuration.employee_field_mapping = 'VENDOR'
    configuration.save()

    search_and_upsert_vendors(workspace_id=workspace_id, configuration=configuration, expense_group_filters={}, fund_source='CCC')

    assert mock_search_and_create_vendors.call_count == 2


def test_search_and_upsert_vendors_personal(db, mocker):
    """
    Test search_and_upsert_vendors personal
    """
    workspace_id = 1
    configuration = Configuration.objects.filter(workspace_id=workspace_id).first()
    expense_group = ExpenseGroup.objects.filter(workspace_id=workspace_id).first()

    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.employee_field_mapping = 'VENDOR'
    configuration.save()

    mock_search_and_create_vendors = mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.search_and_create_vendors')
    mocker.patch('apps.sage_intacct.tasks.get_filtered_expense_group_ids', return_value=[expense_group.id])
    mocker.patch('apps.sage_intacct.tasks.get_employee_as_vendors_name', return_value=['Ashwin T'])

    search_and_upsert_vendors(workspace_id=workspace_id, configuration=configuration, expense_group_filters={}, fund_source='PERSONAL')

    assert mock_search_and_create_vendors.call_count == 1


def test_handle_skipped_exports(db, mocker):
    """
    Test handle skipped exports
    """
    mock_post_summary = mocker.patch('apps.sage_intacct.queue.post_accounting_export_summary_for_skipped_exports', return_value=None)
    mock_update_last_export = mocker.patch('apps.sage_intacct.queue.update_last_export_details')
    mock_logger = mocker.patch('apps.sage_intacct.queue.logger')
    mocker.patch('apps.workspaces.tasks.patch_integration_settings', return_value=None)
    mocker.patch('apps.fyle.actions.post_accounting_export_summary', return_value=None)

    # Create or get two expense groups
    eg1 = ExpenseGroup.objects.create(workspace_id=1, fund_source='PERSONAL')
    eg2 = ExpenseGroup.objects.create(workspace_id=1, fund_source='PERSONAL')
    expense_groups = ExpenseGroup.objects.filter(id__in=[eg1.id, eg2.id])

    # Case 1: triggered_by is DIRECT_EXPORT, not last export
    skip_export_count = 0
    result = handle_skipped_exports(
        expense_groups=expense_groups,
        index=0,
        skip_export_count=skip_export_count,
        expense_group=eg1,
        triggered_by=ExpenseImportSourceEnum.DIRECT_EXPORT
    )
    assert result == 1
    mock_post_summary.assert_called_once_with(expense_group=eg1, workspace_id=eg1.workspace_id)
    mock_update_last_export.assert_not_called()
    mock_logger.info.assert_called()

    mock_post_summary.reset_mock()
    mock_update_last_export.reset_mock()
    mock_logger.reset_mock()

    # Case 2: last export, skip_export_count == total_count-1, should call update_last_export_details
    skip_export_count = 1
    result = handle_skipped_exports(
        expense_groups=expense_groups,
        index=1,
        skip_export_count=skip_export_count,
        expense_group=eg2,
        triggered_by=ExpenseImportSourceEnum.DASHBOARD_SYNC
    )
    assert result == 2
    mock_post_summary.assert_not_called()
    mock_update_last_export.assert_called_once_with(eg2.workspace_id)
    mock_logger.info.assert_called()


def test_create_journal_entry_task_log_does_not_exist(mocker, db):
    """
    Test create_journal_entry when TaskLog.DoesNotExist is raised
    Case: TaskLog with given task_log_id does not exist
    """
    mock_logger = mocker.patch('apps.sage_intacct.tasks.get_logger')
    mock_logger.return_value.info = mocker.Mock()

    create_journal_entry(expense_group_id=1, task_log_id=99999, last_export=True, is_auto_export=False)

    mock_logger.return_value.info.assert_called_with(
        'Task log %s no longer exists, skipping journal entry creation', 99999
    )


def test_create_expense_report_task_log_does_not_exist(mocker, db):
    """
    Test create_expense_report when TaskLog.DoesNotExist is raised
    Case: TaskLog with given task_log_id does not exist
    """
    mock_logger = mocker.patch('apps.sage_intacct.tasks.get_logger')
    mock_logger.return_value.info = mocker.Mock()

    create_expense_report(expense_group_id=1, task_log_id=99999, last_export=True, is_auto_export=False)

    mock_logger.return_value.info.assert_called_with(
        'Task log %s was deleted (likely due to export settings change), skipping expense report creation', 99999
    )


def test_create_bill_task_log_does_not_exist(mocker, db):
    """
    Test create_bill when TaskLog.DoesNotExist is raised
    Case: TaskLog with given task_log_id does not exist
    """
    mock_logger = mocker.patch('apps.sage_intacct.tasks.get_logger')
    mock_logger.return_value.info = mocker.Mock()

    create_bill(expense_group_id=1, task_log_id=99999, last_export=True, is_auto_export=False)

    mock_logger.return_value.info.assert_called_with(
        'Task log %s was deleted (likely due to export settings change), skipping bill creation', 99999
    )


def test_create_charge_card_transaction_task_log_does_not_exist(mocker, db):
    """
    Test create_charge_card_transaction when TaskLog.DoesNotExist is raised
    Case: TaskLog with given task_log_id does not exist
    """
    mock_logger = mocker.patch('apps.sage_intacct.tasks.get_logger')
    mock_logger.return_value.info = mocker.Mock()

    create_charge_card_transaction(expense_group_id=1, task_log_id=99999, last_export=True, is_auto_export=False)

    mock_logger.return_value.info.assert_called_with(
        'Task log %s was deleted (likely due to export settings change), skipping charge card transaction creation', 99999
    )


def test_create_journal_entry_exported_to_intacct_status_on_post_export_failure(mocker, create_task_logs, db):
    """
    Test that create_journal_entry sets status to EXPORTED_TO_INTACCT when export succeeds but post-export fails
    """
    mocker.patch(
        'sageintacctsdk.apis.JournalEntries.post',
        return_value=data['journal_entry_response']
    )
    mocker.patch(
        'apps.sage_intacct.tasks.load_attachments',
        return_value=('sdfgh', False)
    )
    # Mock get_journal_entry_record_number to raise an exception after export succeeds
    mocker.patch(
        'apps.sage_intacct.tasks.get_journal_entry_record_number',
        side_effect=Exception('Failed to get record number')
    )

    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'ENQUEUED'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=3)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()

    expense_group.expenses.set(expenses)
    expense_group.save()

    create_journal_entry(expense_group.id, task_log.id, True, False)

    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'
    assert 'created_journal_entry' in task_log.detail
    assert task_log.journal_entry is None


def test_create_bill_exported_to_intacct_status_on_post_export_failure(mocker, create_task_logs, db):
    """
    Test that create_bill sets status to EXPORTED_TO_INTACCT when export succeeds but post-export fails
    """
    mocker.patch(
        'sageintacctsdk.apis.Bills.post',
        return_value=data['bill_response']
    )
    mocker.patch(
        'apps.sage_intacct.tasks.load_attachments',
        return_value=('sdfgh', False)
    )
    # Mock get_bill to raise an exception after export succeeds
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_bill',
        side_effect=Exception('Failed to get bill')
    )

    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'ENQUEUED'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()

    expense_group.expenses.set(expenses)

    create_bill(expense_group.id, task_log.id, True, False)

    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'
    assert 'created_bill' in task_log.detail
    assert task_log.bill is None


def test_create_expense_report_exported_to_intacct_status_on_post_export_failure(mocker, create_task_logs, db):
    """
    Test that create_expense_report sets status to EXPORTED_TO_INTACCT when export succeeds but post-export fails
    """
    mocker.patch(
        'sageintacctsdk.apis.ExpenseReports.post',
        return_value=data['expense_report_post_response']
    )
    mocker.patch(
        'apps.sage_intacct.tasks.load_attachments',
        return_value=('sdfgh', False)
    )
    # Mock get_expense_report to raise an exception after export succeeds
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_expense_report',
        side_effect=Exception('Failed to get expense report')
    )
    mocker.patch(
        'apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
    )

    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'ENQUEUED'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()

    expense_group.expenses.set(expenses)

    create_expense_report(expense_group.id, task_log.id, True, False)

    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'
    assert 'created_expense_report' in task_log.detail
    assert task_log.expense_report is None


def test_create_charge_card_transaction_exported_to_intacct_status_on_post_export_failure(mocker, create_task_logs, db):
    """
    Test that create_charge_card_transaction sets status to EXPORTED_TO_INTACCT when export succeeds but post-export fails
    """
    mocker.patch(
        'sageintacctsdk.apis.ChargeCardTransactions.post',
        return_value=data['credit_card_response']
    )
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor',
        return_value=DestinationAttribute.objects.get(id=633)
    )
    mocker.patch(
        'apps.sage_intacct.tasks.load_attachments',
        return_value=('sdfgh', False)
    )
    # Mock get_charge_card_transaction to raise an exception after export succeeds
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_charge_card_transaction',
        side_effect=Exception('Failed to get charge card transaction')
    )

    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'ENQUEUED'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=2)
    expense_group.description.update({'employee_email': 'user4444@fyleforgotham.in'})
    expense_group.save()

    expenses = expense_group.expenses.all()

    expense_group.id = random.randint(100, 1500000)
    expense_group.save()

    for expense in expenses:
        expense.expense_group_id = expense_group.id
        expense.save()

    expense_group.expenses.set(expenses)

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_charge_card_id = 'sample'
    general_mappings.save()

    create_charge_card_transaction(expense_group.id, task_log.id, True, False)

    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'
    assert 'created_charge_card_transaction' in task_log.detail
    assert task_log.charge_card_transaction is None


def test_create_journal_entry_skips_exported_to_intacct_status(mocker, create_task_logs, db):
    """
    Test that create_journal_entry skips processing when task log status is EXPORTED_TO_INTACCT
    """
    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'EXPORTED_TO_INTACCT'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=3)

    mock_post = mocker.patch('sageintacctsdk.apis.JournalEntries.post')

    create_journal_entry(expense_group.id, task_log.id, True, False)

    # Should not call post since status is EXPORTED_TO_INTACCT
    mock_post.assert_not_called()
    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'


def test_create_bill_skips_exported_to_intacct_status(mocker, create_task_logs, db):
    """
    Test that create_bill skips processing when task log status is EXPORTED_TO_INTACCT
    """
    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'EXPORTED_TO_INTACCT'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)

    mock_post = mocker.patch('sageintacctsdk.apis.Bills.post')

    create_bill(expense_group.id, task_log.id, True, False)

    # Should not call post since status is EXPORTED_TO_INTACCT
    mock_post.assert_not_called()
    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'


def test_create_expense_report_skips_exported_to_intacct_status(mocker, create_task_logs, db):
    """
    Test that create_expense_report skips processing when task log status is EXPORTED_TO_INTACCT
    """
    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'EXPORTED_TO_INTACCT'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)

    mock_post = mocker.patch('sageintacctsdk.apis.ExpenseReports.post')

    create_expense_report(expense_group.id, task_log.id, True, False)

    # Should not call post since status is EXPORTED_TO_INTACCT
    mock_post.assert_not_called()
    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'


def test_create_charge_card_transaction_skips_exported_to_intacct_status(mocker, create_task_logs, db):
    """
    Test that create_charge_card_transaction skips processing when task log status is EXPORTED_TO_INTACCT
    """
    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'EXPORTED_TO_INTACCT'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=2)

    mock_post = mocker.patch('sageintacctsdk.apis.ChargeCardTransactions.post')

    create_charge_card_transaction(expense_group.id, task_log.id, True, False)

    # Should not call post since status is EXPORTED_TO_INTACCT
    mock_post.assert_not_called()
    task_log.refresh_from_db()
    assert task_log.status == 'EXPORTED_TO_INTACCT'
