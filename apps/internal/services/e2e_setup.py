from apps.fyle.models import ExpenseAttribute, ExpenseGroupSettings
from apps.internal.services.fixture_factory import FixtureFactory
from apps.mappings.models import GeneralMapping, LocationEntityMapping
from apps.sage_intacct.models import DestinationAttribute
from apps.users.models import User
from apps.workspaces.models import Configuration, FyleCredential, LastExportDetail, SageIntacctCredential, Workspace, WorkspaceSchedule
from fyle_rest_auth.models import AuthToken
from django.utils import timezone

import logging
import os
import uuid

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class E2ESetupService:
    """Service for setting up E2E test fixture data"""

    def __init__(self, admin_email, user_id, refresh_token, org_id, cluster_domain):
        self.admin_email = admin_email
        self.user_id = user_id
        self.refresh_token = refresh_token
        self.org_id = org_id
        self.cluster_domain = cluster_domain
        self.fixture_factory = FixtureFactory()

    def setup_organization(self):
        """Main method to set up the test organization"""
        logger.info("Starting E2E setup")

        # Phase 1: Core setup (Parent Org - Clone Setting)
        workspace, user = self._setup_phase1_core_data()

        # Phase 2: Advanced test data
        self._setup_phase2_advanced_data(workspace)

        return {
            "workspace_id": workspace.id,
            "org_name": workspace.name
        }

    def _setup_phase1_core_data(self):
        """Set up Phase 1: Core data required for clone setting (parent org)"""
        logger.info("Setting up Phase 1: Core data (Parent Org - Clone Setting)")

        # 1. Create user
        user = User.objects.create(
            user_id=self.user_id,
            email=self.admin_email,
            staff_id=f'E2E-{uuid.uuid4().hex[:8]}',
            full_name='E2E Test Admin',
            active=True,
            org_id=self.org_id,
            org_name='E2E Integration Tests'
        )

        # 2. Create auth_tokens
        AuthToken.objects.create(
            user=user,
            refresh_token=self.refresh_token
        )

        # 3. Create workspace
        workspace = Workspace.objects.create(
            name='E2E Integration Tests',
            fyle_org_id=self.org_id,
            cluster_domain=self.cluster_domain,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 4. Create workspace-user association (many-to-many)
        workspace.user.add(user)

        # 5. Create expense_group_settings
        ExpenseGroupSettings.objects.create(
            workspace=workspace,
            reimbursable_expense_group_fields=['employee_email', 'report_id', 'claim_number', 'fund_source'],
            corporate_credit_card_expense_group_fields=['employee_email', 'report_id', 'claim_number', 'fund_source'],
            expense_state='PAYMENT_PROCESSING',
            ccc_expense_state='PAID',
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 6. Create Fyle credentials
        FyleCredential.objects.create(
            workspace=workspace,
            refresh_token=self.refresh_token,
            cluster_domain=self.cluster_domain,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 7. Create last_export_details
        LastExportDetail.objects.create(
            workspace=workspace,
            last_exported_at=None,
            export_mode='MANUAL',
            total_expense_groups_count=0,
            successful_expense_groups_count=0,
            failed_expense_groups_count=0,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 8. Create Sage Intacct credentials (from env)
        SageIntacctCredential.objects.create(
            workspace=workspace,
            si_user_id=os.getenv('SI_USER_ID', 'e2e_test_user'),
            si_company_id=os.getenv('SI_COMPANY_ID', 'E2E_TEST_COMPANY'),
            si_user_password=os.getenv('SI_USER_PASSWORD', 'encrypted_password'),
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 9. Create location_entity_mappings
        LocationEntityMapping.objects.create(
            workspace=workspace,
            location_entity_name='E2E Test Location',
            country_name='United States',
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 10. Create configurations
        Configuration.objects.create(
            workspace=workspace,
            reimbursable_expenses_object='BILL',
            corporate_credit_card_expenses_object='CHARGE_CARD_TRANSACTION',
            import_categories=True,
            import_items=False,
            import_vendors_as_merchants=True,
            sync_fyle_to_sage_intacct_payments=False,
            sync_sage_intacct_to_fyle_payments=False,
            auto_map_employees='EMAIL',
            auto_create_destination_entity=True,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 11. Create general_mappings (OneToOne with workspace)
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

        # 12. Create mapping_settings
        self.fixture_factory.create_mapping_settings(workspace)

        # 13. Create dependent_field_settings
        self.fixture_factory.create_dependent_field_settings(workspace)

        # 14. Create destination_attributes
        self.fixture_factory.create_destination_attributes(workspace)

        # 15. Create dimension_details
        self.fixture_factory.create_dimension_details(workspace)

        # 16. Create workspace_schedules
        WorkspaceSchedule.objects.create(
            workspace=workspace,
            enabled=False,
            start_datetime=timezone.now(),
            interval_hours=24,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # 17. Create expense_attributes
        self.fixture_factory.create_expense_attributes(workspace)

        logger.info("Phase 1 core data setup completed")
        return workspace, user

    def _setup_phase2_advanced_data(self, workspace):
        """Set up Phase 2: Advanced test data"""
        logger.info("Setting up Phase 2: Advanced test data")

        # First create some expense attributes for mappings to reference
        expense_attrs = ExpenseAttribute.objects.filter(workspace=workspace)
        dest_attrs = DestinationAttribute.objects.filter(workspace=workspace)

        # 18. Create mappings (1 mapping minimum) - using source_id FK to ExpenseAttribute
        self.fixture_factory.create_mappings(workspace, expense_attrs, dest_attrs, count=1)

        # 19. Create employee_mappings - using source_employee FK to ExpenseAttribute
        self.fixture_factory.create_employee_mappings(workspace, expense_attrs, dest_attrs)

        # 20. Create category_mappings - using source_category FK to ExpenseAttribute
        self.fixture_factory.create_category_mappings(workspace, expense_attrs, dest_attrs)

        # 21. Create expenses
        expenses = self.fixture_factory.create_expenses(workspace, count=10)

        # 22. Create expense_groups
        expense_groups = self.fixture_factory.create_expense_groups(workspace, expenses)

        # 23. Create expense_groups_expenses (many-to-many relationship)
        for group in expense_groups:
            group_expenses = expenses[:5]  # First 5 expenses for first group
            group.expenses.set(group_expenses)

        # 24. Create task_logs
        self.fixture_factory.create_task_logs(workspace, expense_groups)

        # 25. Create bill_lineitems (related to expenses, not expense_group)
        self.fixture_factory.create_bill_lineitems(workspace, expenses)

        # 26. Create bills
        self.fixture_factory.create_bills(workspace, expense_groups)

        # 27. Create charge_card_transaction_lineitems (related to expenses, not expense_group)
        self.fixture_factory.create_charge_card_transaction_lineitems(workspace, expenses)

        # 28. Create charge_card_transactions
        self.fixture_factory.create_charge_card_transactions(workspace, expense_groups)

        # 29. Create errors
        self.fixture_factory.create_error_records(workspace)

        logger.info("Phase 2 advanced data setup completed")
