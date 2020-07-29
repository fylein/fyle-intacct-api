from django.db import models
from django.contrib.postgres.fields import JSONField

from apps.workspaces.models import Workspace
from apps.fyle.models import ExpenseGroup
from apps.sage_intacct.models import Bill, ExpenseReport


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
    type = models.CharField(max_length=50, help_text='Task type (FETCH_EXPENSES / CREATE_BILL / CREATE_EXPENSE)')
    task_id = models.CharField(max_length=255, null=True, help_text='Fyle Jobs task reference')
    expense_group = models.ForeignKey(ExpenseGroup, on_delete=models.PROTECT,
                                      null=True, help_text='Reference to Expense group')
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, \
        help_text='Reference to Bill', null=True)
    expense_report = models.ForeignKey(ExpenseReport, on_delete=models.PROTECT, \
        help_text='Reference to ExpenseReport', null=True)
    status = models.CharField(max_length=255, help_text='Task Status')
    detail = JSONField(help_text='Task Response', null=True, default=get_default)
    sage_intacct_errors = JSONField(help_text='Sage Intacct Errors', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'task_logs'
