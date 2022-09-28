from apps.mappings.models import GeneralMapping
import pytest
from datetime import datetime, timezone
from fyle_rest_auth.models import User
from apps.sage_intacct.utils import Bill,BillLineitem
from apps.fyle.models import ExpenseGroup
from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import Mapping, MappingSetting
from apps.sage_intacct.models import get_department_id_or_none,get_tax_code_id_or_none, get_customer_id_or_none, \
    get_project_id_or_none, get_class_id_or_none, get_expense_purpose, get_transaction_date, get_location_id_or_none, \
        get_intacct_employee_object, \
    APPayment, APPaymentLineitem, JournalEntry, JournalEntryLineitem, ExpenseReport, ExpenseReportLineitem, \
        ChargeCardTransaction, ChargeCardTransactionLineitem, SageIntacctReimbursement, SageIntacctReimbursementLineitem
from apps.tasks.models import TaskLog


def test_create_bill(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    bill = Bill.create_bill(expense_group)
    bill_lineitems = BillLineitem.create_bill_lineitems(expense_group, workspace_general_settings)

    for bill_lineitem in bill_lineitems:
        assert bill_lineitem.amount == 21.0
        assert bill_lineitem.billable == False

    assert bill.currency == 'USD'
    assert bill.transaction_date.split('T')[0] == datetime.now().strftime('%Y-%m-%d')
    assert bill.vendor_id == 'Ashwin'


def test_expense_report(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    expense_report = ExpenseReport.create_expense_report(expense_group)
    expense_report_lineitems  = ExpenseReportLineitem.create_expense_report_lineitems(expense_group, workspace_general_settings)

    for expense_report_lineitem in expense_report_lineitems:
        assert expense_report_lineitem.amount == 11.0
        assert expense_report_lineitem.memo == 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/main/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'
        assert expense_report_lineitem.billable == True

    assert expense_report.currency == 'USD'
    assert expense_report.transaction_date.split('T')[0] == datetime.now().strftime('%Y-%m-%d')


def test_create_journal_entry(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    journal_entry = JournalEntry.create_journal_entry(expense_group)
    journal_entry_lineitems  = JournalEntryLineitem.create_journal_entry_lineitems(expense_group, workspace_general_settings)

    for journal_entry_lineitem in journal_entry_lineitems:
        assert journal_entry_lineitem.amount == 11.0
        assert journal_entry_lineitem.memo == 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/main/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'

    assert journal_entry.currency == 'USD'
    assert journal_entry.transaction_date.split('T')[0] == datetime.now().strftime('%Y-%m-%d')


def test_create_ap_payment(db):

    expense_group = ExpenseGroup.objects.get(id=1)

    ap_payment = APPayment.create_ap_payment(expense_group)

    ap_payment_lineitems = APPaymentLineitem.create_ap_payment_lineitems(expense_group, '3032')

    for ap_payment_lineitem in ap_payment_lineitems:
        assert ap_payment_lineitem.amount == 21.0

    assert ap_payment.currency == 'USD'
    assert ap_payment.vendor_id == 'Ashwin'


def test_create_charge_card_transaction(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    expense_group.description.update({'employee_email': 'user4444@fyleforgotham.in'})
    expense_group.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id) 
    general_mappings.default_charge_card_id = 'sample'
    general_mappings.save()

    charge_card_transaction = ChargeCardTransaction.create_charge_card_transaction(expense_group)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    charge_card_transaction_lineitems = ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(expense_group, workspace_general_settings)

    for charge_card_transaction_lineitem in charge_card_transaction_lineitems:
        assert charge_card_transaction_lineitem.amount == 21.0
        
    assert charge_card_transaction.currency == 'USD'
    assert charge_card_transaction.transaction_date.split('T')[0] == '2022-09-20'


def test_create_sage_intacct_reimbursement(db):

    expense_group = ExpenseGroup.objects.get(id=1)
    sage_intacct_reimbursement = SageIntacctReimbursement.create_sage_intacct_reimbursement(expense_group)

    sage_intacct_reimbursement_lineitems = SageIntacctReimbursementLineitem.create_sage_intacct_reimbursement_lineitems(expense_group, '3032')

    for sage_intacct_reimbursement_lineitem in sage_intacct_reimbursement_lineitems:
        assert sage_intacct_reimbursement_lineitem.amount == 21.0
        
    assert sage_intacct_reimbursement.payment_description == 'Payment for Expense Report by ashwin.t@fyle.in'


def test_get_project_id_or_none(mocker, db):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
        return_value={'options': ['samp'], 'updated_at': '2020-06-11T13:14:55.201598+00:00', 'is_mandatory': False}
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.sync',
        return_value=None
    )
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()
    general_mapping = GeneralMapping.objects.get(workspace_id=workspace_id)

    project_id = get_project_id_or_none(expense_group, expenses[0], general_mapping)

    assert project_id == '10061'

    mapping_setting = MappingSetting.objects.filter( 
        workspace_id=expense_group.workspace_id, 
        destination_field='PROJECT' 
    ).first() 

    mapping_setting.source_field = 'TEAM_2_POSTMAN'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_department_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '300'

    mapping_setting.source_field = 'COST_CENTER'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_department_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '300'


def test_get_department_id_or_none(mocker, db):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
        return_value={'options': ['samp'], 'updated_at': '2020-06-11T13:14:55.201598+00:00', 'is_mandatory': False}
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.sync',
        return_value=None
    )
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    general_mapping = GeneralMapping.objects.get(workspace_id=workspace_id)

    for lineitem in expenses:
        location_id = get_department_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '300'

    mapping_setting = MappingSetting.objects.filter( 
        workspace_id=expense_group.workspace_id, 
        destination_field='DEPARTMENT' 
    ).first() 

    mapping_setting.source_field = 'TEAM_2_POSTMAN'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_department_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '300'

    mapping_setting.source_field = 'COST_CENTER'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_department_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '300'


def test_get_tax_code_id_or_none(db):
    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    for lineitem in expenses:
        location_id = get_tax_code_id_or_none(expense_group, lineitem)
        assert location_id == None


def test_get_customer_id_or_none(mocker, db):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
        return_value={'options': ['samp'], 'updated_at': '2020-06-11T13:14:55.201598+00:00', 'is_mandatory': False}
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.sync',
        return_value=None
    )
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    general_mapping = GeneralMapping.objects.get(workspace_id=workspace_id)

    for lineitem in expenses:
        location_id = get_customer_id_or_none(expense_group, lineitem, general_mapping, '')
        assert location_id == None
    
    mapping_setting = MappingSetting.objects.filter( 
        workspace_id=expense_group.workspace_id, 
        destination_field='PROJECT' 
    ).first()

    mapping_setting.destination_field = 'CUSTOMER'
    mapping_setting.save()

    mapping_setting.source_field = 'PROJECT'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_customer_id_or_none(expense_group, lineitem, general_mapping, 10064)
        assert location_id == '10064'

    mapping_setting.source_field = 'COST_CENTER'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_customer_id_or_none(expense_group, lineitem, general_mapping, '')
        assert location_id == None

    mapping_setting.source_field = 'TEAM_2_POSTMAN'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_customer_id_or_none(expense_group, lineitem, general_mapping, '')
        assert location_id == None


