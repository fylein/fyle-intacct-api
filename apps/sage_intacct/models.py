"""
Sage Intacct models
"""
from datetime import datetime
from django.conf import settings
from django.db.models import Q,JSONField
from django.db import models
from django.utils.module_loading import import_string

from fyle_accounting_mappings.models import Mapping, MappingSetting, DestinationAttribute, CategoryMapping, \
    EmployeeMapping

from apps.fyle.models import ExpenseGroup, Expense, ExpenseAttribute, Reimbursement, ExpenseGroupSettings, DependentFieldSetting
from apps.mappings.models import GeneralMapping

from apps.workspaces.models import Configuration, Workspace, FyleCredential, SageIntacctCredential
from typing import Dict, List, Union


allocation_mapping = {
    'LOCATIONID': 'location_id',
    'DEPARTMENTID': 'department_id',
    'CLASSID': 'class_id',
    'CUSTOMERID': 'customer_id',
    'ITEMID': 'item_id',
    'TASKID': 'task_id',
    'COSTTYPEID': 'cost_type_id',
    'PROJECTID': 'project_id'
}

def get_allocation_id_or_none(expense_group: ExpenseGroup, lineitem: Expense):
    allocation_id = None
    allocation_detail = None

    allocation_setting: MappingSetting = MappingSetting.objects.filter(
        workspace_id=expense_group.workspace_id,
        destination_field ='ALLOCATION'
    ).first()

    if allocation_setting:
        if allocation_setting.source_field == 'PROJECT':
            source_value = lineitem.project
        elif allocation_setting.source_field == 'COST_CENTER':
            source_value = lineitem.cost_center
        else:
            attribute = ExpenseAttribute.objects.filter(attribute_type=allocation_setting.source_field, workspace_id=expense_group.workspace_id).first()
            source_value = lineitem.custom_properties.get(attribute.display_name, None)

        mapping: Mapping = Mapping.objects.filter(
            source_type=allocation_setting.source_field,
            destination_type='ALLOCATION',
            source__value=source_value,
            workspace_id=expense_group.workspace_id
        ).first()

        if mapping:
            allocation_id = mapping.destination.value
            allocation_detail = mapping.destination.detail
    return allocation_id, allocation_detail


def get_project_id_or_none(expense_group: ExpenseGroup, lineitem: Expense, general_mappings: GeneralMapping):
    project_id = None
    if general_mappings and general_mappings.default_project_id:
        project_id = general_mappings.default_project_id

    project_setting: MappingSetting = MappingSetting.objects.filter(
        workspace_id=expense_group.workspace_id,
        destination_field='PROJECT'
    ).first()

    if project_setting:
        if project_setting.source_field == 'PROJECT':
            source_value = lineitem.project
        elif project_setting.source_field == 'COST_CENTER':
            source_value = lineitem.cost_center
        else:
            attribute = ExpenseAttribute.objects.filter(attribute_type=project_setting.source_field, workspace_id=expense_group.workspace_id).first()
            source_value = lineitem.custom_properties.get(attribute.display_name, None)

        mapping: Mapping = Mapping.objects.filter(
            source_type=project_setting.source_field,
            destination_type='PROJECT',
            source__value=source_value,
            workspace_id=expense_group.workspace_id
        ).first()

        if mapping:
            project_id = mapping.destination.destination_id
    return project_id


def get_department_id_or_none(expense_group: ExpenseGroup, lineitem: Expense, general_mappings: GeneralMapping):
    department_id = None
    source_value = None
    if general_mappings and general_mappings.default_department_id:
        department_id = general_mappings.default_department_id

    department_setting: MappingSetting = MappingSetting.objects.filter(
        workspace_id=expense_group.workspace_id,
        destination_field='DEPARTMENT'
    ).first()

    if department_setting:
        if department_setting.source_field == 'PROJECT':
            source_value = lineitem.project
        elif department_setting.source_field == 'COST_CENTER':
            source_value = lineitem.cost_center
        else:
            attribute = ExpenseAttribute.objects.filter(attribute_type=department_setting.source_field, workspace_id=expense_group.workspace_id).first()
            if attribute:
                source_value = lineitem.custom_properties.get(attribute.display_name, None)

        mapping: Mapping = Mapping.objects.filter(
            source_type=department_setting.source_field,
            destination_type='DEPARTMENT',
            source__value=source_value,
            workspace_id=expense_group.workspace_id
        ).first()

        if mapping:
            department_id = mapping.destination.destination_id
    return department_id


def get_location_id_or_none(expense_group: ExpenseGroup, lineitem: Expense, general_mappings: GeneralMapping):
    location_id = None
    if general_mappings and general_mappings.default_location_id:
        location_id = general_mappings.default_location_id

    location_setting: MappingSetting = MappingSetting.objects.filter(
        workspace_id=expense_group.workspace_id,
        destination_field='LOCATION'
    ).first()

    if location_setting:
        if location_setting.source_field == 'PROJECT':
            source_value = lineitem.project
        elif location_setting.source_field == 'COST_CENTER':
            source_value = lineitem.cost_center
        else:
            attribute = ExpenseAttribute.objects.filter(attribute_type=location_setting.source_field, workspace_id=expense_group.workspace_id).first()
            source_value = lineitem.custom_properties.get(attribute.display_name, None)

        mapping: Mapping = Mapping.objects.filter(
            source_type=location_setting.source_field,
            destination_type='LOCATION',
            source__value=source_value,
            workspace_id=expense_group.workspace_id
        ).first()

        if mapping:
            location_id = mapping.destination.destination_id
    return location_id


def get_customer_id_or_none(expense_group: ExpenseGroup, lineitem: Expense, general_mappings: GeneralMapping, project_id: str):
    customer_id = None

    if project_id:
        project = DestinationAttribute.objects.filter(
            attribute_type='PROJECT',
            destination_id=project_id,
            workspace_id=expense_group.workspace_id
        ).order_by('-updated_at').first()
        if project and project.detail:
            customer_id = project.detail['customer_id']

    if not customer_id:
        customer_setting: MappingSetting = MappingSetting.objects.filter(
            workspace_id=expense_group.workspace_id,
            destination_field='CUSTOMER'
        ).first()

        if customer_setting:
            if customer_setting.source_field == 'PROJECT':
                source_value = lineitem.project
            elif customer_setting.source_field == 'COST_CENTER':
                source_value = lineitem.cost_center
            else:
                attribute = ExpenseAttribute.objects.filter(attribute_type=customer_setting.source_field, workspace_id=expense_group.workspace_id).first()
                source_value = lineitem.custom_properties.get(attribute.display_name, None)

            mapping: Mapping = Mapping.objects.filter(
                source_type=customer_setting.source_field,
                destination_type='CUSTOMER',
                source__value=source_value,
                workspace_id=expense_group.workspace_id
            ).first()

            if mapping:
                customer_id = mapping.destination.destination_id

    return customer_id


def get_item_id_or_none(expense_group: ExpenseGroup, lineitem: Expense, general_mappings: GeneralMapping):
    item_id = None

    item_setting: MappingSetting = MappingSetting.objects.filter(
        workspace_id=expense_group.workspace_id,
        destination_field='ITEM'
    ).first()

    if item_setting:
        if item_setting.source_field == 'PROJECT':
            source_value = lineitem.project
        elif item_setting.source_field == 'COST_CENTER':
            source_value = lineitem.cost_center
        else:
            attribute = ExpenseAttribute.objects.filter(attribute_type=item_setting.source_field, workspace_id=expense_group.workspace_id).first()
            source_value = lineitem.custom_properties.get(attribute.display_name, None)

        mapping: Mapping = Mapping.objects.filter(
            source_type=item_setting.source_field,
            destination_type='ITEM',
            source__value=source_value,
            workspace_id=expense_group.workspace_id
        ).first()
        if mapping:
            item_id = mapping.destination.destination_id
    if item_id is None:
        item_id = general_mappings.default_item_id if general_mappings.default_item_id else None
    return item_id


