from datetime import datetime, timezone

import pytest
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute

from apps.fyle.models import Expense, ExpenseGroup, ExpenseGroupSettings
from apps.tasks.models import Error
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


@pytest.fixture
def add_category_test_expense(db):
    """
    Add a category test expense
    """
    workspace = Workspace.objects.get(id=1)
    expense = Expense.objects.create(
        workspace_id=workspace.id,
        expense_id='txCategoryTest',
        employee_email='category.test@test.com',
        employee_name='Category Test User',
        category='Test Category',
        amount=100,
        currency='USD',
        org_id=workspace.fyle_org_id,
        settlement_id='setlCat',
        report_id='rpCat',
        spent_at='2024-01-01T00:00:00Z',
        expense_created_at='2024-01-01T00:00:00Z',
        expense_updated_at='2024-01-01T00:00:00Z',
        fund_source='PERSONAL'
    )
    return expense


@pytest.fixture
def add_category_test_expense_group(db, add_category_test_expense):
    """
    Add a category test expense group
    """
    workspace = Workspace.objects.get(id=1)
    expense = add_category_test_expense
    expense_group = ExpenseGroup.objects.create(
        workspace_id=workspace.id,
        fund_source='PERSONAL',
        description={'employee_email': expense.employee_email},
        employee_name=expense.employee_name
    )
    expense_group.expenses.add(expense)
    return expense_group


@pytest.fixture
def add_category_mapping_error(db, add_category_test_expense_group):
    """
    Add a category mapping error
    """
    workspace = Workspace.objects.get(id=1)
    expense_group = add_category_test_expense_group
    error = Error.objects.create(
        workspace_id=workspace.id,
        type='CATEGORY_MAPPING',
        is_resolved=False,
        mapping_error_expense_group_ids=[expense_group.id]
    )
    return error


@pytest.fixture
def add_category_expense_attribute(db):
    """
    Add a category expense attribute
    """
    workspace = Workspace.objects.get(id=1)
    expense_attribute = ExpenseAttribute.objects.create(
        workspace_id=workspace.id,
        attribute_type='CATEGORY',
        value='Test Category Attribute',
        display_name='Category',
        source_id='catTest123'
    )
    return expense_attribute


@pytest.fixture
def add_destination_attributes_for_category(db):
    """
    Add destination attributes for category
    """
    workspace = Workspace.objects.get(id=1)
    account = DestinationAttribute.objects.create(
        workspace_id=workspace.id,
        attribute_type='ACCOUNT',
        value='Test Account',
        display_name='ACCOUNT',
        destination_id='ACC123'
    )
    expense_head = DestinationAttribute.objects.create(
        workspace_id=workspace.id,
        attribute_type='EXPENSE_TYPE',
        value='Test Expense Head',
        display_name='EXPENSE_TYPE',
        destination_id='EXP123'
    )
    return {'account': account, 'expense_head': expense_head}
