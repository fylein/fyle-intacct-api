from datetime import datetime, timezone

import pytest

from apps.workspaces.models import FyleCredential, LastExportDetail, SageIntacctCredential, Workspace
from apps.fyle.models import ExpenseGroupSettings


@pytest.fixture
def add_workspace_to_database():
    """
    Add worksapce to database fixture
    """
    workspace = Workspace.objects.create(
        id=100,
        name = 'Fyle for labhvam2',
        fyle_org_id = 'l@bhv@m2',
        xero_short_code = '',
        last_synced_at = None,
        source_synced_at = None,
        destination_synced_at = None,
        xero_accounts_last_synced_at = datetime.now(tz=timezone.utc),
        created_at = datetime.now(tz=timezone.utc),
        updated_at = datetime.now(tz=timezone.utc)
    )

    LastExportDetail.objects.create(workspace_id=100)
    workspace.save()


@pytest.fixture()
def add_sage_intacct_credentials(db):
    """
    Add Sage Intacct credentials to database fixture
    """
    workspace_id = 2
    Workspace.objects.update_or_create(
        id=workspace_id,
        defaults={
            'name': f'Test Workspace {workspace_id}',
            'fyle_org_id': f'fyle_org_{workspace_id}'
        }
    )
    LastExportDetail.objects.update_or_create(workspace_id=workspace_id)

    SageIntacctCredential.objects.create(
        refresh_token = '',
        workspace_id = workspace_id
    )


@pytest.fixture()
def add_fyle_credentials(db):
    """
    Add Fyle credentials to database fixture
    """
    workspace_id = 2
    Workspace.objects.update_or_create(
        id=workspace_id,
        defaults={
            'name': f'Test Workspace {workspace_id}',
            'fyle_org_id': f'fyle_org_{workspace_id}'
        }
    )
    LastExportDetail.objects.update_or_create(workspace_id=workspace_id)

    FyleCredential.objects.create(
        refresh_token='dummy_refresh_token',
        workspace_id=workspace_id,
        cluster_domain='https://staging.fyle.tech'
    )


@pytest.fixture()
def add_workspace_with_settings(db):
    """
    Add workspace with all required settings for export settings tests
    """
    def _create_workspace(workspace_id: int):
        Workspace.objects.update_or_create(
            id=workspace_id,
            defaults={
                'name': f'Test Workspace {workspace_id}',
                'fyle_org_id': f'fyle_org_{workspace_id}'
            }
        )
        LastExportDetail.objects.update_or_create(workspace_id=workspace_id)

        ExpenseGroupSettings.objects.update_or_create(
            workspace_id=workspace_id,
            defaults={
                'reimbursable_expense_group_fields': ['employee_email', 'report_id', 'claim_number', 'fund_source'],
                'corporate_credit_card_expense_group_fields': ['fund_source', 'employee_email', 'claim_number', 'expense_id', 'report_id'],
                'expense_state': 'PAYMENT_PROCESSING',
                'reimbursable_export_date_type': 'current_date',
                'ccc_export_date_type': 'current_date'
            }
        )
        return workspace_id

    return _create_workspace
