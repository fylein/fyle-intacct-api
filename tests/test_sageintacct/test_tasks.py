import logging
import random
from unittest import mock
from django_q.models import Schedule
from apps.tasks.models import TaskLog
from apps.sage_intacct.models import *
from apps.sage_intacct.tasks import __validate_expense_group
from apps.sage_intacct.tasks import *
from apps.sage_intacct.queue import *
from fyle_intacct_api.exceptions import BulkError
from sageintacctsdk.exceptions import WrongParamsError, InvalidTokenError, NoPrivilegeError
from fyle_accounting_mappings.models import EmployeeMapping
from apps.workspaces.models import Configuration, SageIntacctCredential
from fyle_accounting_mappings.models import DestinationAttribute, EmployeeMapping
from apps.fyle.models import ExpenseGroup, Reimbursement
from apps.sage_intacct.utils import SageIntacctConnector
from apps.mappings.models import GeneralMapping
from .fixtures import data
from django.conf import settings

logger = logging.getLogger(__name__)


def test_handle_intacct_errors(db):
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
    error: Error = Error.objects.filter(workspace_id=1).first()

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


def test_get_or_create_credit_card_vendor(mocker, db):
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor',
        return_value=[]
    )
    workspace_id = 1

    general_settings = Configuration.objects.get(workspace_id=workspace_id)

    contact = get_or_create_credit_card_vendor('samp_merchant', workspace_id)
    assert contact != None

    contact = get_or_create_credit_card_vendor('', workspace_id)
    assert contact != None

    try:
        with mock.patch('apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor') as mock_call:
            mock_call.side_effect = WrongParamsError(msg='wrong parameters', response='wrong parameters')
            contact = get_or_create_credit_card_vendor('samp_merchant', workspace_id)

            mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
            contact = get_or_create_credit_card_vendor('samp_merchant', workspace_id)
    except:
        logger.info('wrong parameters')


def test_create_or_update_employee_mapping(mocker, db):
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
        return_value={'data': {'employee': data['get_employees'][0]}}
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
        except:
            logger.info('Employee mapping not found')


def test_post_bill_success(mocker, create_task_logs, db):
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
        return_value=['sdfgh']
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
    
    create_bill(expense_group, task_log.id, True)
    
    task_log = TaskLog.objects.get(pk=task_log.id)
    bill = Bill.objects.get(expense_group_id=expense_group.id)
    assert task_log.status=='COMPLETE'
    assert bill.currency == 'USD'
    assert bill.vendor_id == 'Ashwin'

    task_log.status = 'READY'
    task_log.save()

    with mock.patch('apps.sage_intacct.utils.SageIntacctConnector.update_bill') as mock_call:
        mock_call.side_effect = Exception()
        create_bill(expense_group, task_log.id, True)

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_bill(expense_group, task_log.id, True)


def test_create_bill_exceptions(mocker, db, create_task_logs):
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
        create_bill(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_bill(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = Exception()
        create_bill(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FATAL'

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            })
        create_bill(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
            })
        create_bill(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_bill(expense_group, task_log.id, True)


def test_post_sage_intacct_reimbursements_success(mocker, create_task_logs, db, create_expense_report):
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

        mock_call.side_effect = Exception()
        create_sage_intacct_reimbursement(workspace_id)

        task_log = TaskLog.objects.get(task_id='PAYMENT_{}'.format(expense_report.expense_group.id))
        assert task_log.status == 'FATAL'

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
        })
        create_sage_intacct_reimbursement(workspace_id)

        task_log = TaskLog.objects.get(task_id='PAYMENT_{}'.format(expense_report.expense_group.id))
        assert task_log.status == 'FAILED'

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
        })
        create_sage_intacct_reimbursement(workspace_id)

        task_log = TaskLog.objects.get(task_id='PAYMENT_{}'.format(expense_report.expense_group.id))
        assert task_log.status == 'FAILED'

        mock_call.side_effect = SageIntacctCredential.DoesNotExist()
        create_sage_intacct_reimbursement(workspace_id)

        task_log = TaskLog.objects.get(task_id='PAYMENT_{}'.format(expense_report.expense_group.id))
        assert task_log.status == 'FAILED'

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_sage_intacct_reimbursement(workspace_id)

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
        })
        create_sage_intacct_reimbursement(workspace_id)
        expense_report = ExpenseReport.objects.get(id=expense_report.id)

        assert expense_report.paid_on_sage_intacct == True
        assert expense_report.payment_synced == True

