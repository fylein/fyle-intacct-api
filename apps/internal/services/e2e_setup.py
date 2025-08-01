import logging

from django.conf import settings
from django.utils import timezone

from apps.fyle.models import ExpenseAttribute, ExpenseGroupSettings
from apps.internal.services.fixture_factory import FixtureFactory
from apps.mappings.models import GeneralMapping, LocationEntityMapping
from apps.sage_intacct.models import DestinationAttribute
from apps.workspaces.models import Configuration, LastExportDetail, SageIntacctCredential, Workspace, WorkspaceSchedule

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class E2ESetupService:
    """Service for setting up E2E test fixture data"""

    def __init__(self, workspace_id: int, use_real_intacct_credentials: bool = False) -> None:
        self.workspace_id = workspace_id
        self.fixture_factory = FixtureFactory()
        self.use_real_intacct_credentials = use_real_intacct_credentials

    def setup_organization(self) -> dict:
        """Main method to set up the test organization"""
        logger.info("Starting E2E setup")

        # Phase 1: Core setup (Parent Org - Clone Setting)
        workspace = self._setup_phase1_core_data()

        # Phase 2: Advanced test data
        self._setup_phase2_advanced_data(workspace)

        return {
            "workspace_id": workspace.id,
            "org_name": workspace.name
        }

    def _setup_phase1_core_data(self) -> Workspace:
        """Set up Phase 1: Core data required for clone setting (parent org)"""
        logger.info("Setting up Phase 1: Core data (Parent Org - Clone Setting)")

        # 1. Create expense_group_settings
        workspace = Workspace.objects.get(id=self.workspace_id)
        ExpenseGroupSettings.objects.update_or_create(
            workspace=workspace,
            defaults={
                'reimbursable_expense_group_fields': ['employee_email', 'report_id', 'claim_number', 'fund_source'],
                'corporate_credit_card_expense_group_fields': ['employee_email', 'report_id', 'claim_number', 'fund_source'],
                'expense_state': 'PAYMENT_PROCESSING',
                'ccc_expense_state': 'PAID'
            }
        )

        # 2. Create last_export_details
        LastExportDetail.objects.update_or_create(
            workspace_id=workspace.id,
            defaults={
                'last_exported_at': None,
                'export_mode': 'MANUAL',
                'total_expense_groups_count': 0,
                'successful_expense_groups_count': 0,
                'failed_expense_groups_count': 0
            }
        )

        # 3. Create Sage Intacct credentials (from env)
        si_user_id = 'e2e_test_user'
        si_company_id = 'E2E_TEST_COMPANY'
        si_user_password = 'encrypted_password'
        if self.use_real_intacct_credentials:
            si_user_id = settings.E2E_TEST_USER_ID or si_user_id
            si_company_id = settings.E2E_TEST_COMPANY_ID or si_company_id
            si_user_password = settings.E2E_TEST_USER_PASSWORD or si_user_password

        SageIntacctCredential.objects.create(
            workspace=workspace,
            si_user_id=si_user_id,
            si_company_id=si_company_id,
            si_user_password=si_user_password,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 4. Create location_entity_mappings
        LocationEntityMapping.objects.create(
            workspace=workspace,
            location_entity_name='E2E Test Location',
            country_name='United States',
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 5. Create configurations
        Configuration.objects.create(
            workspace=workspace,
            employee_field_mapping='VENDOR',
            reimbursable_expenses_object='BILL',
            corporate_credit_card_expenses_object='CHARGE_CARD_TRANSACTION',
            import_vendors_as_merchants=True,
            sync_fyle_to_sage_intacct_payments=False,
            sync_sage_intacct_to_fyle_payments=False,
            auto_map_employees='EMAIL',
            auto_create_destination_entity=True,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 6. Create general_mappings (OneToOne with workspace)
        GeneralMapping.objects.create(
            workspace=workspace,
            location_entity_name='E2E Test Location Entity',
            location_entity_id='E2E_LOC_001',
            default_location_name='E2E Default Location',
            default_location_id='DEF_LOC_001',
            default_department_name='E2E Default Department',
            default_department_id='DEF_DEPT_001',
            default_class_name='E2E Default Class',
            default_class_id='DEF_CLASS_001',
            default_project_name='E2E Default Project',
            default_project_id='DEF_PROJ_001',
            payment_account_name='E2E Payment Account',
            payment_account_id='PAY_ACC_001',
            use_intacct_employee_departments=False,
            use_intacct_employee_locations=False,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 7. Create mapping_settings
        self.fixture_factory.create_mapping_settings(workspace)

        # 8. Create destination_attributes
        self.fixture_factory.create_destination_attributes(workspace)

        # 9. Create dimension_details
        self.fixture_factory.create_dimension_details(workspace)

        # 10. Create workspace_schedules
        WorkspaceSchedule.objects.create(
            workspace=workspace,
            enabled=False,
            start_datetime=timezone.now(),
            interval_hours=24,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 11. Create expense_attributes
        self.fixture_factory.create_expense_attributes(workspace)

        logger.info("Phase 1 core data setup completed")
        return workspace

    def _setup_phase2_advanced_data(self, workspace: Workspace) -> None:
        """Set up Phase 2: Advanced test data"""
        logger.info("Setting up Phase 2: Advanced test data")

        # First create some expense attributes for mappings to reference
        expense_attrs = ExpenseAttribute.objects.filter(workspace=workspace).order_by('id')
        dest_attrs = DestinationAttribute.objects.filter(workspace=workspace).order_by('id')

        # 12. Create mappings (1 mapping minimum) - using source_id FK to ExpenseAttribute
        self.fixture_factory.create_mappings(workspace, expense_attrs, dest_attrs, count=1)

        # 13. Create employee_mappings - using source_employee FK to ExpenseAttribute
        self.fixture_factory.create_employee_mappings(workspace, expense_attrs, dest_attrs)

        # 14. Create category_mappings - using source_category FK to ExpenseAttribute
        self.fixture_factory.create_category_mappings(workspace, expense_attrs, dest_attrs)

        # 15. Create expenses
        expenses = self.fixture_factory.create_expenses(workspace, count=22)

        # 16. Create expense_groups
        expense_groups = self.fixture_factory.create_expense_groups(workspace, expenses, group_size=2)

        # 17. Create task_logs
        self.fixture_factory.create_task_logs(workspace, expense_groups)

        # 18. Create bills and bill_lineitems (related to expense_groups)
        self.fixture_factory.create_bills_and_lineitems(expense_groups)

        # 19. Create charge_card_transactions and charge_card_transaction_lineitems (related to expense_groups)
        self.fixture_factory.create_charge_card_transactions_and_lineitems(expense_groups)

        # 20. Create errors
        # self.fixture_factory.create_error_records(workspace, expense_groups[:-2])

        # 21. Update the onboarding state
        workspace = Workspace.objects.get(id=self.workspace_id)
        workspace.onboarding_state = 'COMPLETE'
        workspace.save()
        logger.info("Phase 2 advanced data setup completed")
