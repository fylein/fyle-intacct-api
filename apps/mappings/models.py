"""
Mapping Models
"""
from django.db import models
from django.db.models import JSONField

from apps.workspaces.models import Workspace


IMPORT_STATUS_CHOICES= (
    ('FATAL', 'FATAL'),
    ('COMPLETE', 'COMPLETE'),
    ('IN_PROGRESS', 'IN_PROGRESS'),
    ('FAILED', 'FAILED')
)

class LocationEntityMapping(models.Model):
    """
    Location Entity Mapping
    """
    id = models.AutoField(primary_key=True)
    location_entity_name = models.CharField(max_length=255, help_text='SageIntacct Location Entity Name')
    country_name = models.CharField(max_length=255, help_text='SageIntacct Location Entities Country', null=True)
    destination_id = models.CharField(max_length=255, help_text='SageIntacct location entity id', null=True)
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'location_entity_mappings'

class GeneralMapping(models.Model):
    """
    General Mappings
    """
    id = models.AutoField(primary_key=True)
    location_entity_name = models.CharField(max_length=255, help_text='Location Entity name', null=True)
    location_entity_id = models.CharField(max_length=255, help_text='Location Entity ID', null=True)
    default_location_name = models.CharField(max_length=255, help_text='Default location name', null=True)
    default_location_id = models.CharField(max_length=255, help_text='Default location ID', null=True)
    default_department_name = models.CharField(max_length=255, help_text='Default department name', null=True)
    default_department_id = models.CharField(max_length=255, help_text='Default department ID', null=True)
    default_class_name = models.CharField(max_length=255, help_text='Default class name', null=True)
    default_class_id = models.CharField(max_length=255, help_text='Default class ID', null=True)
    default_project_name = models.CharField(max_length=255, help_text='Default project name', null=True)
    default_project_id = models.CharField(max_length=255, help_text='Default project ID', null=True)
    default_charge_card_name = models.CharField(max_length=255, help_text='Default charge card name', null=True)
    default_charge_card_id = models.CharField(max_length=255, help_text='Default charge card ID', null=True)
    default_credit_card_name = models.CharField(max_length=255, help_text='Default credit card name', null=True)
    default_credit_card_id = models.CharField(max_length=255, help_text='Default credit card ID', null=True)
    default_gl_account_name = models.CharField(max_length=255, help_text='Default credit card name', null=True)
    default_gl_account_id = models.CharField(max_length=255, help_text='Default credit card ID', null=True)
    default_ccc_vendor_name = models.CharField(max_length=255, help_text='Default ccc vendor name', null=True)
    default_ccc_vendor_id = models.CharField(max_length=255, help_text='Default ccc vendor ID', null=True)
    default_item_name = models.CharField(max_length=255, help_text='Default item name', null=True)
    default_item_id = models.CharField(max_length=255, help_text='Default item ID', null=True)
    default_tax_code_id = models.CharField(max_length=255, help_text='DEfault Tax Code Id', null=True)
    default_tax_code_name = models.CharField(max_length=255, help_text='DEfault Tax Code Id', null=True)
    payment_account_id = models.CharField(max_length=255, help_text='Sage Intacct Payment Account id', null=True)
    payment_account_name = models.CharField(max_length=255, help_text='Sage Intacct Payment Account name', null=True)
    default_reimbursable_expense_payment_type_id = models.CharField(
        max_length=255, help_text='Default Expense Payment Type ID for reimbursable expenses', null=True)
    default_reimbursable_expense_payment_type_name = models.CharField(
        max_length=255, help_text='Default Expense Payment Type Name for reimbursable expenses', null=True)
    default_ccc_expense_payment_type_id = models.CharField(
        max_length=255, help_text='Default Expense Payment Type ID for ccc expenses', null=True)
    default_ccc_expense_payment_type_name = models.CharField(
        max_length=255, help_text='Default Expense Payment Type Name for ccc expenses', null=True)
    use_intacct_employee_departments = models.BooleanField(default=False, help_text='Use SageIntacct Employee Default '
                                                                                    'Department')
    use_intacct_employee_locations = models.BooleanField(default=False, help_text='Use SageIntacct Employee Default '
                                                                                  'Location')
    workspace = models.OneToOneField(
        Workspace,
        on_delete=models.PROTECT,
        help_text='Reference to Workspace model',
        related_name='general_mappings'
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'general_mappings'


class ImportLog(models.Model):
    """
    Table to store import logs
    """
    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    attribute_type = models.CharField(max_length=150, help_text='Attribute type')
    status = models.CharField(max_length=255, help_text='Status', choices=IMPORT_STATUS_CHOICES, null=True)
    error_log = JSONField(help_text='Error Log', default=list)
    total_batches_count = models.IntegerField(help_text='Queued batches', default=0)
    processed_batches_count = models.IntegerField(help_text='Processed batches', default=0)
    last_successful_run_at = models.DateTimeField(help_text='Last successful run', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'import_logs'
        unique_together = ('workspace', 'attribute_type')
