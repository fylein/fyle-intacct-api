from unittest.mock import Mock

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

    # Test with default credentials (use_real_intacct_credentials=False)
    service = E2ESetupService(workspace_id=workspace_id, use_real_intacct_credentials=False)

    # Execute the full setup
    service.setup_organization()

    # Verify that intacct credentials were mocked out
    credential = SageIntacctCredential.objects.get(workspace=workspace)
    assert credential.si_user_id == 'e2e_test_user'
    assert credential.si_company_id == 'E2E_TEST_COMPANY'
    assert credential.si_user_password == 'encrypted_password'

    # Verify Phase 1 data creation
    assert ExpenseGroupSettings.objects.filter(workspace=workspace).exists()
    assert LastExportDetail.objects.filter(workspace_id=workspace_id).exists()
    assert LocationEntityMapping.objects.filter(workspace=workspace).exists()
    assert Configuration.objects.filter(workspace=workspace).exists()
    assert GeneralMapping.objects.filter(workspace=workspace).exists()
    assert WorkspaceSchedule.objects.filter(workspace=workspace).exists()

    # Verify Phase 2 data creation
    assert Expense.objects.filter(workspace=workspace).count() == 22
    assert ExpenseGroup.objects.filter(workspace=workspace).exists()
    assert TaskLog.objects.filter(workspace=workspace).exists()
    assert Bill.objects.filter(expense_group__workspace=workspace).exists()
    assert ChargeCardTransaction.objects.filter(expense_group__workspace=workspace).exists()


def test_e2e_setup_with_real_intacct_credentials(mocker, db):
    """
    Test E2ESetupService with real Intacct credentials from settings
    """
    workspace_id = 3

    # Create initial workspace
    workspace = Workspace.objects.create(
        id=workspace_id,
        name='Real Credentials Workspace',
        fyle_org_id='test_org_002'
    )

    # Test with real credentials (use_real_intacct_credentials=True)
    service = E2ESetupService(workspace_id=workspace_id, use_real_intacct_credentials=True)

    # Mock settings variables
    mock_settings = Mock()
    mock_settings.E2E_TEST_USER_ID = 'real_user_123'
    mock_settings.E2E_TEST_COMPANY_ID = 'REAL_COMPANY_456'
    mock_settings.E2E_TEST_USER_PASSWORD = 'real_password_789'
    mocker.patch('apps.internal.services.e2e_setup.settings', mock_settings)

    # Execute Phase 1 setup to test credentials
    service._setup_phase1_core_data()

    # Verify SageIntacctCredential with real values from settings
    credential = SageIntacctCredential.objects.get(workspace=workspace)
    assert credential.si_user_id == 'real_user_123'
    assert credential.si_company_id == 'REAL_COMPANY_456'
    assert credential.si_user_password == 'real_password_789'
