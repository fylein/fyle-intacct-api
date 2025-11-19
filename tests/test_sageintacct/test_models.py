import logging
from datetime import datetime

from fyle_accounting_mappings.models import DestinationAttribute, EmployeeMapping, ExpenseAttribute, Mapping, MappingSetting

from apps.fyle.models import ExpenseGroup, ExpenseGroupSettings
from apps.mappings.models import GeneralMapping
from apps.sage_intacct.models import (
    APPayment,
    APPaymentLineitem,
    Bill,
    BillLineitem,
    ChargeCardTransaction,
    ChargeCardTransactionLineitem,
    CostType,
    ExpenseReport,
    ExpenseReportLineitem,
    JournalEntry,
    JournalEntryLineitem,
    SageIntacctReimbursement,
    SageIntacctReimbursementLineitem,
    get_allocation_id_or_none,
    get_ccc_account_id,
    get_class_id_or_none,
    get_cost_type_id_or_none,
    get_customer_id_or_none,
    get_department_id_or_none,
    get_intacct_employee_object,
    get_item_id_or_none,
    get_location_id_or_none,
    get_memo,
    get_memo_or_purpose,
    get_project_id_or_none,
    get_task_id_or_none,
    get_tax_code_id_or_none,
    get_transaction_date,
    get_user_defined_dimension_object,
)
from apps.sage_intacct.tasks import get_or_create_credit_card_vendor
from apps.workspaces.models import Configuration, SageIntacctCredential, Workspace

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def test_create_bill(db, create_expense_group_expense, create_cost_type, create_dependent_field_setting):
    """
    Test create bill
    """
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
        assert bill_lineitem.billable == None

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
    except Exception:
        logger.info('General mapping not found')


def test_expense_report(db):
    """
    Test create expense report
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.use_intacct_employee_locations = True
    general_mappings.use_intacct_employee_departments = True
    general_mappings.save()

    expense_report = ExpenseReport.create_expense_report(expense_group)
    expense_report_lineitems = ExpenseReportLineitem.create_expense_report_lineitems(expense_group, workspace_general_settings)

    for expense_report_lineitem in expense_report_lineitems:
        assert expense_report_lineitem.amount == 11.0
        assert expense_report_lineitem.memo == 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txCqLqsEnAjf&org_id=or79Cob97KSh'
        assert expense_report_lineitem.billable == True

    assert expense_report.currency == 'USD'
    assert expense_report.transaction_date.split('T')[0] == datetime.now().strftime('%Y-%m-%d')

    try:
        general_mappings.delete()
        expense_report_lineitems = ExpenseReportLineitem.create_expense_report_lineitems(expense_group, workspace_general_settings)
    except Exception:
        logger.info('General mapping not found')


def test_create_journal_entry(db, mocker, create_expense_group_expense, create_cost_type, create_dependent_field_setting):
    """
    Test create journal entry
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.use_intacct_employee_locations = True
    general_mappings.use_intacct_employee_departments = True
    general_mappings.save()

    journal_entry = JournalEntry.create_journal_entry(expense_group)
    sage_intacct_connection = mocker.patch('apps.sage_intacct.utils.SageIntacctConnector')
    sage_intacct_connection.return_value = mocker.Mock()
    journal_entry_lineitems = JournalEntryLineitem.create_journal_entry_lineitems(expense_group, workspace_general_settings, sage_intacct_connection)

    for journal_entry_lineitem in journal_entry_lineitems:
        assert journal_entry_lineitem.amount == 11.0
        assert journal_entry_lineitem.memo == 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txCqLqsEnAjf&org_id=or79Cob97KSh'

    assert journal_entry.currency == 'USD'
    assert journal_entry.transaction_date.split('T')[0] == datetime.now().strftime('%Y-%m-%d')

    try:
        general_mappings.delete()
        journal_entry_lineitems = JournalEntryLineitem.create_journal_entry_lineitems(expense_group, workspace_general_settings, sage_intacct_connection)
    except Exception:
        logger.info('General mapping not found')