def test_get_class_id_or_none(mocker, db):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
        return_value={'options': ['samp'], 'updated_at': '2020-06-11T13:14:55.201598+00:00', 'is_mandatory': False}
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.sync',
        return_value=None
    )
    workspace_id = 1
    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    general_mapping = GeneralMapping.objects.get(workspace_id=workspace_id)
    mapping_setting = MappingSetting.objects.filter( 
        workspace_id=expense_group.workspace_id, 
        destination_field='PROJECT' 
    ).first()

    mapping_setting.destination_field = 'CLASS'
    mapping_setting.save()

    for lineitem in expenses:
        location_id = get_class_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '600'

    mapping_setting.source_field = 'TEAM_2_POSTMAN'
    mapping_setting.save()

    for lineitem in expenses:
        location_id = get_class_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '600'

    mapping_setting.source_field = 'COST_CENTER'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_class_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '600'


def test_get_expense_purpose(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    expenses = expense_group.expenses.all()

    for lineitem in expenses:
        category = lineitem.category if lineitem.category == lineitem.sub_category else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)
    
        expense_purpose = get_expense_purpose(workspace_id, lineitem, category, workspace_general_settings)

        assert expense_purpose == 'ashwin.t@fyle.in - Food / None - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/main/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'


def test_get_transaction_date(mocker, db):

    expense_group = ExpenseGroup.objects.get(id=1)
    transaction_date = get_transaction_date(expense_group)

    assert transaction_date >= datetime.now().strftime('%Y-%m-%d')


def test_get_location_id_or_none(mocker, db):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
        return_value={'options': ['samp'], 'updated_at': '2020-06-11T13:14:55.201598+00:00', 'is_mandatory': False}
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.sync',
        return_value=None
    )
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    general_mapping = GeneralMapping.objects.get(workspace_id=workspace_id)

    mapping_setting = MappingSetting.objects.filter( 
        workspace_id=expense_group.workspace_id, 
        destination_field='PROJECT' 
    ).first()

    mapping_setting.destination_field='LOCATION'
    mapping_setting.save()

    for lineitem in expenses:
        location_id = get_location_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '600'
    
    mapping_setting.source_field = 'TEAM_2_POSTMAN'
    mapping_setting.save()

    for lineitem in expenses:
        location_id = get_location_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '600'
    
    mapping_setting.source_field = 'COST_CENTER'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_location_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '600'


def test_get_intacct_employee_object(db):
    expense_group = ExpenseGroup.objects.get(id=1)
    
    default_employee_object = get_intacct_employee_object('email', expense_group)
    assert default_employee_object == 'ashwin.t@fyle.in'
