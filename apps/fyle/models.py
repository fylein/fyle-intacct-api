"""
Fyle Models
"""
from dateutil import parser
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db import models
from django.db.models import Count, Q, JSONField

from fyle_accounting_mappings.models import ExpenseAttribute

from apps.workspaces.models import Workspace, Configuration

ALLOWED_FIELDS = [
    'employee_email', 'report_id', 'claim_number', 'settlement_id',
    'fund_source', 'vendor', 'category', 'project', 'cost_center',
    'verified_at', 'approved_at', 'spent_at', 'expense_id', 'expense_number', 'payment_number', 'posted_at'
]

ALLOWED_FORM_INPUT = {
    'group_expenses_by': ['settlement_id', 'claim_number', 'report_id', 'category', 'vendor', 'expense_id', 'expense_number', 'payment_number'],
    'export_date_type': ['current_date', 'approved_at', 'spent_at', 'verified_at', 'last_spent_at', 'posted_at']
}

SOURCE_ACCOUNT_MAP = {
    'PERSONAL_CASH_ACCOUNT': 'PERSONAL',
    'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT': 'CCC'
}

CCC_EXPENSE_STATE = (
    ('APPROVED', 'APPROVED'),
    ('PAID', 'PAID'),
    ('PAYMENT_PROCESSING', 'PAYMENT_PROCESSING')
)

EXPENSE_FILTER_RANK = (
    (1, 1),
    (2, 2)
)

EXPENSE_FILTER_JOIN_BY = (
    ('AND', 'AND'),
    ('OR', 'OR')
)

EXPENSE_FILTER_CUSTOM_FIELD_TYPE = (
    ('SELECT', 'SELECT'),
    ('NUMBER', 'NUMBER'),
    ('TEXT','TEXT'),
    ('BOOLEAN', 'BOOLEAN')
)

EXPENSE_FILTER_OPERATOR = (
	('isnull', 'isnull'),
	('in', 'in'),
	('iexact' , 'iexact'),
    ('exact' , 'exact'),
	('icontains', 'icontains'),
	('lt', 'lt'),
	('lte', 'lte'),
	('not_in', 'not_in'),
)

def _format_date(date_string) -> datetime:
    """
    Format date.
    Args:
        date_string (str): Date string.
    Returns:
        datetime: Formatted date.
    """
    if date_string:
        date_string = parser.parse(date_string)
    return date_string


def get_default_expense_group_fields():
    return ['employee_email', 'report_id', 'claim_number', 'fund_source']


def get_default_expense_state():
    return 'PAYMENT_PROCESSING'

def get_default_ccc_expense_state():
    return 'PAID'

