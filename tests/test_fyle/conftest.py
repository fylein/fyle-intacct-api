from datetime import datetime, timezone

import pytest
from fyle_accounting_mappings.models import ExpenseAttribute

from apps.fyle.models import ExpenseGroupSettings
from apps.workspaces.models import FeatureConfig, Workspace


@pytest.fixture
def create_temp_workspace(db):
    """
    Create a workspace fixture
    """
    workspace = Workspace.objects.create(
        id=98,
        name = 'Fyle for Testing',
        fyle_org_id = 'Testing',
        last_synced_at = None,
        source_synced_at = None,
        destination_synced_at = None,
        created_at = datetime.now(tz=timezone.utc),
        updated_at = datetime.now(tz=timezone.utc)
    )

    workspace.save()

    ExpenseGroupSettings.objects.create(
        reimbursable_expense_group_fields='{employee_email,report_id,claim_number,fund_source}',
        corporate_credit_card_expense_group_fields='{fund_source,employee_email,claim_number,expense_id,report_id}',
        expense_state='PAYMENT PROCESSING',
        workspace_id=98,
        reimbursable_export_date_type='current_date',
        ccc_export_date_type='current_date'
    )


@pytest.fixture
def add_webhook_attribute_data(db):
    """
    Create test data for webhook attribute processing
    """
    workspace = Workspace.objects.get(id=1)
    FeatureConfig.objects.update_or_create(
        workspace=workspace,
        defaults={
            'export_via_rabbitmq': False,
            'import_via_rabbitmq': False,
            'fyle_webhook_sync_enabled': True
        }
    )
    ExpenseAttribute.objects.create(
        workspace_id=workspace.id,
        attribute_type='CATEGORY',
        display_name='Category',
        value='Webhook Test Food',
        source_id='cat_webhook_food_123',
        active=True
    )
    ExpenseAttribute.objects.create(
        workspace_id=workspace.id,
        attribute_type='PROJECT',
        display_name='Project',
        value='Webhook Marketing Project',
        source_id='proj_webhook_marketing_456',
        active=True
    )