def test_create_ap_payment(db):
    """
    Test create ap payment
    """
    expense_group = ExpenseGroup.objects.get(id=1)

    ap_payment = APPayment.create_ap_payment(expense_group)

    ap_payment_lineitems = APPaymentLineitem.create_ap_payment_lineitems(expense_group, '3032')

    for ap_payment_lineitem in ap_payment_lineitems:
        assert ap_payment_lineitem.amount == 21.0

    assert ap_payment.currency == 'USD'
    assert ap_payment.vendor_id == 'Ashwin'


def test_create_charge_card_transaction(mocker, db, create_expense_group_expense, create_cost_type, create_dependent_field_setting):
    """
    Test create charge card transaction
    """
    mocker.patch(
        'apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor',
        return_value=DestinationAttribute.objects.get(id=633)
    )
    workspace_id = 1

    configuration = Configuration.objects.get(workspace_id=workspace_id)

    expense_group = ExpenseGroup.objects.get(id=1)
    expense_group.description.update({'employee_email': 'user4444@fyleforgotham.in'})
    expense_group.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.default_charge_card_id = 'sample'
    general_mappings.use_intacct_employee_locations = True
    general_mappings.use_intacct_employee_departments = True
    general_mappings.save()

    merchant = expense_group.expenses.first().vendor
    vendor = get_or_create_credit_card_vendor(expense_group.workspace_id, configuration, merchant)

    charge_card_transaction = ChargeCardTransaction.create_charge_card_transaction(expense_group, vendor.destination_id)
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

    charge_card_transaction = ChargeCardTransaction.create_charge_card_transaction(expense_group, vendor.destination_id)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    charge_card_transaction_lineitems = ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(expense_group, workspace_general_settings)

    for charge_card_transaction_lineitem in charge_card_transaction_lineitems:
        assert charge_card_transaction_lineitem.amount == 11.0

    assert charge_card_transaction.currency == 'USD'
    assert charge_card_transaction.transaction_date.split('T')[0] == '2022-09-20'

    # Test billable field
    expense_group = ExpenseGroup.objects.get(id=1)
    workspace_id = expense_group.workspace_id
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    expense = expense_group.expenses.first()
    expense.billable = True
    expense.save()

    mocker.patch(
        'apps.sage_intacct.models.get_item_id_or_none',
        return_value='123'
    )

    mocker.patch(
        'apps.sage_intacct.models.get_customer_id_or_none',
        return_value='123'
    )

    charge_card_transaction_lineitems = ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(expense_group, workspace_general_settings)

    assert charge_card_transaction_lineitems[0].billable

    mocker.patch(
        'apps.sage_intacct.models.get_customer_id_or_none',
        return_value=None
    )
    charge_card_transaction_lineitems = ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(expense_group, workspace_general_settings)

    assert not charge_card_transaction_lineitems[0].billable

    try:
        general_mappings.delete()
        charge_card_transaction_lineitems = ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(expense_group, workspace_general_settings)
    except Exception:
        logger.info('General mapping not found')


def test_create_sage_intacct_reimbursement(db):
    """
    Test create sage intacct reimbursement
    """
    expense_group = ExpenseGroup.objects.get(id=1)
    sage_intacct_reimbursement = SageIntacctReimbursement.create_sage_intacct_reimbursement(expense_group)

    sage_intacct_reimbursement_lineitems = SageIntacctReimbursementLineitem.create_sage_intacct_reimbursement_lineitems(expense_group, '3032')

    for sage_intacct_reimbursement_lineitem in sage_intacct_reimbursement_lineitems:
        assert sage_intacct_reimbursement_lineitem.amount == 21.0

    assert sage_intacct_reimbursement.payment_description == 'Payment for Expense Report by ashwin.t@fyle.in'