class Expense(models.Model):
    """
    Expense
    """
    id = models.AutoField(primary_key=True)
    employee_email = models.EmailField(max_length=255, unique=False, help_text='Email id of the Fyle employee')
    employee_name = models.CharField(max_length=255, null=True, help_text='Name of the Fyle employee')
    category = models.CharField(max_length=255, null=True, blank=True, help_text='Fyle Expense Category')
    sub_category = models.CharField(max_length=255, null=True, blank=True, help_text='Fyle Expense Sub-Category')
    project = models.CharField(max_length=255, null=True, blank=True, help_text='Project')
    expense_id = models.CharField(max_length=255, unique=True, help_text='Expense ID')
    org_id = models.CharField(max_length=255, null=True, help_text='Organization ID')
    expense_number = models.CharField(max_length=255, help_text='Expense Number')
    claim_number = models.CharField(max_length=255, help_text='Claim Number', null=True)
    amount = models.FloatField(help_text='Home Amount')
    currency = models.CharField(max_length=5, help_text='Home Currency')
    foreign_amount = models.FloatField(null=True, help_text='Foreign Amount')
    foreign_currency = models.CharField(null=True, max_length=5, help_text='Foreign Currency')
    tax_amount = models.FloatField(null=True, help_text='Tax Amount')
    tax_group_id = models.CharField(null=True, max_length=255, help_text='Tax Group ID')
    settlement_id = models.CharField(max_length=255, help_text='Settlement ID', null=True)
    reimbursable = models.BooleanField(default=False, help_text='Expense reimbursable or not')
    billable = models.BooleanField(null=True, help_text='Expense Billable or not')
    state = models.CharField(max_length=255, help_text='Expense state')
    vendor = models.CharField(max_length=255, null=True, blank=True, help_text='Vendor')
    cost_center = models.CharField(max_length=255, null=True, blank=True, help_text='Fyle Expense Cost Center')
    purpose = models.TextField(null=True, blank=True, help_text='Purpose')
    report_id = models.CharField(max_length=255, help_text='Report ID')
    spent_at = models.DateTimeField(null=True, help_text='Expense spent at')
    approved_at = models.DateTimeField(null=True, help_text='Expense approved at')
    posted_at = models.DateTimeField(null=True, help_text='Date when the money is taken from the bank')
    expense_created_at = models.DateTimeField(help_text='Expense created at')
    expense_updated_at = models.DateTimeField(help_text='Expense updated at')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')
    fund_source = models.CharField(max_length=255, help_text='Expense fund source')
    verified_at = models.DateTimeField(help_text='Report verified at', null=True)
    custom_properties = JSONField(null=True)
    paid_on_sage_intacct = models.BooleanField(help_text='Expense Payment status on Sage Intacct', default=False)
    file_ids = ArrayField(base_field=models.CharField(max_length=255), null=True, help_text='File IDs')
    payment_number = models.CharField(max_length=55, help_text='Expense payment number', null=True)
    corporate_card_id = models.CharField(max_length=255, null=True, blank=True, help_text='Corporate Card ID')
    is_skipped = models.BooleanField(null=True, default=False, help_text='Expense is skipped or not')
    report_title = models.TextField(null=True, blank=True, help_text='Report title')

    class Meta:
        db_table = 'expenses'

    @staticmethod
    def create_expense_objects(expenses: List[Dict], workspace_id: int):
        """
        Bulk create expense objects
        """
        expense_objects = []

        for expense in expenses:
            for custom_property_field in expense['custom_properties']:
                if expense['custom_properties'][custom_property_field] == '':
                    expense['custom_properties'][custom_property_field] = None
            expense_object, _ = Expense.objects.update_or_create(
                expense_id=expense['id'],
                defaults={
                    'employee_email': expense['employee_email'],
                    'employee_name': expense['employee_name'],
                    'category': expense['category'],
                    'sub_category': expense['sub_category'],
                    'project': expense['project'],
                    'expense_number': expense['expense_number'],
                    'org_id': expense['org_id'],
                    'claim_number': expense['claim_number'],
                    'amount': round(expense['amount'], 2),
                    'currency': expense['currency'],
                    'foreign_amount': expense['foreign_amount'],
                    'foreign_currency': expense['foreign_currency'],
                    'tax_amount': expense['tax_amount'],
                    'tax_group_id': expense['tax_group_id'],
                    'settlement_id': expense['settlement_id'],
                    'reimbursable': expense['reimbursable'],
                    'billable': expense['billable'],
                    'state': expense['state'],
                    'vendor': expense['vendor'][:250] if expense['vendor'] else None,
                    'cost_center': expense['cost_center'],
                    'purpose': expense['purpose'],
                    'report_id': expense['report_id'],
                    'report_title': expense['report_title'],
                    'spent_at': expense['spent_at'],
                    'approved_at': expense['approved_at'],
                    'posted_at': expense['posted_at'],
                    'expense_created_at': expense['expense_created_at'],
                    'expense_updated_at': expense['expense_updated_at'],
                    'fund_source': SOURCE_ACCOUNT_MAP[expense['source_account_type']],
                    'verified_at': expense['verified_at'],
                    'custom_properties': expense['custom_properties'],
                    'payment_number': expense['payment_number'],
                    'file_ids': expense['file_ids'],
                    'corporate_card_id': expense['corporate_card_id'],
                }
            )

            if not ExpenseGroup.objects.filter(expenses__id=expense_object.id).first():
                expense_objects.append(expense_object)

        return expense_objects