def test_post_charge_card_transaction_success(mocker, create_task_logs, db):
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
        return_value=['sdfgh']
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

    create_charge_card_transaction(expense_group, task_log.id, True)
    
    task_log = TaskLog.objects.get(pk=task_log.id)
    charge_card_transaction = ChargeCardTransaction.objects.get(expense_group_id=expense_group.id)

    assert task_log.status=='COMPLETE'
    assert charge_card_transaction.currency == 'USD'

    with mock.patch('sageintacctsdk.apis.ChargeCardTransactions.update_attachment') as mock_call:
        mock_call.side_effect = Exception()
        create_charge_card_transaction(expense_group, task_log.id, True)

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_charge_card_transaction(expense_group, task_log.id, True)


def test_post_credit_card_exceptions(mocker, create_task_logs, db):
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor',
        return_value=DestinationAttribute.objects.get(id=633)
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
        create_charge_card_transaction(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_charge_card_transaction(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = Exception()
        create_charge_card_transaction(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FATAL'

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
        })
        create_charge_card_transaction(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
        })
        create_charge_card_transaction(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_charge_card_transaction(expense_group, task_log.id, True)

def test_post_journal_entry_success(mocker, create_task_logs, db):
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
        return_value=['sdfgh']
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
    
    create_journal_entry(expense_group, task_log.id, True)
    
    task_log = TaskLog.objects.get(id=task_log.id)
    journal_entry = JournalEntry.objects.get(expense_group_id=expense_group.id)

    assert task_log.status=='COMPLETE'
    assert journal_entry.currency == 'GBP'

    task_log.status = 'READY'
    task_log.save()

    with mock.patch('sageintacctsdk.apis.JournalEntries.update') as mock_call:
        mock_call.side_effect = Exception()
        create_journal_entry(expense_group, task_log.id, True)

        mock_call.side_effect = NoPrivilegeError(msg='insufficient permission', response='insufficient permission')
        create_journal_entry(expense_group, task_log.id, True)


def test_post_create_journal_entry_exceptions(create_task_logs, db):
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
        create_journal_entry(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_journal_entry(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = Exception()
        create_journal_entry(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FATAL'

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
        })
        create_journal_entry(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': {'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''},
                'type': 'Invalid_params'
        })
        create_journal_entry(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = NoPrivilegeError(msg='Insufficient Permission', response="Insufficient Permission")
        create_journal_entry(expense_group, task_log.id, True)


def test_post_expense_report_success(mocker, create_task_logs, db):
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
        return_value=['sdfgh']
    )

    mocker.patch(
        'apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
    )

    workspace_id = 1

    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()
    task_log.status = 'READY'
    task_log.save()

    expense_group = ExpenseGroup.objects.get(id=1)
    create_expense_report(expense_group, task_log.id, True)
    
    task_log = TaskLog.objects.get(id=task_log.id)
    expense_report = ExpenseReport.objects.get(expense_group_id=expense_group.id)

    assert task_log.status=='COMPLETE'
    assert expense_report.currency == 'USD'

    task_log.status = 'READY'
    task_log.save()

    with mock.patch('sageintacctsdk.apis.ExpenseReports.update_attachment') as mock_call:
        mock_call.side_effect = Exception()
        create_expense_report(expense_group, task_log.id, True)

        mock_call.side_effect = NoPrivilegeError(msg='Insufficient Permission', response="Insufficient Permission")
        create_expense_report(expense_group, task_log.id, True)


def test_post_create_expense_report_exceptions(mocker, create_task_logs, db):
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

    with mock.patch('apps.sage_intacct.utils.SageIntacctConnector.post_expense_report') as mock_call:
        mock_call.side_effect = SageIntacctCredential.DoesNotExist()
        create_expense_report(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = BulkError(msg='employess not found', response='mapping error')
        create_expense_report(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = Exception()
        create_expense_report(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FATAL'

        mock_call.side_effect = WrongParamsError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
        })
        create_expense_report(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': [{'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''}],
                'type': 'Invalid_params'
        })
        create_expense_report(expense_group, task_log.id, True)

        task_log = TaskLog.objects.get(id=task_log.id)
        assert task_log.status == 'FAILED'

        mock_call.side_effect = NoPrivilegeError(msg='Insufficient Permission', response="Insufficient Permission")
        create_expense_report(expense_group, task_log.id, True)

