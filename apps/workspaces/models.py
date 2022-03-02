"""
Workspace Models
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django_q.models import Schedule

User = get_user_model()


class Workspace(models.Model):
    """
    Workspace model
    """
    id = models.AutoField(primary_key=True, help_text='Unique Id to identify a workspace')
    name = models.CharField(max_length=255, help_text='Name of the workspace')
    user = models.ManyToManyField(User, help_text='Reference to users table')
    fyle_org_id = models.CharField(max_length=255, help_text='org id', unique=True)
    cluster_domain = models.CharField(max_length=255, help_text='Cluster Domain', null=True)
    last_synced_at = models.DateTimeField(help_text='Datetime when expenses were pulled last', null=True)
    source_synced_at = models.DateTimeField(help_text='Datetime when source dimensions were pulled', null=True)
    destination_synced_at = models.DateTimeField(help_text='Datetime when destination dimensions were pulled', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'workspaces'


REIMBURSABLE_EXPENSES_OBJECT_CHOICES = (
    ('EXPENSE_REPORT', 'EXPENSE_REPORT'),
    ('BILL', 'BILL')
)

COPORATE_CARD_EXPENSES_OBJECT_CHOICES = (
    ('EXPENSE_REPORT', 'EXPENSE_REPORT'),
    ('BILL', 'BILL'),
    ('CHARGE_CARD_TRANSACTION', 'CHARGE_CARD_TRANSACTION'),
    ('JOURNAL_ENTRY', 'JOURNAL_ENTRY')
)

AUTO_MAP_EMPLOYEE_CHOICES = (
    ('EMAIL', 'EMAIL'),
    ('NAME', 'NAME'),
    ('EMPLOYEE_CODE', 'EMPLOYEE_CODE'),
)


def get_default_memo_fields():
    return ['employee_email', 'category', 'spent_on', 'report_number', 'purpose', 'expense_link']


class Configuration(models.Model):
    """
    Workspace General Settings
    """
    id = models.AutoField(primary_key=True, help_text='Unique Id to identify a workspace')
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    reimbursable_expenses_object = models.CharField(
        max_length=50, choices=REIMBURSABLE_EXPENSES_OBJECT_CHOICES, help_text='Mapping Settings ( BILL / EXPENSE_REPORT )'
    )
    corporate_credit_card_expenses_object = models.CharField(
        max_length=50, choices=COPORATE_CARD_EXPENSES_OBJECT_CHOICES, 
        help_text='Mapping Settings ( BILL / CHARGE_CARD_TRANSACTION )', null=True
    )
    import_projects = models.BooleanField(default=False, help_text='Auto import projects to Fyle')
    import_categories = models.BooleanField(default=False, help_text='Auto import caimport_categories to Fyle')
    sync_fyle_to_sage_intacct_payments = models.BooleanField(default=False, help_text='Auto Sync Payments from Fyle '
                                                                                      'to Sage Intacct')
    sync_sage_intacct_to_fyle_payments = models.BooleanField(default=False, help_text='Auto Sync Payments from Sage '
                                                                                      'Intacct to Fyle')
    auto_map_employees = models.CharField(
        max_length=50, choices=AUTO_MAP_EMPLOYEE_CHOICES,
        help_text='Auto Map Employees type from Sage Intacct to Fyle', null=True
    )
    import_tax_codes = models.BooleanField(default=False, help_text='Auto import tax codes to Fyle', null=True)
    memo_structure = ArrayField(
        base_field=models.CharField(max_length=100), default=get_default_memo_fields,
        help_text='list of system fields for creating custom memo'
    )
    auto_create_destination_entity = models.BooleanField(default=False, help_text='Auto create vendor / employee')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'configurations'


class SageIntacctCredential(models.Model):
    """
    Table to store Sage Intacct credentials
    """
    id = models.AutoField(primary_key=True)
    si_user_id = models.TextField(help_text='Stores Sage Intacct user id')
    si_company_id = models.TextField(help_text='Stores Sage Intacct company id')
    si_company_name = models.TextField(help_text='Stores Sage Intacct company name')
    si_user_password = models.TextField(help_text='Stores Sage Intacct user password')
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'sage_intacct_credentials'


class FyleCredential(models.Model):
    """
    Table to store Fyle credentials
    """
    id = models.AutoField(primary_key=True)
    refresh_token = models.TextField(help_text='Stores Fyle refresh token')
    cluster_domain = models.TextField(null=True, help_text='Cluster Domain')
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    cluster_domain = models.TextField(null=True, help_text='Cluster Domain')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'fyle_credentials'


class WorkspaceSchedule(models.Model):
    """
    Workspace Schedule
    """
    id = models.AutoField(primary_key=True, help_text='Unique Id to identify a schedule')
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    enabled = models.BooleanField(default=False)
    start_datetime = models.DateTimeField(help_text='Datetime for start of schedule', null=True)
    interval_hours = models.IntegerField(null=True)
    schedule = models.OneToOneField(Schedule, on_delete=models.PROTECT, null=True)

    class Meta:
        db_table = 'workspace_schedules'