class ExpenseGroupSettings(models.Model):
    """
    ExpenseGroupCustomizationSettings
    """
    id = models.AutoField(primary_key=True)
    reimbursable_expense_group_fields = ArrayField(
        base_field=models.CharField(max_length=100), default=get_default_expense_group_fields,
        help_text='list of fields reimbursable expense grouped by'
    )

    corporate_credit_card_expense_group_fields = ArrayField(
        base_field=models.CharField(max_length=100), default=get_default_expense_group_fields,
        help_text='list of fields ccc expenses grouped by'
    )
    expense_state = models.CharField(
        max_length=100, default=get_default_expense_state,
        help_text='state at which the expenses are fetched ( PAYMENT_PROCESSING / PAID)')
    ccc_expense_state = models.CharField(max_length=100, default=get_default_ccc_expense_state, 
        choices=CCC_EXPENSE_STATE, help_text='state at which the ccc expenses are fetched (APPROVED/PAID)', null=True)
    reimbursable_export_date_type = models.CharField(max_length=100, default='current_date', help_text='Export Date')
    ccc_export_date_type = models.CharField(max_length=100, default='current_date', help_text='CCC Export Date')
    workspace = models.OneToOneField(
        Workspace, on_delete=models.PROTECT,
        help_text='To which workspace this expense group setting belongs to',
        related_name='expense_group_settings'
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'expense_group_settings'

    @staticmethod
    def update_expense_group_settings(expense_group_settings: Dict, workspace_id: int):
        settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)
        current_reimbursable_settings = list(settings.reimbursable_expense_group_fields)
        current_ccc_settings = list(settings.corporate_credit_card_expense_group_fields)

        reimbursable_grouped_by = []
        corporate_credit_card_expenses_grouped_by = []

        immutable_reimbursable_list = tuple(current_reimbursable_settings)
        immutable_ccc_list = tuple(current_ccc_settings)

        for field in immutable_reimbursable_list:
            if field in ALLOWED_FORM_INPUT['group_expenses_by']:
                current_reimbursable_settings.remove(field)

        for field in immutable_ccc_list:
            if field in ALLOWED_FORM_INPUT['group_expenses_by']:
                current_ccc_settings.remove(field)

        if 'report_id' not in current_reimbursable_settings:
            if 'claim_number' in current_reimbursable_settings:
                current_reimbursable_settings.remove('claim_number')
        else:
            current_reimbursable_settings.append('claim_number')
        
        if 'expense_id' not in current_reimbursable_settings:
            if 'expense_number' in current_reimbursable_settings:
                current_reimbursable_settings.remove('expense_number')
        else:
            current_reimbursable_settings.append('expense_number')

        if 'settlement_id' not in current_reimbursable_settings:
            if 'payment_number' in current_reimbursable_settings:
                current_reimbursable_settings.remove('payment_number')
        else:
            current_reimbursable_settings.append('payment_number')

        if 'report_id' not in current_ccc_settings:
            if 'claim_number' in current_ccc_settings:
                current_ccc_settings.remove('claim_number')
        else:
            current_ccc_settings.append('claim_number')

        if 'expense_id' not in current_ccc_settings:
            if 'expense_number' in current_ccc_settings:
                current_ccc_settings.remove('expense_number')
        else:
            current_ccc_settings.append('expense_number')

        if 'settlement_id' not in current_ccc_settings:
            if 'payment_number' in current_ccc_settings:
                current_ccc_settings.remove('payment_number')
        else:
            current_ccc_settings.append('payment_number')

        reimbursable_grouped_by.extend(current_reimbursable_settings)
        corporate_credit_card_expenses_grouped_by.extend(current_ccc_settings)

        reimbursable_grouped_by.extend(expense_group_settings['reimbursable_expense_group_fields'])
        corporate_credit_card_expenses_grouped_by.extend(
            expense_group_settings['corporate_credit_card_expense_group_fields']
        )

        reimbursable_grouped_by = list(set(reimbursable_grouped_by))
        corporate_credit_card_expenses_grouped_by = list(set(corporate_credit_card_expenses_grouped_by))

        for field in ALLOWED_FORM_INPUT['export_date_type']:
            if field in reimbursable_grouped_by:
                reimbursable_grouped_by.remove(field)

        for field in ALLOWED_FORM_INPUT['export_date_type']:
            if field in corporate_credit_card_expenses_grouped_by:
                corporate_credit_card_expenses_grouped_by.remove(field)

        if expense_group_settings['reimbursable_export_date_type'] != 'current_date':
            reimbursable_grouped_by.append(expense_group_settings['reimbursable_export_date_type'])

        if expense_group_settings['ccc_export_date_type'] != 'current_date':
            corporate_credit_card_expenses_grouped_by.append(expense_group_settings['ccc_export_date_type'])

        return ExpenseGroupSettings.objects.update_or_create(
            workspace_id=workspace_id,
            defaults={
                'reimbursable_expense_group_fields': reimbursable_grouped_by,
                'corporate_credit_card_expense_group_fields': corporate_credit_card_expenses_grouped_by,
                'expense_state': expense_group_settings['expense_state'],
                'ccc_expense_state': expense_group_settings['ccc_expense_state'],
                'reimbursable_export_date_type': expense_group_settings['reimbursable_export_date_type'],
                'ccc_export_date_type': expense_group_settings['ccc_export_date_type']
            }
        )