def get_cost_type_id_or_none(expense_group: ExpenseGroup, lineitem: Expense, dependent_field_setting: DependentFieldSetting, project_id: str, task_id: str):
    cost_type_id = None

    selected_cost_type = lineitem.custom_properties.get(dependent_field_setting.cost_type_field_name, None)
    cost_type = CostType.objects.filter(
        workspace_id=expense_group.workspace_id,
        task_id=task_id,
        project_id=project_id,
        name=selected_cost_type
    ).first()

    if cost_type:
        cost_type_id = cost_type.cost_type_id

    return cost_type_id


def get_task_id_or_none(expense_group: ExpenseGroup, lineitem: Expense, dependent_field_setting: DependentFieldSetting, project_id: str):
    task_id = None

    selected_cost_code = lineitem.custom_properties.get(dependent_field_setting.cost_code_field_name, None)
    cost_type = CostType.objects.filter(
        workspace_id=expense_group.workspace_id,
        task_name=selected_cost_code,
        project_id=project_id
    ).first()

    if cost_type:
        task_id = cost_type.task_id

    return task_id


def get_class_id_or_none(expense_group: ExpenseGroup, lineitem: Expense, general_mappings: GeneralMapping):
    class_id = None
    if general_mappings and general_mappings.default_class_id:
        class_id = general_mappings.default_class_id

    class_setting: MappingSetting = MappingSetting.objects.filter(
        workspace_id=expense_group.workspace_id,
        destination_field='CLASS'
    ).first()

    if class_setting:
        if class_setting.source_field == 'PROJECT':
            source_value = lineitem.project
        elif class_setting.source_field == 'COST_CENTER':
            source_value = lineitem.cost_center
        else:
            attribute = ExpenseAttribute.objects.filter(attribute_type=class_setting.source_field, workspace_id=expense_group.workspace_id).first()
            source_value = lineitem.custom_properties.get(attribute.display_name, None)

        mapping: Mapping = Mapping.objects.filter(
            source_type=class_setting.source_field,
            destination_type='CLASS',
            source__value=source_value,
            workspace_id=expense_group.workspace_id
        ).first()

        if mapping:
            class_id = mapping.destination.destination_id

    return class_id


def get_tax_code_id_or_none(expense_group: ExpenseGroup, lineitem: Expense = None):
    tax_code = None
    mapping: Mapping = Mapping.objects.filter(
        source_type='TAX_GROUP',
        destination_type='TAX_DETAIL',
        source__source_id=lineitem.tax_group_id,
        workspace_id=expense_group.workspace_id
    ).first()
    if mapping:
        tax_code = mapping.destination.destination_id

    return tax_code


