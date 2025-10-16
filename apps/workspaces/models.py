from functools import cache

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import JSONField
from django_q.models import Schedule
from fyle_accounting_library.fyle_platform.enums import CacheKeyEnum
from fyle_accounting_mappings.mixins import AutoAddCreateUpdateInfoMixin

User = get_user_model()


ONBOARDING_STATE_CHOICES = (
    ('CONNECTION', 'CONNECTION'),
    ('LOCATION_ENTITY_MAPPINGS', 'LOCATION_ENTITY_MAPPINGS'),
    ('EXPORT_SETTINGS', 'EXPORT_SETTINGS'),
    ('IMPORT_SETTINGS', 'IMPORT_SETTINGS'),
    ('ADVANCED_CONFIGURATION', 'ADVANCED_CONFIGURATION'),
    ('COMPLETE', 'COMPLETE')
)

EXPORT_MODE_CHOICES = (
    ('MANUAL', 'MANUAL'),
    ('AUTO', 'AUTO')
)

APP_VERSION_CHOICES = (
    ('v1', 'v1'),
    ('v2', 'v2')
)

CODE_IMPORT_FIELD_CHOICES = (
    ('PROJECT', 'PROJECT'),
    ('ACCOUNT', 'ACCOUNT'),
    ('EXPENSE_TYPE', 'EXPENSE_TYPE'),
    ('_ACCOUNT', '_ACCOUNT'),
    ('_EXPENSE_TYPE', '_EXPENSE_TYPE'),
    ('DEPARTMENT', 'DEPARTMENT')
)


