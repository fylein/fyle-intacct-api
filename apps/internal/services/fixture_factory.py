from django.utils import timezone
from datetime import datetime, timedelta
import uuid
import random

from apps.fyle.models import Expense, ExpenseGroup, DependentFieldSetting
from apps.sage_intacct.models import Bill, BillLineitem, ChargeCardTransaction, ChargeCardTransactionLineitem
from apps.mappings.models import GeneralMapping
from apps.tasks.models import TaskLog, Error
from fyle_accounting_library.common_resources.models import DimensionDetail
from fyle_accounting_mappings.e2e_fixtures import BaseFixtureFactory

class FixtureFactory(BaseFixtureFactory):
    """Factory for creating Intacct test fixture data"""

    def create_dependent_field_settings(self, workspace, count=2):
        """Create sample dependent field settings"""
        settings = []

        for i in range(count):
            setting = DependentFieldSetting.objects.create(
                workspace=workspace,
                cost_code_field_name='PROJECT',
                cost_code_placeholder='Select Project',
                cost_category_field_name='COST_CENTER',
                cost_category_placeholder='Select Cost Center',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            settings.append(setting)

        return settings

    def create_dimension_details(self, workspace, count=3):
        """Create sample dimension details"""
        details = []

        for i in range(count):
            detail = DimensionDetail.objects.create(
                workspace=workspace,
                dimension_name=f'E2E_DIMENSION_{i+1}',
                dimension_id=f'dim_{i+1}',
                dimension_type='LOCATION',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            details.append(detail)

        return details

    def create_expenses(self, workspace, count=10):
        """Create sample expenses"""
        expenses = []

        for i in range(count):
            expense = Expense.objects.create(
                workspace=workspace,
                expense_id=f'tx{uuid.uuid4().hex[:8]}',
                expense_number=f'E/2024/{i+1:04d}',
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
                employee_name=f'E2E Employee {i+1}',
                is_skipped=False,
                report_title=f'E2E Test Report {i+1}'
            )
            expenses.append(expense)

        return expenses

    def create_expense_groups(self, workspace, expenses, group_size=5):
        """Create expense groups from expenses"""
        groups = []

        for i in range(0, len(expenses), group_size):
            group_expenses = expenses[i:i+group_size]

            group = ExpenseGroup.objects.create(
                workspace=workspace,
                fund_source='PERSONAL',
                description={'employee_email': group_expenses[0].employee_email},
                response_logs=None,
                created_at=timezone.now(),
                updated_at=timezone.now(),
                exported_at=None
            )
            groups.append(group)

        return groups

    def create_task_logs(self, workspace, expense_groups):
        """Create task logs for expense groups"""
        task_logs = []

        for i, group in enumerate(expense_groups):
            task_log = TaskLog.objects.create(
                workspace=workspace,
                type='CREATING_BILL',
                task_id=f'task_{uuid.uuid4().hex[:8]}',
                expense_group=group,
                status='COMPLETE' if i % 3 != 0 else 'FAILED',  # Changed from SUCCESS to COMPLETE
                detail={'message': f'E2E test task log {i+1}'},
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            task_logs.append(task_log)

        return task_logs

    def create_bill_lineitems(self, workspace, expenses):
        """Create bill line items - related to expenses, not expense_group"""
        lineitems = []

        # First create some bills
        bills = self.create_bills_for_lineitems(workspace, len(expenses))

        for i, expense in enumerate(expenses):
            bill = bills[i % len(bills)]  # Distribute expenses across bills

            lineitem = BillLineitem.objects.create(
                bill=bill,  # FK to Bill
                expense=expense,  # OneToOne with Expense
                gl_account_number=f'GL-{i+1:04d}',
                project_id=f'proj_{i+1}',
                location_id=f'loc_{i+1}',
                department_id=f'dept_{i+1}',
                amount=expense.amount,
                memo=f'E2E Bill LineItem {i+1}',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            lineitems.append(lineitem)

        return lineitems

    def create_bills_for_lineitems(self, workspace, count):
        """Helper method to create bills for lineitems"""
        bills = []

        for i in range(min(count, 3)):  # Create max 3 bills
            bill = Bill.objects.create(
                workspace=workspace,
                vendor_id=f'vendor_{i+1}',
                vendor_name=f'E2E Vendor {i+1}',
                bill_number=f'BILL-{i+1:04d}',
                description=f'E2E Test Bill {i+1}',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            bills.append(bill)

        return bills

    def create_bills(self, workspace, expense_groups):
        """Create bills"""
        bills = []

        for i, group in enumerate(expense_groups):
            bill = Bill.objects.create(
                workspace=workspace,
                expense_group=group,
                vendor_id=f'vendor_{i+1}',
                vendor_name=f'E2E Vendor {i+1}',
                bill_number=f'BILL-{i+1:04d}',
                description=f'E2E Test Bill {i+1}',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            bills.append(bill)

        return bills

    def create_charge_card_transaction_lineitems(self, workspace, expenses):
        """Create charge card transaction line items - related to expenses, not expense_group"""
        lineitems = []

        # First create some charge card transactions
        transactions = self.create_charge_card_transactions_for_lineitems(workspace, len(expenses))

        for i, expense in enumerate(expenses):
            transaction = transactions[i % len(transactions)]  # Distribute expenses across transactions

            lineitem = ChargeCardTransactionLineitem.objects.create(
                charge_card_transaction=transaction,  # FK to ChargeCardTransaction
                expense=expense,  # OneToOne with Expense
                gl_account_number=f'GL-CC-{i+1:04d}',
                project_id=f'proj_{i+1}',
                location_id=f'loc_{i+1}',
                department_id=f'dept_{i+1}',
                amount=expense.amount,
                memo=f'E2E CC LineItem {i+1}',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            lineitems.append(lineitem)

        return lineitems

    def create_charge_card_transactions_for_lineitems(self, workspace, count):
        """Helper method to create charge card transactions for lineitems"""
        transactions = []

        for i in range(min(count, 3)):  # Create max 3 transactions
            transaction = ChargeCardTransaction.objects.create(
                workspace=workspace,
                charge_card_id=f'cc_{i+1}',
                vendor_id=f'vendor_{i+1}',
                description=f'E2E CC Transaction {i+1}',
                reference_no=f'CCT-{i+1:04d}',
                currency='USD',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            transactions.append(transaction)

        return transactions

    def create_charge_card_transactions(self, workspace, expense_groups):
        """Create charge card transactions"""
        transactions = []

        for i, group in enumerate(expense_groups):
            transaction = ChargeCardTransaction.objects.create(
                workspace=workspace,
                expense_group=group,
                charge_card_id=f'cc_{i+1}',
                vendor_id=f'vendor_{i+1}',
                description=f'E2E CC Transaction {i+1}',
                reference_no=f'CCT-{i+1:04d}',
                currency='USD',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            transactions.append(transaction)

        return transactions

    def create_error_records(self, workspace, count=3):
        """Create error records for testing error scenarios"""
        errors = []

        for i in range(count):
            error = Error.objects.create(
                workspace=workspace,
                type='SAGE_INTACCT_ERROR',
                error_title=f'E2E Test Error {i+1}',
                error_detail=f'E2E test error detail {i+1}',
                is_resolved=False,
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            errors.append(error)

        return errors