import random
import uuid
from datetime import timedelta

from django.utils import timezone
from fyle_accounting_library.common_resources.models import DimensionDetail

from apps.fyle.models import DependentFieldSetting, Expense, ExpenseGroup
from apps.sage_intacct.models import Bill, BillLineitem, ChargeCardTransaction, ChargeCardTransactionLineitem
from apps.tasks.models import Error, TaskLog
from apps.workspaces.models import Workspace
from fyle_accounting_mappings.e2e_fixtures import BaseFixtureFactory
from fyle_accounting_mappings.models import ExpenseAttribute


class FixtureFactory(BaseFixtureFactory):
    """Factory for creating Intacct test fixture data"""

    def create_dependent_field_settings(self, workspace: Workspace) -> list[DependentFieldSetting]:
        """Create sample dependent field settings"""
        # Create DependentFieldSetting instance without saving
        setting = DependentFieldSetting(
            workspace=workspace,
            is_import_enabled=True,
            project_field_id=1,
            cost_code_field_name='PROJECT',
            cost_code_field_id=1,
            cost_code_placeholder='Select Project',
            cost_type_field_name='COST_CENTER',
            cost_type_placeholder='Select Cost Center',
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        # Use bulk_create to avoid triggering pre_save signals
        settings = DependentFieldSetting.objects.bulk_create([setting])

        return settings

    def create_dimension_details(self, workspace: Workspace) -> None:
        """Create a sample dimension detail"""
        for source_type in ['FYLE', 'PROJECT']:
            DimensionDetail.objects.update_or_create(
                workspace=workspace,
                attribute_type='PROJECT',
                display_name='Custom Project',
                source_type=source_type
            )

    def create_expenses(self, workspace: Workspace, count: int = 10) -> list[Expense]:
        """Create sample expenses"""
        expenses = []

        for i in range(count):
            expense = Expense.objects.create(
                workspace=workspace,
                expense_id=f'tx{uuid.uuid4().hex[:8]}',
                expense_number=f'E/2025/01/T/{i + 1}',
                amount=round(random.uniform(10.0, 1000.0), 2),
                currency='USD',
                foreign_amount=None,
                foreign_currency=None,
                settlement_id=f'settle_{i}',
                reimbursable=True,
                billable=False,
                state='PAYMENT_PROCESSING',
                vendor='E2E Test Vendor',
                category='E2E Test Category',
                project='E2E Test Project',
                expense_created_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                expense_updated_at=timezone.now() - timedelta(days=random.randint(0, 5)),
                created_at=timezone.now(),
                updated_at=timezone.now(),
                fund_source='PERSONAL',
                verified_at=timezone.now(),
                custom_properties={},
                cost_center='E2E Cost Center',
                purpose='E2E Test Purpose',
                report_id=f'rp{uuid.uuid4().hex[:8]}',
                spent_at=timezone.now() - timedelta(days=random.randint(1, 15)),
                approved_at=timezone.now() - timedelta(days=random.randint(0, 3)),
                posted_at=timezone.now(),
                employee_email=f'employee{i}@e2etest.com',
                employee_name=f'E2E Employee {i + 1}',
                is_skipped=False,
                report_title=f'E2E Test Report {i + 1}'
            )
            expenses.append(expense)

        return expenses

    def create_expense_groups(self, workspace: Workspace, expenses: list[Expense], group_size: int = 5) -> list[ExpenseGroup]:
        """Create expense groups from expenses"""
        groups = []

        for i in range(0, len(expenses), group_size):
            group_expenses = expenses[i: i + group_size]

            group = ExpenseGroup.objects.create(
                workspace=workspace,
                fund_source=group_expenses[0].fund_source,
                description={
                    "expense_id": group_expenses[0].expense_id,
                    "fund_source": group_expenses[0].fund_source,
                    "employee_email": group_expenses[0].employee_email,
                    "expense_number": group_expenses[0].expense_number
                },
                export_type="JOURNAL_ENTRY",
                response_logs=None,
                created_at=timezone.now(),
                updated_at=timezone.now(),
                exported_at=timezone.now()
            )
            group.expenses.set(group_expenses)
            groups.append(group)

        return groups

    def create_task_logs(self, workspace: Workspace, expense_groups: list[ExpenseGroup]) -> None:
        """Create task logs for expense groups"""
        for i, group in enumerate(expense_groups):
            TaskLog.objects.create(
                workspace=workspace,
                type='CREATING_BILL',
                task_id=f'task_{uuid.uuid4().hex[:8]}',
                expense_group=group,
                status='COMPLETE',
                detail={'message': f'E2E test task log {i + 1}'},
                created_at=timezone.now(),
                updated_at=timezone.now()
            )

    def create_bills_and_lineitems(self, expense_groups: list[ExpenseGroup]) -> None:
        """Create bills and bill line items for expense groups"""
        for expense_group in expense_groups:
            # First create a bill for this expense group
            bill = Bill.objects.create(
                expense_group=expense_group,
                vendor_id=f'vendor_{expense_group.id}',
                description=f'E2E Test Bill for Group {expense_group.id}',
                currency='USD',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )

            # Get expenses from the expense group and create lineitems for each
            expenses = expense_group.expenses.all()
            for expense in expenses:
                BillLineitem.objects.create(
                    bill=bill,
                    expense=expense,
                    gl_account_number=f'GL-{expense.id:04d}',
                    project_id=f'proj_{expense.id}',
                    location_id=f'loc_{expense.id}',
                    department_id=f'dept_{expense.id}',
                    amount=expense.amount,
                    memo=f'E2E Bill LineItem for Expense {expense.id}',
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )

    def create_charge_card_transactions_and_lineitems(self, expense_groups: list[ExpenseGroup]) -> None:
        """Create charge card transactions and line items for expense groups"""
        for expense_group in expense_groups:
            # First create a charge card transaction for this expense group
            transaction = ChargeCardTransaction.objects.create(
                expense_group=expense_group,
                charge_card_id=f'cc_{expense_group.id}',
                vendor_id=f'vendor_{expense_group.id}',
                description=f'E2E CC Transaction for Group {expense_group.id}',
                reference_no=f'CCT-{expense_group.id:04d}',
                currency='USD',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )

            # Get expenses from the expense group and create lineitems for each
            expenses = expense_group.expenses.all()
            for expense in expenses:
                ChargeCardTransactionLineitem.objects.create(
                    charge_card_transaction=transaction,
                    expense=expense,
                    gl_account_number=f'GL-CC-{expense.id:04d}',
                    project_id=f'proj_{expense.id}',
                    location_id=f'loc_{expense.id}',
                    department_id=f'dept_{expense.id}',
                    amount=expense.amount,
                    memo=f'E2E CC LineItem for Expense {expense.id}',
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )

    def create_error_records(self, workspace: Workspace, expense_groups: list[ExpenseGroup]) -> None:
        """Create error records for testing error scenarios"""
        employees = ExpenseAttribute.objects.filter(attribute_type='EMPLOYEE')
        for i, expense_group in enumerate(expense_groups):
            Error.objects.create(
                workspace=workspace,
                type='EMPLOYEE_MAPPING',
                repetition_count=1,
                expense_group=expense_group,
                expense_attribute=employees[i],
                error_title=f'E2E Test Error for expense group {expense_group.id}',
                error_detail=f'E2E test error detail for expense group {expense_group.id}',
                is_resolved=False,
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
