from django.utils import timezone

from apps.fyle.models import Expense, ExpenseGroup, ExpenseGroupSettings
from apps.internal.services.e2e_setup import E2ESetupService
from apps.internal.services.fixture_factory import FixtureFactory
from apps.mappings.models import GeneralMapping, LocationEntityMapping
from apps.sage_intacct.models import Bill, ChargeCardTransaction
from apps.tasks.models import TaskLog
from apps.workspaces.models import Configuration, LastExportDetail, SageIntacctCredential, Workspace, WorkspaceSchedule


def test_e2e_setup_service_init(db):
    """
    Test E2ESetupService initialization
    """
    workspace_id = 2
    service = E2ESetupService(workspace_id=workspace_id)

    assert service.workspace_id == workspace_id
    assert service.fixture_factory is not None
    assert isinstance(service.fixture_factory, FixtureFactory)


def test_setup_organization_complete_flow(mocker, db):
    """
    Test complete organization setup flow with real services
    """
    workspace_id = 2

    # Create initial workspace
    workspace = Workspace.objects.create(
        id=workspace_id,
        name='Initial Workspace',
        fyle_org_id='test_org_001'
    )

    service = E2ESetupService(workspace_id=workspace_id)

    # Mock only external dependencies
    mocker.patch('apps.internal.services.e2e_setup.os.getenv', side_effect=lambda key, default: {
        'SI_USER_ID': 'test_user_123',
        'SI_COMPANY_ID': 'TEST_COMPANY_456',
        'SI_USER_PASSWORD': 'secure_password_789'
    }.get(key, default))

    mocker.patch('apps.internal.services.e2e_setup.timezone.now',
                 return_value=timezone.now())

    # Execute the full setup
    result = service.setup_organization()

    # Verify return value
    assert result['workspace_id'] == workspace_id
    assert result['org_name'] == 'E2E Integration Tests'

    # Verify workspace was updated
    workspace.refresh_from_db()
    assert workspace.name == 'E2E Integration Tests'

    # Verify Phase 1 data creation
    assert ExpenseGroupSettings.objects.filter(workspace=workspace).exists()
    assert LastExportDetail.objects.filter(workspace_id=workspace_id).exists()
    assert SageIntacctCredential.objects.filter(workspace=workspace).exists()
    assert LocationEntityMapping.objects.filter(workspace=workspace).exists()
    assert Configuration.objects.filter(workspace=workspace).exists()
    assert GeneralMapping.objects.filter(workspace=workspace).exists()
    assert WorkspaceSchedule.objects.filter(workspace=workspace).exists()

    # Verify Phase 2 data creation
    assert Expense.objects.filter(workspace=workspace).count() == 10
    assert ExpenseGroup.objects.filter(workspace=workspace).exists()
    assert TaskLog.objects.filter(workspace=workspace).exists()
    assert Bill.objects.filter(expense_group__workspace=workspace).exists()
    assert ChargeCardTransaction.objects.filter(expense_group__workspace=workspace).exists()