def _group_expenses(expenses, group_fields, workspace_id):
    expense_ids = list(map(lambda expense: expense.id, expenses))
    expenses = Expense.objects.filter(id__in=expense_ids).all()

    custom_fields = {}

    for field in group_fields:
        if field.lower() not in ALLOWED_FIELDS:
            group_fields.pop(group_fields.index(field))
            field = ExpenseAttribute.objects.filter(workspace_id=workspace_id,
                                                    attribute_type=field.upper()).first()
            if field:
                custom_fields[field.attribute_type.lower()] = KeyTextTransform(field.display_name, 'custom_properties')

    expense_groups = list(expenses.values(*group_fields, **custom_fields).annotate(
        total=Count('*'), expense_ids=ArrayAgg('id')))
    return expense_groups


def filter_negative_expenses(filtered_expenses):
    return list(filter(lambda expense: expense.amount > 0, filtered_expenses))


def filter_expense_groups(expense_groups, expenses: Expense, expenses_object, expense_group_fields):
    filtered_expense_groups = []

    for expense_group in expense_groups:
        expense_group_expenses_ids = expense_group['expense_ids']

        filtered_expenses = [item for item in expenses if item.id in expense_group_expenses_ids]

        # Export type => Expense Report and Group By => Report
        if expenses_object == 'EXPENSE_REPORT' and 'expense_id' not in expense_group_fields:
            total_amount = sum(expense.amount for expense in filtered_expenses)

            if total_amount < 0:
                filtered_expenses = filter_negative_expenses(filtered_expenses)
        
        # Export type => Journal Entry, Expense Report and Group By => Expense
        elif (expenses_object == 'EXPENSE_REPORT' and 'expense_id' in expense_group_fields):
            filtered_expenses = filter_negative_expenses(filtered_expenses)

        filtered_expense_ids = [item.id for item in filtered_expenses]

        if len(filtered_expense_ids) != 0:
            expense_group['expense_ids'] = filtered_expense_ids
            filtered_expense_groups.append(expense_group)

    return filtered_expense_groups