REIMBURSABLE_EXPENSES_OBJECT_CHOICES = (
    ('EXPENSE_REPORT', 'EXPENSE_REPORT'),
    ('BILL', 'BILL'),
    ('JOURNAL_ENTRY', 'JOURNAL_ENTRY')
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

EMPLOYEE_FIELD_MAPPING_CHOICES = (
    ('EMPLOYEE', 'EMPLOYEE'),
    ('VENDOR', 'VENDOR')
)


def get_default_onboarding_state() -> str:
    """
    Default onboarding state
    """
    return 'CONNECTION'


def get_default_memo_fields() -> list:
    """
    Default memo fields
    """
    return ['employee_email', 'category', 'spent_on', 'report_number', 'purpose', 'expense_link']


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
    ccc_last_synced_at = models.DateTimeField(help_text='Datetime when ccc expenses were pulled last', null=True)
    source_synced_at = models.DateTimeField(help_text='Datetime when source dimensions were pulled', null=True)
    destination_synced_at = models.DateTimeField(help_text='Datetime when destination dimensions were pulled', null=True)
    app_version = models.CharField(max_length=2, help_text='App version', default='v1', choices=APP_VERSION_CHOICES)
    onboarding_state = models.CharField(
        max_length=50, choices=ONBOARDING_STATE_CHOICES, default=get_default_onboarding_state,
        help_text='Onboarding status of the workspace', null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'workspaces'


class Configuration(AutoAddCreateUpdateInfoMixin, models.Model):
    """
    Workspace General Settings
    """
    id = models.AutoField(primary_key=True, help_text='Unique Id to identify a workspace')
    workspace = models.OneToOneField(
        Workspace,
        on_delete=models.PROTECT,
        help_text='Reference to Workspace model',
        related_name='configurations'
    )
    employee_field_mapping = models.CharField(
        max_length=50,
        choices=EMPLOYEE_FIELD_MAPPING_CHOICES,
        help_text='Employee field mapping',
        null=True
    )
    reimbursable_expenses_object = models.CharField(
        max_length=50, choices=REIMBURSABLE_EXPENSES_OBJECT_CHOICES, help_text='Mapping Settings ( BILL / EXPENSE_REPORT )', null = True
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
    top_level_memo_structure = ArrayField(
        base_field=models.CharField(max_length=100), default=list, help_text='list of system fields for creating custom description for top level'
    )
    auto_create_destination_entity = models.BooleanField(default=False, help_text='Auto create vendor / employee')
    is_journal_credit_billable = models.BooleanField(default=False, help_text='Billable on journal entry credit line')
    change_accounting_period = models.BooleanField(default=True, help_text='Change the accounting period')
    import_vendors_as_merchants = models.BooleanField(default=False, help_text='Auto import vendors from sage intacct '
                                                                               'as merchants to Fyle')

    use_merchant_in_journal_line = models.BooleanField(default=False, help_text='Export merchant as vendor in journal entry line item')
    auto_create_merchants_as_vendors = models.BooleanField(default=False, help_text='Auto create merchants as vendors in sage intacct')
    import_code_fields = ArrayField(
        base_field=models.CharField(max_length=100, choices=CODE_IMPORT_FIELD_CHOICES),
        help_text='Array Field to store code-naming preference',
        blank=True, default=list
    )
    skip_accounting_export_summary_post = models.BooleanField(default=False, help_text='Skip accounting export summary post')
    je_single_credit_line = models.BooleanField(default=False, help_text='Single credit line in journal entry')
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
    si_company_name = models.TextField(help_text='Stores Sage Intacct company name', null=True)
    si_user_password = models.TextField(help_text='Stores Sage Intacct user password')
    is_expired = models.BooleanField(default=False, help_text='Sage Intacct Password expiry flag')
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'sage_intacct_credentials'

    @staticmethod
    def get_active_sage_intacct_credentials(workspace_id: int) -> 'SageIntacctCredential':
        """
        Get active Sage Intacct credentials
        :param workspace_id: Workspace ID
        :return: Sage Intacct credentials
        """
        return SageIntacctCredential.objects.get(workspace_id=workspace_id, is_expired=False)


class FyleCredential(models.Model):
    """
    Table to store Fyle credentials
    """
    id = models.AutoField(primary_key=True)
    refresh_token = models.TextField(help_text='Stores Fyle refresh token')
    cluster_domain = models.TextField(null=True, help_text='Cluster Domain')
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'fyle_credentials'


class WorkspaceSchedule(models.Model):
    """
    Workspace Schedule
    """
    id = models.AutoField(primary_key=True, help_text='Unique Id to identify a schedule')
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model', related_name='workspace_schedules')
    enabled = models.BooleanField(default=False)
    start_datetime = models.DateTimeField(help_text='Datetime for start of schedule', null=True)
    interval_hours = models.IntegerField(null=True)
    error_count = models.IntegerField(null=True, help_text='Number of errors in export')
    additional_email_options = JSONField(default=list, help_text='Email and Name of person to send email', null=True)
    emails_selected = ArrayField(base_field=models.CharField(max_length=255), null=True, help_text='Emails that has to be send mail')
    is_real_time_export_enabled = models.BooleanField(default=False)
    schedule = models.OneToOneField(Schedule, on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, null=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'workspace_schedules'


class LastExportDetail(models.Model):
    """
    Table to store Last Export Details
    """
    id = models.AutoField(primary_key=True)
    last_exported_at = models.DateTimeField(help_text='Last exported at datetime', null=True)
    next_export_at = models.DateTimeField(help_text='next export datetime', null=True)
    export_mode = models.CharField(
        max_length=50, help_text='Mode of the export Auto / Manual', choices=EXPORT_MODE_CHOICES, null=True
    )
    total_expense_groups_count = models.IntegerField(help_text='Total count of expense groups exported', null=True)
    successful_expense_groups_count = models.IntegerField(help_text='count of successful expense_groups ', null=True)
    failed_expense_groups_count = models.IntegerField(help_text='count of failed expense_groups ', null=True)
    unmapped_card_count = models.IntegerField(help_text='count of unmapped card', default=0)
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'last_export_details'


class FeatureConfig(models.Model):
    """
    Table to store Feature configs
    """
    id = models.AutoField(primary_key=True)
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    export_via_rabbitmq = models.BooleanField(default=True, help_text='Enable export via rabbitmq')
    import_via_rabbitmq = models.BooleanField(default=True, help_text='Enable import via rabbitmq')
    fyle_webhook_sync_enabled = models.BooleanField(default=False, help_text='Enable fyle attribute webhook sync')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    @classmethod
    def get_feature_config(cls, workspace_id: int, key: str) -> bool:
        """
        Get cached feature config value for workspace
        Cache for 48 hours (172800 seconds)
        :param workspace_id: workspace id
        :param key: feature config key (export_via_rabbitmq, import_via_rabbitmq, fyle_webhook_sync_enabled)
        :return: Boolean value for the requested feature
        """
        cache_key_map = {
            'export_via_rabbitmq': CacheKeyEnum.FEATURE_CONFIG_EXPORT_VIA_RABBITMQ,
            'fyle_webhook_sync_enabled': CacheKeyEnum.FEATURE_CONFIG_FYLE_WEBHOOK_SYNC_ENABLED
        }

        cache_key_enum = cache_key_map.get(key)
        cache_key = cache_key_enum.value.format(workspace_id=workspace_id)
        cached_value = cache.get(cache_key)

        if cached_value is not None:
            return cached_value

        feature_config = cls.objects.get(workspace_id=workspace_id)
        value = getattr(feature_config, key)
        cache.set(cache_key, value, 172800)
        return value

    class Meta:
        db_table = 'feature_configs'
