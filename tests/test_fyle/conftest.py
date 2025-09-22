import pytest

from datetime import datetime, timezone
from apps.workspaces.models import Workspace
from apps.fyle.models import ExpenseGroupSettings


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