class ExpenseGroup(models.Model):
    """
    Expense Group
    """
    id = models.AutoField(primary_key=True)
    fund_source = models.CharField(max_length=255, help_text='Expense fund source')
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT,
                                  help_text='To which workspace this expense group belongs to')
    expenses = models.ManyToManyField(Expense, help_text="Expenses under this Expense Group")
    description = JSONField(max_length=255, help_text='Description', null=True)
    response_logs = JSONField(help_text='Reponse log of the export', null=True)
    employee_name = models.CharField(max_length=100, help_text='Expense Group Employee Name', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    export_type = models.CharField(max_length=50, help_text='Expense Group exported as', null=True)
    exported_at = models.DateTimeField(help_text='Exported at', null=True)
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'expense_groups'

    @staticmethod
    def create_expense_groups_by_report_id_fund_source(expense_objects: List[Expense], configuration: Configuration, workspace_id):
        """
        Group expense by and fund_source
        """
        expense_groups = []
        expense_group_settings = ExpenseGroupSettings.objects.get(workspace_id=workspace_id)

        reimbursable_expense_group_fields = expense_group_settings.reimbursable_expense_group_fields
        reimbursable_expenses = list(filter(lambda expense: expense.fund_source == 'PERSONAL', expense_objects))

        reimbursable_expense_groups = _group_expenses(reimbursable_expenses, reimbursable_expense_group_fields, workspace_id)

        filtered_reimbursable_expense_groups = filter_expense_groups(
            reimbursable_expense_groups, reimbursable_expenses, configuration.reimbursable_expenses_object, reimbursable_expense_group_fields
        )

        expense_groups.extend(filtered_reimbursable_expense_groups)

        corporate_credit_card_expense_group_field = expense_group_settings.corporate_credit_card_expense_group_fields
        corporate_credit_card_expenses = list(filter(lambda expense: expense.fund_source == 'CCC', expense_objects))
        corporate_credit_card_expense_groups = _group_expenses(
            corporate_credit_card_expenses, corporate_credit_card_expense_group_field, workspace_id)

        filtered_corporate_credit_card_expense_groups = filter_expense_groups(
            corporate_credit_card_expense_groups, corporate_credit_card_expenses, configuration.corporate_credit_card_expenses_object, corporate_credit_card_expense_group_field
        )

        expense_groups.extend(filtered_corporate_credit_card_expense_groups)

        for expense_group in expense_groups:
            if expense_group_settings.reimbursable_export_date_type == 'last_spent_at':
                expense_group['last_spent_at'] = Expense.objects.filter(
                                                 id__in=expense_group['expense_ids']
                                                 ).order_by('-spent_at').first().spent_at

            if expense_group_settings.ccc_export_date_type == 'last_spent_at':
                expense_group['last_spent_at'] = Expense.objects.filter(
                                                 id__in=expense_group['expense_ids']
                                                 ).order_by('-spent_at').first().spent_at

    
            employee_name = Expense.objects.filter(
                id__in=expense_group['expense_ids']
            ).first().employee_name

            expense_ids = expense_group['expense_ids']
            expense_group.pop('total')
            expense_group.pop('expense_ids')

            for key in expense_group:
                if key in ALLOWED_FORM_INPUT['export_date_type']:
                    if expense_group[key]:
                        expense_group[key] = expense_group[key].strftime('%Y-%m-%dT%H:%M:%S')
                    else:
                        expense_group[key] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

            expense_group_object = ExpenseGroup.objects.create(
                workspace_id=workspace_id,
                fund_source=expense_group['fund_source'],
                description=expense_group,
                employee_name=employee_name
            )

            expense_group_object.expenses.add(*expense_ids)


class Reimbursement(models.Model):
    """
    Reimbursements
    """
    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.PROTECT, help_text='To which workspace this reimbursement belongs to'
    )
    settlement_id = models.CharField(max_length=255, help_text='Fyle Settlement ID')
    reimbursement_id = models.CharField(max_length=255, help_text='Fyle Reimbursement ID')
    payment_number = models.CharField(max_length=255, help_text='Fyle Payment Number', null=True)
    state = models.CharField(max_length=255, help_text='Fyle Reimbursement State')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        unique_together = ('workspace', 'payment_number')
        db_table = 'reimbursements'

    @staticmethod
    def create_or_update_reimbursement_objects(reimbursements: List[Dict], workspace_id):
        """
        Create or Update reimbursement attributes
        """
        reimbursement_id_list = [reimbursement['id'] for reimbursement in reimbursements]
        existing_reimbursements = Reimbursement.objects.filter(
            reimbursement_id__in=reimbursement_id_list, workspace_id=workspace_id).all()

        existing_reimbursement_ids = []
        primary_key_map = {}

        for existing_reimbursement in existing_reimbursements:
            existing_reimbursement_ids.append(existing_reimbursement.reimbursement_id)
            primary_key_map[existing_reimbursement.reimbursement_id] = {
                'id': existing_reimbursement.id,
                'state': existing_reimbursement.state
            }

        attributes_to_be_created = []
        attributes_to_be_updated = []

        for reimbursement in reimbursements:
            reimbursement['state'] = 'COMPLETE' if reimbursement['is_paid'] else 'PENDING'
            if reimbursement['id'] not in existing_reimbursement_ids:
                attributes_to_be_created.append(
                    Reimbursement(
                        settlement_id=reimbursement['settlement_id'],
                        reimbursement_id=reimbursement['id'],
                        state=reimbursement['state'],
                        payment_number=reimbursement['reimbursement_number'],
                        workspace_id=workspace_id
                    )
                )
            else:
                if reimbursement['state'] != primary_key_map[reimbursement['id']]['state']:
                    attributes_to_be_updated.append(
                        Reimbursement(
                            id=primary_key_map[reimbursement['id']]['id'],
                            state=reimbursement['state']
                        )
                    )

        if attributes_to_be_created:
            Reimbursement.objects.bulk_create(attributes_to_be_created, batch_size=50)

        if attributes_to_be_updated:
            Reimbursement.objects.bulk_update(attributes_to_be_updated, fields=['state'], batch_size=50)

    @staticmethod
    def get_last_synced_at(workspace_id: int):
        """
        Get last synced at datetime
        :param workspace_id: Workspace Id
        :return: last_synced_at datetime
        """
        return Reimbursement.objects.filter(
            workspace_id=workspace_id
        ).order_by('-updated_at').first()