def test_get_project_id_or_none(mocker, db):
    """
    Test get project id or none
    """
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
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.list_all',
        return_value=[]
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
    """
    Test get department id or none
    """
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
    """
    Test get tax code id or none
    """
    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    for lineitem in expenses:
        location_id = get_tax_code_id_or_none(expense_group, lineitem)
        assert location_id == None


def test_get_customer_id_or_none(mocker, db):
    """
    Test get customer id or none
    """
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
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.list_all',
        return_value=[]
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
    """
    Test get class id or none
    """
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
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.list_all',
        return_value=[]
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
    """
    Test get user defined dimension object
    """
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
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.list_all',
        return_value=[]
    )
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
    """
    Test get expense purpose
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)
    expenses = expense_group.expenses.all()

    for lineitem in expenses:
        category = lineitem.category if lineitem.category == lineitem.sub_category else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        expense_purpose = get_memo_or_purpose(workspace_id, lineitem, category, workspace_general_settings, export_table=ExpenseReport)

        assert expense_purpose == 'ashwin.t@fyle.in - Food / None - 2022-09-20 - C/2022/09/R/22 - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txCqLqsEnAjf&org_id=or79Cob97KSh'

    workspace = Workspace.objects.get(id=workspace_id)
    workspace.cluster_domain = ''
    workspace.save()

    for lineitem in expenses:
        category = lineitem.category if lineitem.category == lineitem.sub_category else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        expense_purpose = get_memo_or_purpose(workspace_id, lineitem, category, workspace_general_settings, export_table=ExpenseReport)
        assert expense_purpose == 'ashwin.t@fyle.in - Food / None - 2022-09-20 - C/2022/09/R/22 - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txCqLqsEnAjf&org_id=or79Cob97KSh'


def test_get_memo_or_purpose_top_level(db):
    """
    Test get memo or purpose with is_top_level=True
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    # Set up top_level_memo_structure
    workspace_general_settings.top_level_memo_structure = ['employee_email', 'employee_name', 'claim_number']
    workspace_general_settings.save()

    expenses = expense_group.expenses.all()

    for lineitem in expenses:
        category = lineitem.category if lineitem.category == lineitem.sub_category else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        # Test with is_top_level=True
        top_level_memo = get_memo_or_purpose(workspace_id, lineitem, category, workspace_general_settings, is_top_level=True, export_table=ExpenseReport)

        # Expected format: employee_email - employee_name - group_by
        # Since expense_group_settings.description has claim_number, group_by should be claim_number
        expected_memo = 'ashwin.t@fyle.in -  - C/2022/09/R/22'
        assert top_level_memo == expected_memo

    # Test with different top_level_memo_structure
    workspace_general_settings.top_level_memo_structure = ['employee_name', 'claim_number']
    workspace_general_settings.save()

    for lineitem in expenses:
        category = lineitem.category if lineitem.category == lineitem.sub_category else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        top_level_memo = get_memo_or_purpose(workspace_id, lineitem, category, workspace_general_settings, is_top_level=True, export_table=ExpenseReport)

        # Expected format: employee_name - group_by
        expected_memo = ' - C/2022/09/R/22'
        assert top_level_memo == expected_memo

    # Test with empty top_level_memo_structure (should fall back to regular memo_structure)
    workspace_general_settings.top_level_memo_structure = []
    workspace_general_settings.save()

    for lineitem in expenses:
        category = lineitem.category if lineitem.category == lineitem.sub_category else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        top_level_memo = get_memo_or_purpose(workspace_id, lineitem, category, workspace_general_settings, is_top_level=False, export_table=ExpenseReport)

        # Should fall back to regular memo structure
        expected_memo = 'ashwin.t@fyle.in - Food / None - 2022-09-20 - C/2022/09/R/22 - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txCqLqsEnAjf&org_id=or79Cob97KSh'
        assert top_level_memo == expected_memo

    # Test when expense_group_settings has expense_number instead of claim_number
    expense_group = ExpenseGroup.objects.get(workspace_id=workspace_id, expenses__in=expenses)

    # Modify description to not have claim_number
    expense_group.description = {'expense_number': 'E/2022/09/T/22'}
    expense_group.save()

    workspace_general_settings.top_level_memo_structure = ['employee_email', 'expense_number']
    workspace_general_settings.save()

    for lineitem in expenses:
        category = lineitem.category if lineitem.category == lineitem.sub_category else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        top_level_memo = get_memo_or_purpose(workspace_id, lineitem, category, workspace_general_settings, is_top_level=True, export_table=ExpenseReport)

        # Should use expense_number as group_by
        expected_memo = 'ashwin.t@fyle.in - E/2022/09/T/22'
        assert top_level_memo == expected_memo