def test_create_ap_payment(mocker, db):
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
        return_value=['sdfgh']
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
    
    create_bill(expense_group, task_log.id, True)

    bill = Bill.objects.get(expense_group__workspace_id=workspace_id)

    task_log = TaskLog.objects.get(expense_group=bill.expense_group)
    task_log.detail = data['bill_response']
    task_log.save()

    create_ap_payment(workspace_id)
    assert task_log.status == 'COMPLETE'


def test_post_ap_payment_exceptions(mocker, db):
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
    
    create_bill(expense_group, task_log.id, True)

    bill = Bill.objects.last()
    task_log = TaskLog.objects.get(id=task_log.id)
    task_log.expense_group=bill.expense_group
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
        })
        create_ap_payment(workspace_id)

        mock_call.side_effect = InvalidTokenError(
            msg={
                'Message': 'Invalid parametrs'
            }, response={
                'error': {'code': 400, 'Message': 'Invalid parametrs', 'Detail': 'Invalid parametrs', 'description': '', 'description2': '', 'correction': ''},
                'type': 'Invalid_params'
        })
        create_ap_payment(workspace_id)

        mock_call.side_effect = NoPrivilegeError(msg="insufficient permission", response="insufficient permission")
        create_ap_payment(workspace_id)

        try:
            mock_call.side_effect = SageIntacctCredential.DoesNotExist()
            create_ap_payment(workspace_id)
        except:
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
        })
        create_ap_payment(workspace_id)
        bill = Bill.objects.get(id=bill.id)

        assert bill.paid_on_sage_intacct == True
        assert bill.payment_synced == True


def test_schedule_ap_payment_creation(db):
    workspace_id = 1
    workspace_configuration = Configuration.objects.get(workspace_id=workspace_id)

    schedule_ap_payment_creation(configuration=workspace_configuration, workspace_id=workspace_id)
    schedule = Schedule.objects.filter(func='apps.sage_intacct.tasks.create_ap_payment').count()

    assert schedule == 1
    workspace_configuration.sync_fyle_to_sage_intacct_payments = False
    schedule_ap_payment_creation(configuration=workspace_configuration, workspace_id=workspace_id)
    schedule = Schedule.objects.filter(func='apps.sage_intacct.tasks.create_ap_payment').count()

    assert schedule == 0


def test_check_sage_intacct_object_status(mocker, db):
    mocker.patch(
        'sageintacctsdk.apis.Bills.get',
        return_value=data['get_bill']
    )
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_expense_report',
        return_value=data['expense_report_response']['data']
    )
    workspace_id = 1
    
    expense_group = ExpenseGroup.objects.get(id=1)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    bill = Bill.create_bill(expense_group)
    bill_lineitems = BillLineitem.create_bill_lineitems(expense_group, workspace_general_settings)

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
    expense_report_lineitems = ExpenseReportLineitem.create_expense_report_lineitems(expense_group, workspace_general_settings)

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

    with mock.patch('apps.sage_intacct.utils.SageIntacctConnector.get_expense_report') as mock_call:
        mock_call.side_effect = NoPrivilegeError(msg="insufficient permission", response="insufficient permission")
        check_sage_intacct_object_status(workspace_id)

def test_schedule_fyle_reimbursements_sync(db):
    workspace_id = 1

    schedule = Schedule.objects.filter(func='apps.sage_intacct.tasks.process_fyle_reimbursements', args=workspace_id).count()
    assert schedule == 0

    schedule_fyle_reimbursements_sync(sync_sage_intacct_to_fyle_payments=True, workspace_id=workspace_id)

    schedule_count = Schedule.objects.filter(func='apps.sage_intacct.tasks.process_fyle_reimbursements', args=workspace_id).count()
    assert schedule_count == 1

    schedule_fyle_reimbursements_sync(sync_sage_intacct_to_fyle_payments=False, workspace_id=workspace_id)

    schedule_count = Schedule.objects.filter(func='apps.sage_intacct.tasks.process_fyle_reimbursements', args=workspace_id).count()
    assert schedule_count == 0


def test_process_fyle_reimbursements(db, mocker):

    mocker.patch(
        'fyle_integrations_platform_connector.apis.Reports.bulk_mark_as_paid',
        return_value=[]
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Reimbursements.sync',
        return_value=[],
    )
    workspace_id = 1

    reimbursements = data['reimbursements']

    expenses = Expense.objects.filter(fund_source='PERSONAL')
    for expense in expenses:
        expense.paid_on_sage_intacct=True
        expense.save()

    reimbursement = Reimbursement.objects.filter(workspace_id=workspace_id).first()
    reimbursement.state = 'PENDING'
    reimbursement.save()

    process_fyle_reimbursements(workspace_id)

    reimbursement = Reimbursement.objects.filter(workspace_id=workspace_id).count()

    assert reimbursement == 258