class ExpenseFilter(models.Model):
    """
    Reimbursements
    """
    id = models.AutoField(primary_key=True)
    condition = models.CharField(max_length=255, help_text='Condition for the filter')
    operator = models.CharField(max_length=255, choices=EXPENSE_FILTER_OPERATOR, help_text='Operator for the filter')
    values = ArrayField(base_field=models.CharField(max_length=255), null=True, help_text='Values for the operator')
    rank = models.IntegerField(choices=EXPENSE_FILTER_RANK, help_text='Rank for the filter')
    join_by = models.CharField(
        max_length=3,
        null=True,
        choices=EXPENSE_FILTER_JOIN_BY,
        help_text='Used to join the filter (AND/OR)'
    )
    is_custom = models.BooleanField(default=False, help_text='Custom Field or not')
    custom_field_type = models.CharField(
        max_length=255,
        null=True,
        help_text='Custom field type',
        choices=EXPENSE_FILTER_CUSTOM_FIELD_TYPE
    )
    workspace = models.ForeignKey(
        Workspace, 
        on_delete=models.PROTECT,
        help_text='To which workspace these filters belongs to'
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'expense_filters'


class DependentFieldSetting(models.Model):
    """
    Fyle Dependent Fields
    DB Table: dependent_field_settings:
    """
    id = models.AutoField(primary_key=True)
    is_import_enabled = models.BooleanField(help_text='Is Import Enabled')
    project_field_id = models.IntegerField(help_text='Fyle Source Field ID')
    cost_code_field_name = models.CharField(max_length=255, help_text='Fyle Cost Code Field Name')
    cost_code_field_id = models.IntegerField(help_text='Fyle Cost Code Field ID')
    cost_code_placeholder = models.TextField(blank=True, null=True, help_text='Placeholder for Cost code')
    cost_type_field_name = models.CharField(max_length=255, help_text='Fyle Cost Type Field Name')
    cost_type_field_id = models.IntegerField(help_text='Fyle Cost Type Field ID')
    cost_type_placeholder = models.TextField(blank=True, null=True, help_text='Placeholder for Cost Type')
    workspace = models.OneToOneField(
        Workspace,
        on_delete=models.PROTECT, 
        help_text='Reference to Workspace',
        related_name='dependent_field_settings'
    )
    last_successful_import_at = models.DateTimeField(null=True, help_text='Last Successful Import At')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'dependent_field_settings'