def test_get_transaction_date(db):
    """
    Test get transaction date
    """
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
    """
    Test get location id or none
    """
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
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.list_all',
        return_value=[]
    )
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    expenses = expense_group.expenses.all()

    general_mapping = GeneralMapping.objects.get(workspace_id=workspace_id)

    mapping_setting = MappingSetting.objects.filter(
        workspace_id=expense_group.workspace_id,
        destination_field='PROJECT'
    ).first()

    mapping_setting.destination_field = 'LOCATION'
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
    """
    Test get intacct employee object
    """
    expense_group = ExpenseGroup.objects.get(id=1)

    default_employee_object = get_intacct_employee_object('email', expense_group)
    assert default_employee_object == 'ashwin.t@fyle.in'


def test_get_memo(db):
    """
    Test get memo
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    expense_group.description.update({'settlement_id': 'setqwcKcC9q1k'})

    expense_group_settings: ExpenseGroupSettings = ExpenseGroupSettings.objects.get(
        workspace_id=expense_group.workspace_id
    )
    expense_group_settings.reimbursable_export_date_type = 'spent_at'
    expense_group_settings.save()

    get_memo(expense_group, ExportTable=Bill, workspace_id=workspace_id)

    expense_group = ExpenseGroup.objects.get(id=2)
    workspace_id = expense_group.workspace.id

    config = Configuration.objects.get(workspace_id=workspace_id)
    config.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    config.save()

    expense_group.description['employee_email'] = 'abc@def.co'
    expense_group.save()

    memo = get_memo(expense_group, ExportTable=ChargeCardTransaction, workspace_id=workspace_id)
    assert memo == 'Corporate Card Expense by abc@def.co'

    ChargeCardTransaction.create_charge_card_transaction(expense_group)

    memo = get_memo(expense_group, ExportTable=ChargeCardTransaction, workspace_id=workspace_id)
    assert memo == 'Corporate Card Expense by abc@def.co - 1'

    for i in range(3):
        expense_group = ExpenseGroup.objects.get(id=i + 1)
        expense_group.description['employee_email'] = 'abc@def.co'
        expense_group.save()

        ChargeCardTransaction.create_charge_card_transaction(expense_group)

    memo = get_memo(expense_group, ExportTable=ChargeCardTransaction, workspace_id=workspace_id)
    assert memo == 'Corporate Card Expense by abc@def.co - 3'


def test_get_item_id_or_none(db, mocker):
    """
    Test get item id or none
    """
    workspace_id = 1

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    expense_group = ExpenseGroup.objects.get(id=1)

    expense = expense_group.expenses.first()

    general_mappings.default_item_id = None
    general_mappings.save()

    item_id = get_item_id_or_none(expense_group, expense, general_mappings)

    assert item_id == None

    general_mappings.default_item_id = '1234'
    general_mappings.save()

    item_id = get_item_id_or_none(expense_group, expense, general_mappings)

    assert item_id == general_mappings.default_item_id

    item_setting: MappingSetting = MappingSetting.objects.filter(workspace_id=workspace_id).first()
    item_setting.source_field = 'PROJECT'
    item_setting.destination_field = 'ITEM'
    item_setting.save()

    item_id = get_item_id_or_none(expense_group, expense, general_mappings)

    assert item_id == general_mappings.default_item_id

    expense_attribute = ExpenseAttribute.objects.filter(
        attribute_type = 'PROJECT',
        value = 'Aaron Abbott'
    ).first()

    mapping = Mapping.objects.first()
    mapping.destination_type = 'ITEM'
    mapping.source_type = 'PROJECT'
    mapping.source = expense_attribute
    mapping.workspace_id = general_mappings.workspace
    mapping.save()

    source_value = expense.project

    mapping = Mapping.objects.filter(
        source_type=item_setting.source_field,
        destination_type='ITEM',
        source__value=source_value,
        workspace_id=expense_group.workspace_id
    ).first()

    item_id = get_item_id_or_none(expense_group, expense, general_mappings)

    assert item_id == mapping.destination.destination_id

    item_setting: MappingSetting = MappingSetting.objects.filter(workspace_id=workspace_id).first()
    item_setting.source_field = 'COST_CENTER'
    item_setting.destination_field = 'ITEM'
    item_setting.save()

    expense_attribute = ExpenseAttribute.objects.filter(
        attribute_type = 'COST_CENTER'
    ).first()

    mapping = Mapping.objects.first()
    mapping.destination_type = 'ITEM'
    mapping.source_type = 'COST_CENTER'
    mapping.source = expense_attribute
    mapping.workspace_id = general_mappings.workspace
    mapping.save()

    expense.cost_center = expense_attribute.value
    expense.save()

    source_value = expense.cost_center

    mapping = Mapping.objects.filter(
        source_type=item_setting.source_field,
        destination_type='ITEM',
        source__value=source_value,
        workspace_id=expense_group.workspace_id
    ).first()

    item_id = get_item_id_or_none(expense_group, expense, general_mappings)

    assert item_id == mapping.destination.destination_id

    item_setting: MappingSetting = MappingSetting.objects.filter(workspace_id=workspace_id).first()
    item_setting.source_field = 'EMPLOYEE'
    item_setting.destination_field = 'ITEM'
    item_setting.save()

    expense_attribute = ExpenseAttribute.objects.first()
    expense_attribute.attribute_type = 'EMPLOYEE'
    expense_attribute.display_name = 'Employee'
    expense_attribute.value = 'Los'
    expense_attribute.save()

    mapping = Mapping.objects.first()
    mapping.destination_type = 'ITEM'
    mapping.source_type = 'EMPLOYEE'
    mapping.source = expense_attribute
    mapping.workspace_id = general_mappings.workspace
    mapping.save()

    expense.custom_properties[expense_attribute.display_name] = expense_attribute.value
    expense.save()

    source_value = expense.custom_properties.get(expense_attribute.display_name, None)

    mapping = Mapping.objects.filter(
        source_type=item_setting.source_field,
        destination_type='ITEM',
        source__value=source_value,
        workspace_id=expense_group.workspace_id
    ).first()

    item_id = get_item_id_or_none(expense_group, expense, general_mappings)

    assert item_id == mapping.destination.destination_id


def test_get_ccc_account_id(db, mocker):
    """
    Test get ccc account id
    """
    workspace_id = 1

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION'
    configuration.save()

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    expense_group = ExpenseGroup.objects.get(id=1)

    expense = expense_group.expenses.first()
    expense.corporate_card_id = 900
    expense.save()

    expense_attribute = ExpenseAttribute.objects.first()
    expense_attribute.source_id = expense.corporate_card_id
    expense_attribute.save()

    mapping = Mapping.objects.first()
    mapping.source_type = 'CORPORATE_CARD'
    mapping.destination_type = 'CHARGE_CARD_NUMBER'
    mapping.source = expense_attribute
    mapping.workspace_id = general_mappings.workspace
    mapping.save()

    cct_id = get_ccc_account_id(general_mappings, expense, expense_group.description)

    assert cct_id == mapping.destination.destination_id

    mapping.source_type = 'COST_CENTER'
    mapping.destination_type = 'COST_CENTER'
    mapping.save()

    expense_attribute.value = expense_group.description.get('employee_email')

    destination_mapping = DestinationAttribute.objects.first()
    destination_mapping.destination_id = 12345
    destination_mapping.save()

    employee_mapping = EmployeeMapping.objects.first()
    employee_mapping.workspace_id = general_mappings.workspace
    employee_mapping.source_employee = expense_attribute
    employee_mapping.destination_card_account = destination_mapping
    employee_mapping.save()
    employee_mapping: EmployeeMapping = EmployeeMapping.objects.filter(
        source_employee__value=expense_group.description.get('employee_email'),
        workspace_id=general_mappings.workspace
    ).first()

    cct_id = get_ccc_account_id(general_mappings, expense, expense_group.description)

    assert cct_id == employee_mapping.destination_card_account.destination_id

    expense.corporate_card_id = None
    expense.save()

    employee_mapping.destination_card_account = None
    employee_mapping.save()

    cct_id = get_ccc_account_id(general_mappings, expense, expense_group.description)

    assert cct_id == general_mappings.default_charge_card_id


def test_get_cost_type_id_or_none(db, create_expense_group_expense, create_cost_type, create_dependent_field_setting):
    """
    Test get cost type id or none
    """
    expense_group, expense = create_expense_group_expense
    cost_type_id = get_cost_type_id_or_none(expense_group, expense, create_dependent_field_setting, 'pro1', 'task1')

    assert cost_type_id == 'cost1'


def test_get_task_id_or_none(db, create_expense_group_expense, create_cost_type, create_dependent_field_setting):
    """
    Test get task id or none
    """
    expense_group, expense = create_expense_group_expense
    task_id = get_task_id_or_none(expense_group, expense, create_dependent_field_setting, 'pro1')

    assert task_id == 'task1'


def test_cost_type_bulk_create_or_update(db, create_cost_type, create_dependent_field_setting):
    """
    Test cost type bulk create or update
    """
    cost_types = [
        {
            'RECORDNO': '2342341',
            'PROJECTKEY': 'pro1234',
            'PROJECTID': 'pro1234',
            'PROJECTNAME': 'pro1234',
            'TASKKEY': 'task1234',
            'TASKID': 'task1234',
            'TASKNAME': 'task2341',
            'COSTTYPEID': 'cost2341',
            'NAME': 'cost12342',
            'STATUS': 'Active'
        },
        {
            'RECORDNO': '34234',
            'PROJECTKEY': 34,
            'PROJECTID': 'pro1',
            'PROJECTNAME': 'proUpdated',
            'TASKKEY': 34,
            'TASKNAME': 'task1',
            'STATUS': 'ACTIVE',
            'COSTTYPEID': 'cost1',
            'NAME': 'costUpdated',
            'TASKID': 'task1'
        }
    ]
    existing_cost_type = CostType.objects.get(record_number='34234')
    assert existing_cost_type.name == 'cost'
    assert existing_cost_type.project_name == 'pro'

    CostType.bulk_create_or_update(cost_types, 1)

    assert CostType.objects.filter(record_number='2342341').exists()
    # We would not update only the status and nothing else
    assert CostType.objects.get(record_number='34234').name == 'cost'


def test_get_allocation_or_none(db, mocker):
    """
    Test get allocation or none
    """
    workspace_id = 1
    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)

    expense_group = ExpenseGroup.objects.get(id=1)

    expense = expense_group.expenses.first()

    allocation_id, _ = get_allocation_id_or_none(expense_group=expense_group, lineitem=expense)

    assert allocation_id == None

    allocation_setting: MappingSetting = MappingSetting.objects.filter(workspace_id=workspace_id).first()
    allocation_setting.source_field = 'PROJECT'
    allocation_setting.destination_field = 'ALLOCATION'
    allocation_setting.save()

    expense_attribute = ExpenseAttribute.objects.filter(
        attribute_type = 'PROJECT',
        value = 'Aaron Abbott'
    ).first()

    destination_attribute = DestinationAttribute.objects.create(
        attribute_type='ALLOCATION',
        workspace_id=workspace_id,
        display_name = 'allocation',
        value = 'RENT',
        destination_id = '1',
        active = True,
        detail = {'LOCATIONID':'100'}
    )

    mapping = Mapping.objects.first()
    mapping.destination_type = 'ALLOCATION'
    mapping.source_type = 'PROJECT'
    mapping.destination = destination_attribute
    mapping.source = expense_attribute
    mapping.workspace_id = general_mappings.workspace
    mapping.save()

    source_value = expense.project

    mapping = Mapping.objects.filter(
        source_type=allocation_setting.source_field,
        destination_type='ALLOCATION',
        source__value=source_value,
        workspace_id=expense_group.workspace_id
    ).first()

    allocation_id, _ = get_allocation_id_or_none(expense_group, expense)

    assert allocation_id == mapping.destination.value


def test_bill_with_allocation(db, mocker):
    """
    Test bill with allocation
    """
    workspace_id = 1

    expense_group = ExpenseGroup.objects.get(id=1)
    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.use_intacct_employee_locations = True
    general_mappings.use_intacct_employee_departments = True
    general_mappings.save()

    allocation_setting: MappingSetting = MappingSetting.objects.filter(workspace_id=workspace_id).first()
    allocation_setting.source_field = 'PROJECT'
    allocation_setting.destination_field = 'ALLOCATION'
    allocation_setting.save()

    expense_attribute = ExpenseAttribute.objects.filter(
        attribute_type = 'PROJECT',
        value = 'Aaron Abbott'
    ).first()

    destination_attribute = DestinationAttribute.objects.create(
        attribute_type='ALLOCATION',
        workspace_id=workspace_id,
        display_name = 'allocation',
        value = 'RENT',
        destination_id = '1',
        active = True,
        detail = {'LOCATIONID':'600', 'CLASSID': '600', 'DEPARTMENTID': '300'}
    )

    mapping = Mapping.objects.first()
    mapping.destination_type = 'ALLOCATION'
    mapping.source_type = 'PROJECT'
    mapping.destination = destination_attribute
    mapping.source = expense_attribute
    mapping.workspace_id = general_mappings.workspace
    mapping.save()

    bill = Bill.create_bill(expense_group)
    bill_lineitems = BillLineitem.create_bill_lineitems(expense_group, workspace_general_settings)

    for bill_lineitem in bill_lineitems:
        assert bill_lineitem.location_id is None
        assert bill_lineitem.class_id is None
        assert bill_lineitem.department_id is None
        assert bill_lineitem.item_id == '1012'
        assert bill_lineitem.amount == 21.0
        assert bill_lineitem.billable == None
        assert bill_lineitem.allocation_id == 'RENT'

    assert bill.currency == 'USD'
    assert bill.transaction_date.split('T')[0] == datetime.now().strftime('%Y-%m-%d')
    assert bill.vendor_id == 'Ashwin'


def test_bill_with_allocation_and_user_dimensions(db, mocker, create_expense_group_for_allocation):
    """
    Test bill with allocation and user dimensions
    """
    workspace_id = 1

    expense_group, expense = create_expense_group_for_allocation

    workspace_general_settings = Configuration.objects.get(workspace_id=workspace_id)

    general_mappings = GeneralMapping.objects.get(workspace_id=workspace_id)
    general_mappings.use_intacct_employee_locations = True
    general_mappings.use_intacct_employee_departments = True
    general_mappings.save()

    mapping_setting = MappingSetting.objects.filter(
        workspace_id=expense_group.workspace_id,
        destination_field='TAX_CODE'
    ).first()

    expense_attribute = ExpenseAttribute.objects.filter(
        attribute_type = 'COST_CENTER',
        value = 'Izio',
        workspace_id=1
    ).first()

    destination_attribute = DestinationAttribute.objects.create(
        attribute_type='ALLOCATION',
        workspace_id=workspace_id,
        display_name = 'allocation',
        value = 'RENT',
        destination_id = '1',
        active = True,
        detail = {'GLDIMPROJECT': '2024'}
    )

    mapping_setting.source_field = 'COST_CENTER'
    mapping_setting.destination_field = 'ALLOCATION'
    mapping_setting.save()

    mapping = Mapping.objects.filter(
        source_type='TAX_GROUP',
        workspace_id=expense_group.workspace_id
    ).first()

    mapping.destination_type = 'ALLOCATION'
    mapping.source_type = 'COST_CENTER'
    mapping.destination = destination_attribute
    mapping.source = expense_attribute
    mapping.save()

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

    mapping.destination_type = 'CLASS'
    mapping.source = ExpenseAttribute.objects.get(value=expense.project)
    mapping.save()

    location_id = get_user_defined_dimension_object(expense_group, expense)
    assert location_id == [{'GLDIMPROJECT': '10061'}]

    _ = Bill.create_bill(expense_group)
    bill_lineitems = BillLineitem.create_bill_lineitems(expense_group, workspace_general_settings)

    for bill_lineitem in bill_lineitems:
        assert bill_lineitem.user_defined_dimensions == []
        assert bill_lineitem.project_id == '10061'
        assert bill_lineitem.location_id == '600'
        assert bill_lineitem.class_id == '10061'
        assert bill_lineitem.department_id == '300'
        assert bill_lineitem.customer_id == '10061'
        assert bill_lineitem.item_id == '1012'
        assert bill_lineitem.allocation_id == 'RENT'


def test_post_bill_with_vendor_mapping(mocker, db):
    """
    Test create_bill success with vendor mapping
    """
    expense_group = ExpenseGroup.objects.get(id=1)
    expense_group.fund_source = 'CCC'
    expense_group.save()
    expenses = expense_group.expenses.all()

    expenses.update(
        fund_source='CCC',
        corporate_card_id='baccjpfvrtsPg9'
    )

    vendor = DestinationAttribute.objects.create(
        value='abcd',
        destination_id='ABCD',
        attribute_type='VENDOR',
        display_name='Vendor',
        workspace_id=1,
        active=True,
        detail={
            'email': 'vendor123@fyle.in'
        }
    )

    corporate_card = ExpenseAttribute.objects.create(
        attribute_type='CORPORATE_CARD',
        value='American Express - 61662',
        display_name='Corporate Card',
        source_id='baccjpfvrtsPg9',
        workspace_id=1,
        active=True
    )

    _ = Mapping.objects.create(
        workspace_id=1,
        source_id=corporate_card.id,
        destination_id=vendor.id,
        source_type='CORPORATE_CARD',
        destination_type='VENDOR',
    )

    bill = Bill.create_bill(expense_group)
    assert bill.vendor_id == 'ABCD'


def test_post_bill_with_no_vendor_mapping(mocker, db):
    """
    Test create_bill success with no corporate card vendor mapping
    """
    expense_group = ExpenseGroup.objects.get(id=1)
    expense_group.fund_source = 'CCC'
    expense_group.save()
    expenses = expense_group.expenses.all()

    expenses.update(
        fund_source='CCC',
        corporate_card_id='baccjpfvrtsPg9'
    )

    bill = Bill.create_bill(expense_group)
    general_mappings = GeneralMapping.objects.get(workspace_id=1)
    assert bill.vendor_id == general_mappings.default_ccc_vendor_id


def test_get_active_sage_intacct_credentials(mocker):
    """
    Test get active sage intacct credentials
    """
    mock_cred = mocker.Mock()
    mock_get = mocker.patch('apps.workspaces.models.SageIntacctCredential.objects.get', return_value=mock_cred)
    result = SageIntacctCredential.get_active_sage_intacct_credentials(123)
    mock_get.assert_called_once_with(workspace_id=123, is_expired=False)
    assert result == mock_cred
