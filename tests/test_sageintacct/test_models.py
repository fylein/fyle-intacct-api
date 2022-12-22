import logging
from datetime import datetime
from apps.mappings.models import GeneralMapping
from apps.sage_intacct.utils import Bill,BillLineitem
from apps.fyle.models import ExpenseGroup, ExpenseGroupSettings, ExpenseAttribute
from apps.workspaces.models import Configuration, Workspace
from fyle_accounting_mappings.models import MappingSetting
from apps.sage_intacct.models import *

logger = logging.getLogger(__name__)
logger.level = logging.INFO

def test_create_bill(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.use_intacct_employee_locations = True
    general_mappings.use_intacct_employee_departments = True
    general_mappings.save()

    bill = Bill.create_bill(expense_group)
    bill_lineitems = BillLineitem.create_bill_lineitems(expense_group, workspace_general_settings)

    for bill_lineitem in bill_lineitems:
        assert bill_lineitem.amount == 21.0
        assert bill_lineitem.billable == False

    assert bill.currency == 'USD'
    assert bill.transaction_date.split('T')[0] == datetime.now().strftime('%Y-%m-%d')
    assert bill.vendor_id == 'Ashwin'

    expense_group = ExpenseGroup.objects.get(id=2)

    bill = Bill.create_bill(expense_group)
    bill_lineitems = BillLineitem.create_bill_lineitems(expense_group, workspace_general_settings)

    for bill_lineitem in bill_lineitems:
        assert bill_lineitem.amount == 11.0
        assert bill_lineitem.billable == True

    assert bill.currency == 'USD'
    assert bill.transaction_date.split('T')[0] == datetime.now().strftime('%Y-%m-%d')
    assert bill.vendor_id == '20043'

    try:
        general_mappings.delete()
        bill_lineitems = BillLineitem.create_bill_lineitems(expense_group, workspace_general_settings)
    except:
        logger.info('General mapping not found')
        

def test_expense_report(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.use_intacct_employee_locations = True
    general_mappings.use_intacct_employee_departments = True
    general_mappings.save()

    expense_report = ExpenseReport.create_expense_report(expense_group)
    expense_report_lineitems  = ExpenseReportLineitem.create_expense_report_lineitems(expense_group, workspace_general_settings)

    for expense_report_lineitem in expense_report_lineitems:
        assert expense_report_lineitem.amount == 11.0
        assert expense_report_lineitem.memo == 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/main/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'
        assert expense_report_lineitem.billable == True

    assert expense_report.currency == 'USD'
    assert expense_report.transaction_date.split('T')[0] == datetime.now().strftime('%Y-%m-%d')

    try:
        general_mappings.delete()
        expense_report_lineitems  = ExpenseReportLineitem.create_expense_report_lineitems(expense_group, workspace_general_settings)
    except:
        logger.info('General mapping not found')


def test_create_journal_entry(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.use_intacct_employee_locations = True
    general_mappings.use_intacct_employee_departments = True
    general_mappings.save()

    journal_entry = JournalEntry.create_journal_entry(expense_group)
    journal_entry_lineitems  = JournalEntryLineitem.create_journal_entry_lineitems(expense_group, workspace_general_settings)

    for journal_entry_lineitem in journal_entry_lineitems:
        assert journal_entry_lineitem.amount == 11.0
        assert journal_entry_lineitem.memo == 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/main/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'

    assert journal_entry.currency == 'USD'
    assert journal_entry.transaction_date.split('T')[0] == datetime.now().strftime('%Y-%m-%d')

    try:
        general_mappings.delete()
        journal_entry_lineitems  = JournalEntryLineitem.create_journal_entry_lineitems(expense_group, workspace_general_settings)
    except:
        logger.info('General mapping not found')


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
    general_mappings.use_intacct_employee_locations = True
    general_mappings.use_intacct_employee_departments = True
    general_mappings.save()

    charge_card_transaction = ChargeCardTransaction.create_charge_card_transaction(expense_group)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    charge_card_transaction_lineitems = ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(expense_group, workspace_general_settings)

    for charge_card_transaction_lineitem in charge_card_transaction_lineitems:
        assert charge_card_transaction_lineitem.amount == 21.0
        
    assert charge_card_transaction.currency == 'USD'
    assert charge_card_transaction.transaction_date.split('T')[0] == '2022-09-20'

    expense_group = ExpenseGroup.objects.get(id=2)

    vendor = DestinationAttribute.objects.filter(
        value__iexact='Ashwin', attribute_type='VENDOR', workspace_id=expense_group.workspace_id
    ).first()
    vendor.value = 'sample'
    vendor.save()

    description = expense_group.description

    mapping = EmployeeMapping.objects.filter(
        source_employee__value=description.get('employee_email'),
        workspace_id=expense_group.workspace_id
    ).first()
    mapping.destination_card_account = None
    mapping.save()

    charge_card_transaction = ChargeCardTransaction.create_charge_card_transaction(expense_group)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    charge_card_transaction_lineitems = ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(expense_group, workspace_general_settings)

    for charge_card_transaction_lineitem in charge_card_transaction_lineitems:
        assert charge_card_transaction_lineitem.amount == 11.0
        
    assert charge_card_transaction.currency == 'USD'
    assert charge_card_transaction.transaction_date.split('T')[0] == '2022-09-20'

    try:
        general_mappings.delete()
        charge_card_transaction_lineitems = ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(expense_group, workspace_general_settings)
    except:
        logger.info('General mapping not found')


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

    mapping = Mapping.objects.filter(
        source_type='PROJECT',
        workspace_id=expense_group.workspace_id
    ).first()

    mapping.destination_type = 'PROJECT'
    mapping.source = ExpenseAttribute.objects.get(value=expenses[0].project)
    mapping.save()
    project_id = get_project_id_or_none(expense_group, expenses[0], general_mapping)

    assert project_id == '10061'

    mapping_setting = MappingSetting.objects.filter( 
        workspace_id=expense_group.workspace_id, 
        destination_field='PROJECT' 
    ).first() 

    mapping_setting.source_field = 'TEAM_2_POSTMAN'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_project_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '10061'

    mapping_setting.source_field = 'COST_CENTER'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_project_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '10061'


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

    mapping_setting = MappingSetting.objects.filter( 
        workspace_id=expense_group.workspace_id, 
    ).first()

    mapping_setting.destination_field = 'DEPARTMENT'
    mapping_setting.save()

    mapping_setting.source_field = 'PROJECT'
    mapping_setting.save()

    mapping = Mapping.objects.filter(
        source_type='PROJECT',
        workspace_id=expense_group.workspace_id
    ).first()

    for lineitem in expenses:
        mapping.destination_type = 'DEPARTMENT'
        mapping.source = ExpenseAttribute.objects.get(value=lineitem.project)
        mapping.save()
        location_id = get_department_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '10061'


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
    mapping = Mapping.objects.filter(
        source_type='PROJECT',
        workspace_id=expense_group.workspace_id
    ).first()

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
    
    for lineitem in expenses:
        mapping.destination_type = 'CUSTOMER'
        mapping.source = ExpenseAttribute.objects.get(value=lineitem.project)
        mapping.save()
        location_id = get_customer_id_or_none(expense_group, lineitem, general_mapping, '')
        assert location_id == '10061'

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

    mapping = Mapping.objects.filter(
        source_type='PROJECT',
        workspace_id=expense_group.workspace_id
    ).first()
    for lineitem in expenses:
        mapping.destination_type = 'CLASS'
        mapping.source = ExpenseAttribute.objects.get(value=lineitem.project)
        mapping.save()
        location_id = get_class_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '10061'

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


def test_get_user_defined_dimension_object(mocker, db):
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

    mapping_setting = MappingSetting.objects.filter( 
        workspace_id=expense_group.workspace_id, 
        destination_field='PROJECT' 
    ).first()

    mapping_setting.source_field = 'PROJECT'
    mapping_setting.destination_field = 'CLASS'
    mapping_setting.save()

    mapping = Mapping.objects.filter(
        source_type='PROJECT',
        workspace_id=expense_group.workspace_id
    ).first()

    for lineitem in expenses:
        mapping.destination_type = 'CLASS'
        mapping.source = ExpenseAttribute.objects.get(value=lineitem.project)
        mapping.save()

        location_id = get_user_defined_dimension_object(expense_group, lineitem)
        assert location_id == [{'GLDIMPROJECT': '10061'}]

    mapping_setting.source_field = 'TEAM_2_POSTMAN'
    mapping_setting.save()

    for lineitem in expenses:
        location_id = get_user_defined_dimension_object(expense_group, lineitem)
        assert location_id == []

    mapping_setting.source_field = 'COST_CENTER'
    mapping_setting.save()
    for lineitem in expenses:
        location_id = get_user_defined_dimension_object(expense_group, lineitem)
        assert location_id == []


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

    workspace = Workspace.objects.get(id=workspace_id)
    workspace.cluster_domain = ''
    workspace.save()

    for lineitem in expenses:
        category = lineitem.category if lineitem.category == lineitem.sub_category else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)
    
        expense_purpose = get_expense_purpose(workspace_id, lineitem, category, workspace_general_settings)
        assert expense_purpose == 'ashwin.t@fyle.in - Food / None - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/main/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'


def test_get_transaction_date(db):
    expense_group = ExpenseGroup.objects.get(id=1)

    approved_at = {'spent_at': '2000-09-14'}
    expense_group.description.update(approved_at)

    transaction_date = get_transaction_date(expense_group).split('T')[0]
    assert transaction_date <= datetime.now().strftime('%Y-%m-%d')

    expense_group.description.pop('spent_at')

    approved_at = {'approved_at': '2000-09-14'}
    expense_group.description.update(approved_at)

    transaction_date = get_transaction_date(expense_group).split('T')[0]
    assert transaction_date <= datetime.now().strftime('%Y-%m-%d')

    verified_at = {'verified_at': '2000-09-14'}
    expense_group.description.pop('approved_at')
    expense_group.description.update(verified_at)

    transaction_date = get_transaction_date(expense_group).split('T')[0]
    assert transaction_date <= datetime.now().strftime('%Y-%m-%d')

    last_spent_at = {'last_spent_at': '2000-09-14'}
    expense_group.description.pop('verified_at')
    expense_group.description.update(last_spent_at)

    transaction_date = get_transaction_date(expense_group).split('T')[0]
    assert transaction_date <= datetime.now().strftime('%Y-%m-%d')


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

    mapping = Mapping.objects.filter(
        source_type='PROJECT',
        workspace_id=expense_group.workspace_id
    ).first()

    for lineitem in expenses:
        mapping.destination_type = 'LOCATION'
        mapping.source = ExpenseAttribute.objects.get(value=lineitem.project)
        mapping.save()
        location_id = get_location_id_or_none(expense_group, lineitem, general_mapping)
        assert location_id == '10061'
    
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


def test_get_memo(db):
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    expense_group.description.update({'settlement_id': 'setqwcKcC9q1k'})

    expense_group_settings: ExpenseGroupSettings = ExpenseGroupSettings.objects.get( 
        workspace_id=expense_group.workspace_id 
    )
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    expense_group_settings.save()

    get_memo(expense_group, '')