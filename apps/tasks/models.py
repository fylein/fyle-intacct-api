from django.db import models
from django.db.models import JSONField
from fyle_accounting_mappings.models import ExpenseAttribute

from apps.workspaces.models import Workspace
from apps.fyle.models import ExpenseGroup
from apps.sage_intacct.models import Bill, ExpenseReport, ChargeCardTransaction, APPayment, SageIntacctReimbursement, JournalEntry



ERROR_TYPE_CHOICES = (
    ('EMPLOYEE_MAPPING', 'EMPLOYEE_MAPPING'),
    ('CATEGORY_MAPPING', 'CATEGORY_MAPPING'),
    ('INTACCT_ERROR', 'INTACCT_ERROR')
)

def get_default():
    return {
        'default': 'default value'
    }


class TaskLog(models.Model):
    """
    Table to store task logs
    """
    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    type = models.CharField(max_length=50, help_text='Task type (FETCH_EXPENSES / CREATE_BILL / CREATE_EXPENSE_REPORT / CREATE_CHARGE_CARD_TRANSACTION)')
    task_id = models.CharField(max_length=255, null=True, help_text='Fyle Jobs task reference')
    expense_group = models.ForeignKey(ExpenseGroup, on_delete=models.PROTECT,
                                      null=True, help_text='Reference to Expense group')
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, \
        help_text='Reference to Bill', null=True)
    expense_report = models.ForeignKey(ExpenseReport, on_delete=models.PROTECT, \
        help_text='Reference to ExpenseReport', null=True)
    charge_card_transaction = models.ForeignKey(ChargeCardTransaction, on_delete=models.PROTECT, \
        help_text='Reference to ChargeCardTransaction', null=True)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, \
        help_text='Reference to JournalEntry', null=True)
    ap_payment = models.ForeignKey(APPayment, on_delete=models.PROTECT, help_text='Reference to AP Payment', null=True)
    sage_intacct_reimbursement = models.ForeignKey(SageIntacctReimbursement, on_delete=models.PROTECT,
                                                   help_text='Reference to Sage Intacct Reimbursement', null=True)
    status = models.CharField(max_length=255, help_text='Task Status')
    detail = JSONField(help_text='Task Response', null=True, default=get_default)
    sage_intacct_errors = JSONField(help_text='Sage Intacct Errors', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'task_logs'


class Error(models.Model):
    """
    Table to store errors
    """
    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    type = models.CharField(max_length=50, choices=ERROR_TYPE_CHOICES, help_text='Error type')
    expense_group = models.ForeignKey(
        ExpenseGroup, on_delete=models.PROTECT, 
        null=True, help_text='Reference to Expense group'
    )
    expense_attribute = models.OneToOneField(
        ExpenseAttribute, on_delete=models.PROTECT,
        null=True, help_text='Reference to Expense Attribute'
    )
    is_resolved = models.BooleanField(default=False, help_text='Is resolved')
    is_parsed = models.BooleanField(default=False, help_text='Is parsed')
    attribute_type = models.CharField(max_length=255, null=True, blank=True, help_text='Error Attribute type')
    article_link = models.TextField(null=True, blank=True, help_text='Article link')
    error_title = models.CharField(max_length=255, help_text='Error title')
    error_detail = models.TextField(help_text='Error detail')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'errors'