def get_transaction_date(expense_group: ExpenseGroup) -> str:
    if 'posted_at' in expense_group.description and expense_group.description['posted_at']:
        return expense_group.description['posted_at']
    elif 'approved_at' in expense_group.description and expense_group.description['approved_at']:
        return expense_group.description['approved_at']
    elif 'verified_at' in expense_group.description and expense_group.description['verified_at']:
        return expense_group.description['verified_at']
    elif 'last_spent_at' in expense_group.description and expense_group.description['last_spent_at']:
        return expense_group.description['last_spent_at']
    elif 'spent_at' in expense_group.description and expense_group.description['spent_at']:
        return expense_group.description['spent_at']
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def get_memo(expense_group: ExpenseGroup,
            ExportTable: Union['Bill', 'ExpenseReport', 'JournalEntry', 'ChargeCardTransaction', 'APPayment', 'SageIntacctReimbursement'],
            workspace_id: int, payment_type: str=None) -> str:
    """
    Get the memo from the description of the expense group.
    :param expense_group: The expense group to get the memo from.
    :param payment_type: The payment type to use in the memo.
    :return: The memo.
    """

    config = Configuration.objects.get(workspace_id=workspace_id)
    if config.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
        memo = 'Corporate Card Expense'
        email = expense_group.description.get('employee_email')
        if email:
            memo = f'{memo} by {email}'

        # Internal ID
        count = ExportTable.objects.filter(memo__contains=memo, expense_group__workspace_id=workspace_id).count()
        if count > 0:
            memo = f'{memo} - {count}'

        return memo

    expense_fund_source = 'Reimbursable expense' if expense_group.fund_source == 'PERSONAL' \
        else 'Corporate Credit Card expense'
    unique_number = None
    count = 0

    if 'settlement_id' in expense_group.description and expense_group.description['settlement_id']:
        # Grouped by payment
        reimbursement = Reimbursement.objects.filter(
            settlement_id=expense_group.description['settlement_id']
        ).values('payment_number').first()

        if reimbursement and reimbursement['payment_number']:
            unique_number = reimbursement['payment_number']
        else:
            unique_number = expense_group.description['settlement_id']

    elif 'claim_number' in expense_group.description and expense_group.description['claim_number']:
        # Grouped by expense report
        unique_number = expense_group.description['claim_number']
    elif 'expense_number' in expense_group.description and expense_group.description['expense_number']:
        unique_number = expense_group.description['expense_number']

    if payment_type:
        # Payments sync
        return 'Payment for {0} - {1}'.format(payment_type, unique_number)
    elif unique_number:
        memo = '{} - {}'.format(expense_fund_source, unique_number)
        expense_group_settings: ExpenseGroupSettings = ExpenseGroupSettings.objects.get(
            workspace_id=expense_group.workspace_id
        )
        if expense_group.fund_source == 'CCC':
            if expense_group_settings.ccc_export_date_type != 'current_date':
                date = get_transaction_date(expense_group)
                date = (datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')).strftime('%d/%m/%Y')
                memo = '{} - {}'.format(memo, date)
        else:
            if expense_group_settings.reimbursable_export_date_type != 'current_date':
                date = get_transaction_date(expense_group)
                date = (datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')).strftime('%d/%m/%Y')
                memo = '{} - {}'.format(memo, date)
        if not payment_type:
            count = ExportTable.objects.filter(memo__contains=memo, expense_group__workspace_id=workspace_id).count()
        if count > 0:
            memo = '{} - {}'.format(memo, count)        

        return memo.replace('\'', '')
    else:
        # Safety addition
        memo = 'Reimbursable expenses by {0}'.format(expense_group.description.get('employee_email')) \
        if expense_group.fund_source == 'PERSONAL' \
            else 'Credit card expenses by {0}'.format(expense_group.description.get('employee_email'))
        count = ExportTable.objects.filter(memo__contains=memo, expense_group__workspace_id=workspace_id).count()
        if count > 0:
            memo = '{} - {}'.format(memo, count)  
        return memo


def get_expense_purpose(workspace_id, lineitem: Expense, category: str, configuration: Configuration) -> str:
    workspace = Workspace.objects.get(id=workspace_id)
    org_id = workspace.fyle_org_id

    if workspace.cluster_domain:
        cluster_domain = workspace.cluster_domain
    else:
        fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
        cluster_domain = fyle_credentials.cluster_domain
        workspace.cluster_domain = cluster_domain
        workspace.save()

    fyle_url = cluster_domain if settings.BRAND_ID == 'fyle' else settings.FYLE_EXPENSE_URL

    expense_link = '{0}/app/admin/#/enterprise/view_expense/{1}?org_id={2}'.format(
        fyle_url, lineitem.expense_id, org_id
    )

    memo_structure = configuration.memo_structure

    details = {
        'employee_email': lineitem.employee_email,
        'merchant': '{0}'.format(lineitem.vendor) if lineitem.vendor else '',
        'category': '{0}'.format(category) if lineitem.category else '',
        'purpose': '{0}'.format(lineitem.purpose) if lineitem.purpose else '',
        'report_number': '{0}'.format(lineitem.claim_number),
        'spent_on': '{0}'.format(lineitem.spent_at.date()) if lineitem.spent_at else '',
        'expense_link': expense_link
    }

    purpose = ''

    for id, field in enumerate(memo_structure):
        if field in details:
            purpose += details[field]
            if id + 1 != len(memo_structure):
                purpose = '{0} - '.format(purpose)

    return purpose


def get_user_defined_dimension_object(expense_group: ExpenseGroup, lineitem: Expense):
    mapping_settings = MappingSetting.objects.filter(workspace_id=expense_group.workspace_id).all()

    user_dimensions = []
    default_expense_attributes = ['CATEGORY', 'EMPLOYEE']
    default_destination_attributes = ['DEPARTMENT', 'LOCATION', 'PROJECT', 'EXPENSE_TYPE', 'CHARGE_CARD_NUMBER',
                                      'VENDOR', 'ACCOUNT', 'CCC_ACCOUNT', 'CUSTOMER', 'TASK', 'COST_TYPE', 'ALLOCATION']

    for setting in mapping_settings:
        if setting.source_field not in default_expense_attributes and \
                setting.destination_field not in default_destination_attributes:
            if setting.source_field == 'PROJECT':
                source_value = lineitem.project
            elif setting.source_field == 'COST_CENTER':
                source_value = lineitem.cost_center
            else:
                attribute = ExpenseAttribute.objects.filter(
                    attribute_type=setting.source_field,
                    workspace_id=expense_group.workspace_id
                ).first()
                source_value = lineitem.custom_properties.get(attribute.display_name, None)

            mapping: Mapping = Mapping.objects.filter(
                source_type=setting.source_field,
                destination_type=setting.destination_field,
                source__value=source_value,
                workspace_id=expense_group.workspace_id
            ).first()
            if mapping:
                dimension_name = 'GLDIM{}'.format(mapping.destination.attribute_type)
                value = mapping.destination.destination_id

                user_dimensions.append({
                    dimension_name: value
                })

    return user_dimensions


def get_intacct_employee_object(object_type: str, expense_group: ExpenseGroup):
    mapping = EmployeeMapping.objects.filter(
        source_employee__value=expense_group.description.get('employee_email'),
        workspace_id=expense_group.workspace_id
    ).first()

    if mapping and mapping.destination_employee:
        employee = DestinationAttribute.objects.filter(
            attribute_type='EMPLOYEE',
            destination_id=mapping.destination_employee.destination_id,
            workspace_id=expense_group.workspace_id
        ).order_by('-updated_at').first()

        if employee and employee.detail[object_type]:
            default_employee_object = employee.detail[object_type]
            return default_employee_object
    
def get_ccc_account_id(general_mappings: GeneralMapping, expense: Expense, description: str):
    card_mapping = Mapping.objects.filter(
        source_type='CORPORATE_CARD',
        destination_type='CHARGE_CARD_NUMBER',
        source__source_id=expense.corporate_card_id,
        workspace_id=general_mappings.workspace
    ).first()

    if card_mapping:
        return card_mapping.destination.destination_id
    else:
        employee_mapping: EmployeeMapping = EmployeeMapping.objects.filter(
            source_employee__value=description.get('employee_email'),
            workspace_id=general_mappings.workspace
        ).first()
        if employee_mapping and employee_mapping.destination_card_account:
            return employee_mapping.destination_card_account.destination_id 

    return general_mappings.default_charge_card_id

def get_credit_card_transaction_number(expense_group: ExpenseGroup, expense: Expense, expense_group_settings: ExpenseGroupSettings):
    if expense_group.expenses.count() > 1 and expense_group_settings.split_expense_grouping == 'MULTIPLE_LINE_ITEM' and 'bank_transaction_id' in expense_group.description:
        return expense_group.description['bank_transaction_id']
    else:
        return expense.expense_number

class Bill(models.Model):
    """
    Sage Intacct Bill
    """
    id = models.AutoField(primary_key=True)
    expense_group = models.OneToOneField(ExpenseGroup, on_delete=models.PROTECT, help_text='Expense group reference')
    vendor_id = models.CharField(max_length=255, help_text='Sage Intacct Vendor ID')
    description = models.TextField(help_text='Sage Intacct Bill Description')
    memo = models.TextField(help_text='Sage Intacct docnumber', null=True)
    currency = models.CharField(max_length=5, help_text='Expense Report Currency')
    supdoc_id = models.CharField(help_text='Sage Intacct Attachments ID', max_length=255, null=True)
    transaction_date = models.DateTimeField(help_text='Bill transaction date', null=True)
    payment_synced = models.BooleanField(help_text='Payment synced status', default=False)
    paid_on_sage_intacct = models.BooleanField(help_text='Payment status in Sage Intacct', default=False)
    is_retired = models.BooleanField(help_text='Is Payment sync retried', default=False)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'bills'

    @staticmethod
    def create_bill(expense_group: ExpenseGroup, supdoc_id: str = None):
        """
        Create bill
        :param expense_group: expense group
        :return: bill object
        """
        description = expense_group.description
        expense = expense_group.expenses.first()
        general_mappings = GeneralMapping.objects.get(workspace_id=expense_group.workspace_id)
        memo = get_memo(expense_group, ExportTable=Bill, workspace_id=expense_group.workspace_id)

        if expense_group.fund_source == 'PERSONAL':
            vendor_id = EmployeeMapping.objects.get(
                source_employee__value=description.get('employee_email'),
                workspace_id=expense_group.workspace_id
            ).destination_vendor.destination_id

        elif expense_group.fund_source == 'CCC':
            vendor_id = general_mappings.default_ccc_vendor_id

        bill_object, _ = Bill.objects.update_or_create(
            expense_group=expense_group,
            defaults={
                'vendor_id': vendor_id,
                'description': description,
                'memo': memo,
                'supdoc_id': supdoc_id,
                'currency': expense.currency,
                'transaction_date': get_transaction_date(expense_group)
            }
        )
        return bill_object


class BillLineitem(models.Model):
    """
    Sage Intacct Bill Lineitem
    """
    id = models.AutoField(primary_key=True)
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, help_text='Reference to Bill')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    expense_type_id = models.CharField(help_text='Sage Intacct expense type id', max_length=255, null=True)
    gl_account_number = models.CharField(help_text='Sage Intacct gl account number', max_length=255, null=True)
    project_id = models.CharField(help_text='Sage Intacct project id', max_length=255, null=True)
    location_id = models.CharField(help_text='Sage Intacct location id', max_length=255, null=True)
    class_id = models.CharField(help_text='Sage Intacct class id', max_length=255, null=True)
    department_id = models.CharField(help_text='Sage Intacct department id', max_length=255, null=True)
    customer_id = models.CharField(max_length=255, help_text='Sage Intacct customer id', null=True)
    item_id = models.CharField(max_length=255, help_text='Sage Intacct iten id', null=True)
    task_id = models.CharField(max_length=255, help_text='Sage intacct Task Id', null=True)
    cost_type_id = models.CharField(max_length=255, help_text='Sage intacct Task Id', null=True)
    memo = models.TextField(help_text='Sage Intacct lineitem description', null=True)
    user_defined_dimensions = JSONField(null=True, help_text='Sage Intacct User Defined Dimensions')
    amount = models.FloatField(help_text='Bill amount')
    tax_amount = models.FloatField(null=True, help_text='Tax amount')
    tax_code = models.CharField(max_length=255, help_text='Tax Group ID', null=True)
    billable = models.BooleanField(null=True, help_text='Expense Billable or not')
    allocation_id = models.CharField(max_length=255, help_text='Sage Intacct Allocation id', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'bill_lineitems'

    @staticmethod
    def create_bill_lineitems(expense_group: ExpenseGroup,  configuration: Configuration):
        """
        Create bill lineitems
        :param expense_group: expense group
        :param configuration: Workspace Configuration Settings
        :return: lineitems objects
        """
        expenses = expense_group.expenses.all()
        bill = Bill.objects.get(expense_group=expense_group)
        dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=expense_group.workspace_id).first()
        task_id = None
        cost_type_id = None

        default_employee_location_id = None
        default_employee_department_id = None

        try:
            general_mappings = GeneralMapping.objects.get(workspace_id=expense_group.workspace_id)
        except GeneralMapping.DoesNotExist:
            general_mappings = None

        bill_lineitem_objects = []

        for lineitem in expenses:
            category = lineitem.category if (lineitem.category == lineitem.sub_category or lineitem.sub_category == None) else '{0} / {1}'.format(
                lineitem.category, lineitem.sub_category)

            account = CategoryMapping.objects.filter(
                source_category__value=category,
                workspace_id=expense_group.workspace_id
            ).first()

            if general_mappings.use_intacct_employee_locations:
                default_employee_location_id = get_intacct_employee_object('location_id', expense_group)

            if general_mappings.use_intacct_employee_departments:
                default_employee_department_id = get_intacct_employee_object('department_id', expense_group)

            project_id = get_project_id_or_none(expense_group, lineitem, general_mappings)
            department_id = get_department_id_or_none(expense_group, lineitem, general_mappings) if \
                default_employee_department_id is None else None
            location_id = get_location_id_or_none(expense_group, lineitem, general_mappings) if \
                default_employee_location_id is None else None
            class_id = get_class_id_or_none(expense_group, lineitem, general_mappings)
            customer_id = get_customer_id_or_none(expense_group, lineitem, general_mappings, project_id)
            item_id = get_item_id_or_none(expense_group, lineitem, general_mappings)

            if dependent_field_setting:
                task_id = get_task_id_or_none(expense_group, lineitem, dependent_field_setting, project_id)
                cost_type_id = get_cost_type_id_or_none(expense_group, lineitem, dependent_field_setting, project_id, task_id)
            
            user_defined_dimensions = get_user_defined_dimension_object(expense_group, lineitem)

            dimensions_values = {
                    'project_id': project_id,
                    'location_id': default_employee_location_id or location_id,
                    'department_id': default_employee_department_id or department_id,
                    'class_id': class_id,
                    'customer_id': customer_id,
                    'item_id': item_id,
                    'task_id': task_id,
                    'cost_type_id': cost_type_id
                }
            
            allocation_id, allocation_detail = get_allocation_id_or_none(expense_group, lineitem)
            if allocation_id and allocation_detail:
                for allocation_dimension, dimension_variable_name in allocation_mapping.items():
                        if allocation_dimension in allocation_detail.keys():
                            dimensions_values[dimension_variable_name] = None

                allocation_dimensions = set(allocation_detail.keys())
                user_defined_dimensions = [user_defined_dimension for user_defined_dimension in user_defined_dimensions if list(user_defined_dimension.keys())[0] not in allocation_dimensions]
            
            bill_lineitem_object, _ = BillLineitem.objects.update_or_create(
                bill=bill,
                expense_id=lineitem.id,
                defaults={
                    'gl_account_number': account.destination_account.destination_id
                    if account and account.destination_account else None,
                    'expense_type_id': account.destination_expense_head.destination_id
                    if account and account.destination_expense_head else None,
                    'project_id': dimensions_values['project_id'],
                    'department_id': dimensions_values['department_id'],
                    'class_id': dimensions_values['class_id'],
                    'location_id': dimensions_values['location_id'],
                    'customer_id': dimensions_values['customer_id'],
                    'item_id': dimensions_values['item_id'],
                    'task_id': dimensions_values['task_id'],
                    'cost_type_id': dimensions_values['cost_type_id'],
                    'user_defined_dimensions': user_defined_dimensions,
                    'amount': lineitem.amount,
                    'tax_code': get_tax_code_id_or_none(expense_group, lineitem),
                    'tax_amount': lineitem.tax_amount,
                    'billable': lineitem.billable if customer_id and item_id else False,
                    'memo': get_expense_purpose(expense_group.workspace_id, lineitem, category, configuration),
                    'allocation_id': allocation_id
                }
            )

            bill_lineitem_objects.append(bill_lineitem_object)

        return bill_lineitem_objects


class ExpenseReport(models.Model):
    """
    Sage Intacct ExpenseReport
    """
    id = models.AutoField(primary_key=True)
    expense_group = models.OneToOneField(ExpenseGroup, on_delete=models.PROTECT, help_text='Expense group reference')
    employee_id = models.CharField(max_length=255, help_text='Sage Intacct Employee ID')
    description = models.TextField(help_text='Sage Intacct ExpenseReport Description')
    memo = models.TextField(help_text='Sage Intacct memo', null=True)
    currency = models.CharField(max_length=5, help_text='Expense Report Currency')
    supdoc_id = models.CharField(help_text='Sage Intacct Attachments ID', max_length=255, null=True)
    transaction_date = models.DateTimeField(help_text='Expense Report transaction date', null=True)
    payment_synced = models.BooleanField(help_text='Payment synced status', default=False)
    paid_on_sage_intacct = models.BooleanField(help_text='Payment status in Sage Intacct', default=False)
    is_retired = models.BooleanField(help_text='Is Payment sync retried', default=False)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'expense_reports'

    @staticmethod
    def create_expense_report(expense_group: ExpenseGroup, supdoc_id: str = None):
        """
        Create expense report
        :param expense_group: expense group
        :return: expense report object
        """
        description = expense_group.description
        expense = expense_group.expenses.first()
        memo = get_memo(expense_group, ExportTable=ExpenseReport, workspace_id=expense_group.workspace_id)

        expense_report_object, _ = ExpenseReport.objects.update_or_create(
            expense_group=expense_group,
            defaults={
                'employee_id': EmployeeMapping.objects.get(
                    source_employee__value=description.get('employee_email'),
                    workspace_id=expense_group.workspace_id
                ).destination_employee.destination_id,
                'description': description,
                'memo': memo,
                'supdoc_id': supdoc_id,
                'currency': expense.currency,
                'transaction_date': get_transaction_date(expense_group),
            }
        )

        return expense_report_object


class ExpenseReportLineitem(models.Model):
    """
    Sage Intacct ExpenseReport Lineitem
    """
    id = models.AutoField(primary_key=True)
    expense_report = models.ForeignKey(ExpenseReport, on_delete=models.PROTECT, help_text='Reference to ExpenseReport')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    expense_type_id = models.CharField(help_text='Sage Intacct expense type id', max_length=255, null=True)
    gl_account_number = models.CharField(help_text='Sage Intacct gl account number', max_length=255, null=True)
    project_id = models.CharField(help_text='Sage Intacct project id', max_length=255, null=True)
    location_id = models.CharField(help_text='Sage Intacct location id', max_length=255, null=True)
    class_id = models.CharField(help_text='Sage Intacct class id', max_length=255, null=True)
    department_id = models.CharField(help_text='Sage Intacct department id', max_length=255, null=True)
    customer_id = models.CharField(max_length=255, help_text='Sage Intacct customer id', null=True)
    item_id = models.CharField(max_length=255, help_text='Sage Intacct iten id', null=True)
    task_id = models.CharField(max_length=255, help_text='Sage Intacct Task Id', null=True)
    cost_type_id = models.CharField(max_length=255, help_text='Sage Intacct Cost Type', null=True)
    user_defined_dimensions = JSONField(null=True, help_text='Sage Intacct User Defined Dimensions')
    memo = models.TextField(help_text='Sage Intacct lineitem description', null=True)
    amount = models.FloatField(help_text='Expense amount')
    tax_amount = models.FloatField(null=True, help_text='Tax amount')
    tax_code = models.CharField(max_length=255, help_text='Tax Group ID', null=True)
    billable = models.BooleanField(null=True, help_text='Expense Billable or not')
    expense_payment_type = models.CharField(max_length=255, help_text='Expense Payment Type', null=True)
    transaction_date = models.DateTimeField(help_text='Expense Report transaction date', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'expense_report_lineitems'

    @staticmethod
    def create_expense_report_lineitems(expense_group: ExpenseGroup, configuration: Configuration):
        """
        Create expense report lineitems
        :param expense_group: expense group
        :param configuration: Workspace Configuration Settings
        :return: lineitems objects
        """
        expenses = expense_group.expenses.all()
        expense_report = ExpenseReport.objects.get(expense_group=expense_group)
        task_id = None
        cost_type_id = None
        dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=expense_group.workspace_id).first()

        default_employee_location_id = None
        default_employee_department_id = None

        try:
            general_mappings = GeneralMapping.objects.get(workspace_id=expense_group.workspace_id)
        except GeneralMapping.DoesNotExist:
            general_mappings = None

        expense_report_lineitem_objects = []

        for lineitem in expenses:
            category = lineitem.category if (lineitem.category == lineitem.sub_category or lineitem.sub_category == None) else '{0} / {1}'.format(
                lineitem.category, lineitem.sub_category)

            account = CategoryMapping.objects.filter(
                source_category__value=category,
                workspace_id=expense_group.workspace_id
            ).first()

            if general_mappings.use_intacct_employee_locations:
                default_employee_location_id = get_intacct_employee_object('location_id', expense_group)

            if general_mappings.use_intacct_employee_departments:
                default_employee_department_id = get_intacct_employee_object('department_id', expense_group)

            project_id = get_project_id_or_none(expense_group, lineitem, general_mappings)
            department_id = get_department_id_or_none(expense_group, lineitem, general_mappings) if\
                default_employee_department_id is None else None
            location_id = get_location_id_or_none(expense_group, lineitem, general_mappings) if\
                default_employee_location_id is None else None
            class_id = get_class_id_or_none(expense_group, lineitem, general_mappings)
            customer_id = get_customer_id_or_none(expense_group, lineitem, general_mappings, project_id)
            item_id = get_item_id_or_none(expense_group, lineitem, general_mappings)

            if dependent_field_setting:
                task_id = get_task_id_or_none(expense_group, lineitem, dependent_field_setting, project_id)
                cost_type_id = get_cost_type_id_or_none(expense_group, lineitem, dependent_field_setting, project_id, task_id)

            user_defined_dimensions = get_user_defined_dimension_object(expense_group, lineitem)

            if expense_group.fund_source == 'PERSONAL':
                expense_payment_type = general_mappings.default_reimbursable_expense_payment_type_name
            else:
                expense_payment_type = general_mappings.default_ccc_expense_payment_type_name

            expense_report_lineitem_object, _ = ExpenseReportLineitem.objects.update_or_create(
                expense_report=expense_report,
                expense_id=lineitem.id,
                defaults={
                    'gl_account_number': account.destination_account.destination_id
                    if account and account.destination_account else None,
                    'expense_type_id': account.destination_expense_head.destination_id
                    if account and account.destination_expense_head else None,
                    'project_id': project_id,
                    'department_id': default_employee_department_id if default_employee_department_id
                    else department_id,
                    'class_id': class_id,
                    'location_id': default_employee_location_id if default_employee_location_id else location_id,
                    'customer_id': customer_id,
                    'item_id': item_id,
                    'task_id': task_id,
                    'cost_type_id': cost_type_id,
                    'user_defined_dimensions': user_defined_dimensions,
                    'transaction_date': lineitem.spent_at,
                    'amount': lineitem.amount,
                    'tax_code': get_tax_code_id_or_none(expense_group, lineitem),
                    'tax_amount': lineitem.tax_amount,
                    'billable': lineitem.billable if customer_id and item_id else False,
                    'expense_payment_type': expense_payment_type,
                    'memo': get_expense_purpose(expense_group.workspace_id, lineitem, category, configuration)
                }
            )

            expense_report_lineitem_objects.append(expense_report_lineitem_object)

        return expense_report_lineitem_objects


class JournalEntry(models.Model):
    """
    Sage Intacct Journal Entry 
    """
    id = models.AutoField(primary_key=True)
    expense_group = models.OneToOneField(ExpenseGroup, on_delete=models.PROTECT, help_text='Expense group reference')
    description = models.TextField(help_text='Sage Intacct ExpenseReport Description')
    memo = models.TextField(help_text='Sage Intacct memo', null=True)
    currency = models.CharField(max_length=5, help_text='Expense Report Currency')
    supdoc_id = models.CharField(help_text='Sage Intacct Attachments ID', max_length=255, null=True)
    transaction_date = models.DateTimeField(help_text='Expense Report transaction date', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'journal_entries'

    @staticmethod
    def create_journal_entry(expense_group: ExpenseGroup, supdoc_id: str = None):
        """
        Create journal entry
        :param expense_group: expense group
        :param configuration: Workspace configuration
        :return: journal entry object
        """
        description = expense_group.description
        expense = expense_group.expenses.first()
        memo = get_memo(expense_group, ExportTable=JournalEntry, workspace_id=expense_group.workspace_id)

        journal_entry_object, _ = JournalEntry.objects.update_or_create(
            expense_group=expense_group,
            defaults={
                'description': description,
                'memo': memo,
                'currency': expense.currency,
                'supdoc_id': supdoc_id,
                'transaction_date': get_transaction_date(expense_group)
            }
        )

        return journal_entry_object


class JournalEntryLineitem(models.Model):
    """
    Sage Intacct Journal Entry Lineitem
    """
    id = models.AutoField(primary_key=True)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, help_text='Reference to Journal Entry')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    gl_account_number = models.CharField(help_text='Sage Intacct gl account number', max_length=255, null=True)
    project_id = models.CharField(help_text='Sage Intacct project id', max_length=255, null=True)
    employee_id = models.CharField(help_text='Sage Intacct employee id', max_length=255, null=True)
    vendor_id = models.CharField(help_text='Sage Intacct vendor id', max_length=255, null=True)
    location_id = models.CharField(help_text='Sage Intacct location id', max_length=255, null=True)
    class_id = models.CharField(help_text='Sage Intacct class id', max_length=255, null=True)
    department_id = models.CharField(help_text='Sage Intacct department id', max_length=255, null=True)
    customer_id = models.CharField(max_length=255, help_text='Sage Intacct customer id', null=True)
    item_id = models.CharField(max_length=255, help_text='Sage Intacct item id', null=True)
    task_id = models.CharField(max_length=255, help_text='Sage Intacct Task', null=True)
    cost_type_id = models.CharField(max_length=255, help_text='Sage Intacct Cost Type', null=True)
    memo = models.TextField(help_text='Sage Intacct lineitem description', null=True)
    user_defined_dimensions = JSONField(null=True, help_text='Sage Intacct User Defined Dimensions')
    amount = models.FloatField(help_text='Bill amount')
    tax_amount = models.FloatField(null=True, help_text='Tax amount')
    tax_code = models.CharField(max_length=255, help_text='Tax Group ID', null=True)
    billable = models.BooleanField(null=True, help_text='Expense Billable or not')
    transaction_date = models.DateTimeField(help_text='Expense Report transaction date', null=True)
    allocation_id = models.CharField(max_length=255, help_text='Sage Intacct Allocation id', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'journal_entry_lineitems'

    @staticmethod
    def create_journal_entry_lineitems(expense_group: ExpenseGroup, configuration: Configuration, sage_intacct_connection):
        """
        Create journal entry lineitems
        :param expense_group: expense group
        :return: lineitems objects
        """
        expenses = expense_group.expenses.all()
        journal_entry = JournalEntry.objects.get(expense_group=expense_group)
        task_id = None
        cost_type_id = None
        dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=expense_group.workspace_id).first()

        default_employee_location_id = None
        default_employee_department_id = None

        try:
            general_mappings = GeneralMapping.objects.get(workspace_id=expense_group.workspace_id)
        except GeneralMapping.DoesNotExist:
            general_mappings = None

        journal_entry_lineitem_objects = []

        for lineitem in expenses:
            category = lineitem.category if (lineitem.category == lineitem.sub_category or lineitem.sub_category == None) else '{0} / {1}'.format(
                lineitem.category, lineitem.sub_category)

            account = CategoryMapping.objects.filter(
                source_category__value=category,
                workspace_id=expense_group.workspace_id
            ).first()

            if general_mappings.use_intacct_employee_locations:
                default_employee_location_id = get_intacct_employee_object('location_id', expense_group)

            if general_mappings.use_intacct_employee_departments:
                default_employee_department_id = get_intacct_employee_object('department_id', expense_group)

            description = expense_group.description

            employee_mapping_setting = configuration.employee_field_mapping

            project_id = get_project_id_or_none(expense_group, lineitem, general_mappings)
            department_id = get_department_id_or_none(expense_group, lineitem, general_mappings) if \
                default_employee_department_id is None else None
            location_id = get_location_id_or_none(expense_group, lineitem, general_mappings) if \
                default_employee_location_id is None else None

            employee_id = None

            if settings.BRAND_ID == 'fyle':
                entity = EmployeeMapping.objects.get(
                    source_employee__value=description.get('employee_email'),
                    workspace_id=expense_group.workspace_id
                )

                employee_id = entity.destination_employee.destination_id if entity and entity.destination_employee and employee_mapping_setting == 'EMPLOYEE' else None

                vendor_id = entity.destination_vendor.destination_id if entity and entity.destination_vendor and employee_mapping_setting == 'VENDOR' else None

                if lineitem.fund_source == 'CCC' and configuration.use_merchant_in_journal_line:
                    # here it would create a Credit Card Vendor if the expene vendor is not present
                    vendor = import_string('apps.sage_intacct.tasks.get_or_create_credit_card_vendor')(expense_group.workspace_id, configuration, lineitem.vendor, sage_intacct_connection)
                    if vendor:
                        vendor_id = vendor.destination_id

            else:
                vendor = None
                merchant = lineitem.vendor if lineitem.vendor else None

                if merchant:
                    vendor = DestinationAttribute.objects.filter(
                        value__iexact=merchant, attribute_type='VENDOR', workspace_id=expense_group.workspace_id
                    ).order_by('-updated_at').first()

                if not vendor:
                    vendor = DestinationAttribute.objects.filter(
                        value='Credit Card Misc',
                        workspace_id=expense_group.workspace_id
                    ).first()

                vendor_id = vendor.destination_id
            
            class_id = get_class_id_or_none(expense_group, lineitem, general_mappings)

            if dependent_field_setting:
                task_id = get_task_id_or_none(expense_group, lineitem, dependent_field_setting, project_id)
                cost_type_id = get_cost_type_id_or_none(expense_group, lineitem, dependent_field_setting, project_id, task_id)

            customer_id = get_customer_id_or_none(expense_group, lineitem, general_mappings, project_id)
            item_id = get_item_id_or_none(expense_group, lineitem, general_mappings)
            user_defined_dimensions = get_user_defined_dimension_object(expense_group, lineitem)

            allocation_id, _ = get_allocation_id_or_none(expense_group=expense_group, lineitem=lineitem)

            journal_entry_lineitem_object, _ = JournalEntryLineitem.objects.update_or_create(
                journal_entry=journal_entry,
                expense_id=lineitem.id,
                defaults={
                    'gl_account_number': account.destination_account.destination_id
                    if account and account.destination_account else None,
                    'project_id': project_id,
                    'department_id': default_employee_department_id if default_employee_department_id
                    else department_id,
                    'class_id': class_id,
                    'location_id': default_employee_location_id if default_employee_location_id else location_id,
                    'customer_id': customer_id,
                    'item_id': item_id,
                    'employee_id': employee_id,
                    'vendor_id': vendor_id,
                    'task_id': task_id,
                    'cost_type_id': cost_type_id,
                    'user_defined_dimensions': user_defined_dimensions,
                    'amount': lineitem.amount,
                    'tax_code': get_tax_code_id_or_none(expense_group, lineitem),
                    'tax_amount': lineitem.tax_amount,
                    'billable': lineitem.billable if customer_id and item_id else False,
                    'memo': get_expense_purpose(expense_group.workspace_id, lineitem, category, configuration),
                    'allocation_id': allocation_id
                }
            )
            journal_entry_lineitem_objects.append(journal_entry_lineitem_object)

        return journal_entry_lineitem_objects


class ChargeCardTransaction(models.Model):
    """
    Sage Intacct Charge Card Transaction
    """
    id = models.AutoField(primary_key=True)
    expense_group = models.OneToOneField(ExpenseGroup, on_delete=models.PROTECT, help_text='Expense group reference')
    charge_card_id = models.CharField(max_length=255, help_text='Sage Intacct Charge Card ID')
    vendor_id = models.CharField(max_length=255, help_text='Sage Intacct Vendor ID')
    description = models.TextField(help_text='Sage Intacct Charge Card Transaction Description')
    payee = models.CharField(max_length=255, help_text='Sage Intacct Payee', null=True)
    memo = models.TextField(help_text='Sage Intacct referenceno', null=True)
    reference_no = models.CharField(max_length=255, help_text='Sage Intacct Reference number to transaction')
    currency = models.CharField(max_length=5, help_text='Expense Report Currency')
    supdoc_id = models.CharField(help_text='Sage Intacct Attachments ID', max_length=255, null=True)
    transaction_date = models.DateTimeField(help_text='Safe Intacct Charge Card transaction date', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'charge_card_transactions'

    @staticmethod
    def create_charge_card_transaction(expense_group: ExpenseGroup, vendor_id: str = None, supdoc_id: str = None):
        """
        Create create charge card transaction
        :param expense_group: ExpenseGroup
        :return: ChargeCardTransaction object
        """
        description = expense_group.description
        expense = expense_group.expenses.first()
        memo = get_memo(expense_group, ExportTable=ChargeCardTransaction, workspace_id=expense_group.workspace_id)
        expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=expense_group.workspace_id)
        general_mappings = GeneralMapping.objects.get(workspace_id=expense_group.workspace_id)
        charge_card_id = get_ccc_account_id(general_mappings, expense, description)

        expense_group.description['spent_at'] = expense.spent_at.strftime('%Y-%m-%dT%H:%M:%S')
        expense_group.save()

        merchant = expense.vendor if expense.vendor else None
        if not vendor_id: 
            vendor_id = DestinationAttribute.objects.filter(value='Credit Card Misc', workspace_id=expense_group.workspace_id).first().destination_id

        charge_card_transaction_object, _ = ChargeCardTransaction.objects.update_or_create(
            expense_group=expense_group,
            defaults={
                'charge_card_id': charge_card_id,
                'vendor_id': vendor_id,
                'payee': merchant,
                'description': description,
                'memo': memo,
                'supdoc_id': supdoc_id,
                'reference_no': get_credit_card_transaction_number(
                    expense_group,
                    expense,
                    expense_group_settings
                ),
                'currency': expense.currency,
                'transaction_date': get_transaction_date(expense_group)
            }
        )

        return charge_card_transaction_object


class ChargeCardTransactionLineitem(models.Model):
    """
    Sage Intacct Charge Card Transaction Lineitem
    """
    id = models.AutoField(primary_key=True)
    charge_card_transaction = models.ForeignKey(ChargeCardTransaction, on_delete=models.PROTECT,
                                                help_text='Reference to ChargeCardTransaction')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    gl_account_number = models.CharField(help_text='Sage Intacct gl account number', max_length=255, null=True)
    project_id = models.CharField(help_text='Sage Intacct project id', max_length=255, null=True)
    location_id = models.CharField(help_text='Sage Intacct location id', max_length=255, null=True)
    department_id = models.CharField(help_text='Sage Intacct department id', max_length=255, null=True)
    class_id = models.CharField(help_text='Sage Intacct class id', max_length=255, null=True)
    customer_id = models.CharField(max_length=255, help_text='Sage Intacct customer id', null=True)
    item_id = models.CharField(max_length=255, help_text='Sage Intacct iten id', null=True)
    task_id = models.CharField(max_length=255, help_text='Sage Intacct Task Id', null=True)
    cost_type_id = models.CharField(max_length=255, help_text='Sage Intacct Cost Type Id', null=True)
    memo = models.TextField(help_text='Sage Intacct lineitem description', null=True)
    user_defined_dimensions = JSONField(null=True, help_text='Sage Intacct User Defined Dimensions')
    amount = models.FloatField(help_text='Charge Card Transaction amount')
    tax_amount = models.FloatField(null=True, help_text='Tax amount')
    tax_code = models.CharField(max_length=255, help_text='Tax Group ID', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'charge_card_transaction_lineitems'

    @staticmethod
    def create_charge_card_transaction_lineitems(expense_group: ExpenseGroup,  configuration: Configuration):
        """
        Create expense report lineitems
        :param expense_group: expense group
        :param configuration: Workspace Configuration Settings
        :return: lineitems objects
        """
        expenses = expense_group.expenses.all()
        charge_card_transaction = ChargeCardTransaction.objects.get(expense_group=expense_group)

        task_id = None
        cost_type_id = None
        dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=expense_group.workspace_id).first()

        default_employee_location_id = None
        default_employee_department_id = None

        try:
            general_mappings = GeneralMapping.objects.get(workspace_id=expense_group.workspace_id)
        except GeneralMapping.DoesNotExist:
            general_mappings = None

        charge_card_transaction_lineitem_objects = []

        for lineitem in expenses:
            category = lineitem.category if (lineitem.category == lineitem.sub_category or lineitem.sub_category == None) else '{0} / {1}'.format(
                lineitem.category, lineitem.sub_category)

            account = CategoryMapping.objects.filter(
                source_category__value=category,
                workspace_id=expense_group.workspace_id
            ).first()

            if general_mappings.use_intacct_employee_locations:
                default_employee_location_id = get_intacct_employee_object('location_id', expense_group)

            if general_mappings.use_intacct_employee_departments:
                default_employee_department_id = get_intacct_employee_object('department_id', expense_group)

            project_id = get_project_id_or_none(expense_group, lineitem, general_mappings)
            department_id = get_department_id_or_none(expense_group, lineitem, general_mappings) if\
                default_employee_department_id is None else None
            location_id = get_location_id_or_none(expense_group, lineitem, general_mappings) if\
                default_employee_location_id is None else None
            class_id = get_class_id_or_none(expense_group, lineitem, general_mappings)
            customer_id = get_customer_id_or_none(expense_group, lineitem, general_mappings, project_id)
            item_id = get_item_id_or_none(expense_group, lineitem, general_mappings)

            user_defined_dimensions = get_user_defined_dimension_object(expense_group, lineitem)

            if dependent_field_setting:
                task_id = get_task_id_or_none(expense_group, lineitem, dependent_field_setting, project_id)
                cost_type_id = get_cost_type_id_or_none(expense_group, lineitem, dependent_field_setting, project_id, task_id)

            charge_card_transaction_lineitem_object, _ = ChargeCardTransactionLineitem.objects.update_or_create(
                charge_card_transaction=charge_card_transaction,
                expense_id=lineitem.id,
                defaults={
                    'gl_account_number': account.destination_account.destination_id
                    if account and account.destination_account else None,
                    'project_id': project_id,
                    'department_id': default_employee_department_id if default_employee_department_id
                    else department_id,
                    'class_id': class_id,
                    'location_id': default_employee_location_id if default_employee_location_id else location_id,
                    'customer_id': customer_id,
                    'item_id': item_id,
                    'task_id': task_id,
                    'cost_type_id': cost_type_id,
                    'amount': lineitem.amount,
                    'tax_code': get_tax_code_id_or_none(expense_group, lineitem),
                    'tax_amount': lineitem.tax_amount,
                    'memo': get_expense_purpose(expense_group.workspace_id, lineitem, category, configuration),
                    'user_defined_dimensions': user_defined_dimensions
                }
            )

            charge_card_transaction_lineitem_objects.append(charge_card_transaction_lineitem_object)

        return charge_card_transaction_lineitem_objects


class APPayment(models.Model):
    """
    Sage Intacct AP Payments
    """
    id = models.AutoField(primary_key=True)
    expense_group = models.OneToOneField(ExpenseGroup, on_delete=models.PROTECT, help_text='Expense group reference')
    payment_account_id = models.CharField(max_length=255, help_text='Sage Intacct Payment Account ID')
    vendor_id = models.CharField(max_length=255, help_text='Sage Intacct Vendor ID')
    description = models.TextField(help_text='Payment Description')
    currency = models.CharField(max_length=255, help_text='AP Payment Currency')
    created_at = models.DateField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'ap_payments'

    @staticmethod
    def create_ap_payment(expense_group: ExpenseGroup):
        """
        Create AP Payments
        :param expense_group: expense group
        :return: AP Payment object
        """
        description = expense_group.description
        expense = expense_group.expenses.first()
        memo = get_memo(
            expense_group, ExportTable=APPayment,
            workspace_id=expense_group.workspace_id, payment_type='Bill')

        vendor_id = EmployeeMapping.objects.get(
            source_employee__value=description.get('employee_email'),
            workspace_id=expense_group.workspace_id
        ).destination_vendor.destination_id

        general_mappings = GeneralMapping.objects.get(workspace_id=expense_group.workspace_id)

        ap_payment_object, _ = APPayment.objects.update_or_create(
            expense_group=expense_group,
            defaults={
                'payment_account_id': general_mappings.payment_account_id,
                'vendor_id': vendor_id,
                'description': memo,
                'currency': expense.currency
            }
        )

        return ap_payment_object


class APPaymentLineitem(models.Model):
    """
    Sage Intacct AP Payment LineItems
    """
    id = models.AutoField(primary_key=True)
    ap_payment = models.ForeignKey(APPayment, on_delete=models.PROTECT, help_text='Reference to AP Payment')
    amount = models.FloatField(help_text='AP Payment amount')
    record_key = models.CharField(max_length=255, help_text='Sage Intacct Record Key')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'ap_payment_lineitems'

    @staticmethod
    def create_ap_payment_lineitems(expense_group: ExpenseGroup, record_key):
        """
        Create AP Payment lineitems
        :param record_key:
        :param expense_group: expense group
        :return: lineitems objects
        """
        expenses = expense_group.expenses.all()
        ap_payment = APPayment.objects.get(expense_group=expense_group)

        ap_payment_lineitem_objects = []

        total_amount = 0
        for lineitem in expenses:
            total_amount = total_amount + lineitem.amount

        ap_payment_lineitem_object, _ = APPaymentLineitem.objects.update_or_create(
            ap_payment=ap_payment,
            record_key=record_key,
            defaults={
                'amount': round(total_amount, 2),
            }
        )
        ap_payment_lineitem_objects.append(ap_payment_lineitem_object)

        return ap_payment_lineitem_objects


class SageIntacctReimbursement(models.Model):
    """
    Sage Intacct Reimbursement
    """
    id = models.AutoField(primary_key=True)
    expense_group = models.OneToOneField(ExpenseGroup, on_delete=models.PROTECT, help_text='Expense group reference')
    account_id = models.CharField(max_length=255, help_text='Sage Intacct Account ID')
    employee_id = models.CharField(max_length=255, help_text='Sage Intacct Employee ID')
    memo = models.TextField(help_text='Reimbursement Memo')
    payment_description = models.TextField(help_text='Reimbursement Description')
    created_at = models.DateField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'sage_intacct_reimbursements'

    @staticmethod
    def create_sage_intacct_reimbursement(expense_group: ExpenseGroup):
        """
        Create Sage Intacct Reimbursements
        :param expense_group: expense group
        :return: Sage Intacct Reimbursement object
        """

        description = expense_group.description
        memo = get_memo(
            expense_group, ExportTable=SageIntacctReimbursement,
            workspace_id=expense_group.workspace_id, payment_type='Expense Report')

        employee_id = EmployeeMapping.objects.get(
            source_employee__value=description.get('employee_email'),
            workspace_id=expense_group.workspace_id
        ).destination_employee.destination_id

        general_mappings = GeneralMapping.objects.get(workspace_id=expense_group.workspace_id)

        sage_intacct_reimbursement_object, _ = SageIntacctReimbursement.objects.update_or_create(
            expense_group=expense_group,
            defaults={
                'account_id': general_mappings.payment_account_id,
                'employee_id': employee_id,
                'memo': memo,
                'payment_description': 'Payment for Expense Report by {0}'.format(description.get('employee_email'))
            }
        )

        return sage_intacct_reimbursement_object


class SageIntacctReimbursementLineitem(models.Model):
    """
    Sage Intacct Reimbursement LineItems
    """
    id = models.AutoField(primary_key=True)
    sage_intacct_reimbursement = models.ForeignKey(SageIntacctReimbursement, on_delete=models.PROTECT,
                                                   help_text='Reference to Sage Intacct Reimbursement')
    amount = models.FloatField(help_text='Reimbursement amount')
    record_key = models.CharField(max_length=255, help_text='Sage Intacct Record Key')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'sage_intacct_reimbursement_lineitems'

    @staticmethod
    def create_sage_intacct_reimbursement_lineitems(expense_group: ExpenseGroup, record_key):
        """
        Create Reimbursement lineitems
        :param record_key:
        :param expense_group: expense group
        :return: lineitems objects
        """
        expenses = expense_group.expenses.all()
        sage_intacct_reimbursement = SageIntacctReimbursement.objects.get(expense_group=expense_group)

        sage_intacct_reimbursement_lineitem_objects = []

        total_amount = 0
        for lineitem in expenses:
            total_amount = total_amount + lineitem.amount

        sage_intacct_reimbursement_lineitem_object, _ = SageIntacctReimbursementLineitem.objects.update_or_create(
            sage_intacct_reimbursement=sage_intacct_reimbursement,
            record_key=record_key,
            defaults={
                'amount': round(total_amount, 2),
            }
        )
        sage_intacct_reimbursement_lineitem_objects.append(sage_intacct_reimbursement_lineitem_object)

        return sage_intacct_reimbursement_lineitem_objects


class CostType(models.Model):
    """
    Sage Intacct Cost Types
    DB Table: cost_types:
    """
    record_number = models.CharField(max_length=255, help_text='Sage Intacct Record No')
    project_key = models.CharField(max_length=255, help_text='Sage Intacct Project Key')
    project_id = models.CharField(max_length=255, help_text='Sage Intacct Project ID')
    project_name = models.CharField(max_length=255, help_text='Sage Intacct Project Name')
    task_key = models.CharField(max_length=255, help_text='Sage Intacct Task Key')
    task_id = models.CharField(max_length=255, help_text='Sage Intacct Task ID')
    status = models.CharField(max_length=255, help_text='Sage Intacct Status', null=True)
    task_name = models.CharField(max_length=255, help_text='Sage Intacct Task Name')
    cost_type_id = models.CharField(max_length=255, help_text='Sage Intacct Cost Type ID')
    name = models.CharField(max_length=255, help_text='Sage Intacct Cost Type Name')
    when_created = models.CharField(max_length=255, help_text='Sage Intacct When Created', null=True)
    when_modified = models.CharField(max_length=255, help_text='Sage Intacct When Modified', null=True)
    is_imported = models.BooleanField(default=False, help_text='Is Imported')
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        unique_together = ('record_number', 'workspace_id')
        db_table = 'cost_types'

    @staticmethod
    def bulk_create_or_update(cost_types: List[Dict], workspace_id: int):
        """
        Bulk create or update cost types
        """
        record_number_list = [cost_type['RECORDNO'] for cost_type in cost_types]

        filters = {
            'record_number__in': record_number_list,
            'workspace_id': workspace_id
        }

        existing_cost_types = CostType.objects.filter(**filters).values(
            'id',
            'record_number',
            'name',
            'status'
        )

        existing_cost_type_record_numbers = []

        primary_key_map = {}

        for existing_cost_type in existing_cost_types:
            existing_cost_type_record_numbers.append(existing_cost_type['record_number'])

            primary_key_map[existing_cost_type['record_number']] = {
                'id': existing_cost_type['id'],
                'name': existing_cost_type['name'],
                'status': existing_cost_type['status'],
            }

        cost_types_to_be_created = []
        cost_types_to_be_updated = []

        for cost_type in cost_types:
            cost_type_object = CostType(
                record_number=cost_type['RECORDNO'],
                project_key=cost_type['PROJECTKEY'],
                project_id=cost_type['PROJECTID'],
                project_name=cost_type['PROJECTNAME'],
                task_key=cost_type['TASKKEY'],
                task_id=cost_type['TASKID'],
                task_name=cost_type['TASKNAME'],
                cost_type_id=cost_type['COSTTYPEID'],
                name=cost_type['NAME'],
                status=cost_type['STATUS'],
                when_created=cost_type['WHENCREATED'] if 'WHENCREATED' in cost_type else None,
                when_modified=cost_type['WHENMODIFIED'] if 'WHENMODIFIED' in cost_type else None,
                workspace_id=workspace_id
            )

            if cost_type['RECORDNO'] not in existing_cost_type_record_numbers:
                cost_types_to_be_created.append(cost_type_object)

            elif cost_type['RECORDNO'] in primary_key_map.keys() and (
                cost_type['NAME'] != primary_key_map[cost_type['RECORDNO']]['name'] or cost_type['STATUS'] != primary_key_map[cost_type['RECORDNO']]['status']
            ):
                cost_type_object.id = primary_key_map[cost_type['RECORDNO']]['id']
                cost_types_to_be_updated.append(cost_type_object)

        if cost_types_to_be_created:
            CostType.objects.bulk_create(cost_types_to_be_created, batch_size=2000)

        if cost_types_to_be_updated:
            CostType.objects.bulk_update(
                cost_types_to_be_updated, fields=[
                    'project_key', 'project_id', 'project_name', 'task_key', 'task_id', 'task_name',
                    'cost_type_id', 'name', 'status', 'when_modified'
                ],
                batch_size=2000
            )