def test_schedule_sage_intacct_objects_status_sync(db):
    workspace_id = 1

    schedule_sage_intacct_objects_status_sync(sync_sage_intacct_to_fyle_payments=True, workspace_id=workspace_id)

    schedule_count = Schedule.objects.filter(func='apps.sage_intacct.tasks.check_sage_intacct_object_status', args=workspace_id).count()
    assert schedule_count == 1

    schedule_sage_intacct_objects_status_sync(sync_sage_intacct_to_fyle_payments=False, workspace_id=workspace_id)

    schedule_count = Schedule.objects.filter(func='apps.sage_intacct.tasks.check_sage_intacct_object_status', args=workspace_id).count()
    assert schedule_count == 0


def test_schedule_journal_entries_creation(mocker, db):
    workspace_id = 1

    schedule_journal_entries_creation(workspace_id, [1], False, 'PERSONAL', 1)

    TaskLog.objects.filter(type='CREATING_JOURNAL_ENTRIES').count() != 0


def test_schedule_expense_reports_creation(mocker, db):
    workspace_id = 1

    schedule_expense_reports_creation(workspace_id, [1], False, 'PERSONAL', 1)

    TaskLog.objects.filter(type='CREATING_EXPENSE_REPORTS').count() != 0


def test_schedule_bills_creation(mocker, db):
    workspace_id = 1

    schedule_bills_creation(workspace_id, [1], False, 'PERSONAL', 1)

    TaskLog.objects.filter(type='CREATING_BILLS').count() != 0


def test_schedule_charge_card_transaction_creation(mocker, db):
    workspace_id = 1

    schedule_charge_card_transaction_creation(workspace_id, [2], False, 'CCC', 1)

    TaskLog.objects.filter(type='CREATING_CHARGE_CARD_TRANSACTIONS').count() != 0


def test_schedule_sage_intacct_reimbursement_creation(mocker, db):
    workspace_id = 1
    workspace_configuration = Configuration.objects.get(workspace_id=workspace_id)
    workspace_configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    schedule_sage_intacct_reimbursement_creation(configuration=workspace_configuration, workspace_id=workspace_id)

    schedule_count = Schedule.objects.filter(func='apps.sage_intacct.tasks.create_sage_intacct_reimbursement', args=workspace_id).count()
    assert schedule_count == 1

    workspace_configuration.sync_fyle_to_sage_intacct_payments = False
    schedule_sage_intacct_reimbursement_creation(configuration=workspace_configuration, workspace_id=workspace_id)

    schedule_count = Schedule.objects.filter(func='apps.sage_intacct.tasks.create_sage_intacct_reimbursement', args=workspace_id).count()
    assert schedule_count == 0


def test__validate_expense_group(mocker, db):
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
    except:
        logger.info('Mappings are missing')

    configuration.corporate_credit_card_expenses_object = 'BILL'
    configuration.save()

    try:
        __validate_expense_group(expense_group, configuration)
    except:
        logger.info('Mappings are missing')

    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()
    expense_group.description.update({'employee_email': 'ashwin.t@fyle.in'})
    expense_group.save()

    try:
        __validate_expense_group(expense_group, configuration)
    except:
        logger.info('Mappings are missing')

    configuration.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    try:
        __validate_expense_group(expense_group, configuration)
    except:
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

    mocker.patch(
        'sageintacctsdk.apis.Attachments.post',
        return_value=['sdfghj']
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Files.bulk_generate_file_urls',
        return_value=['sdfghj']
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

    post_attachments = load_attachments(sage_intacct_connection, expense_group)
    assert post_attachments == None

    try:
        with mock.patch('fyle_integrations_platform_connector.apis.Files.bulk_generate_file_urls') as mock_call:
            mock_call.side_effect = Exception()
            post_attachments = load_attachments(sage_intacct_connection, expense_group)
    except:
        logger.info('wrong parameters')


def test_update_last_export_details(db):
    workspace_id = 1
    last_export_detail = update_last_export_details(workspace_id)
    assert last_export_detail.export_mode == 'MANUAL'
