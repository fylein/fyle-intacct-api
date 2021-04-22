from django.db.models import Q
from datetime import datetime, timezone

from rest_framework.response import Response
from rest_framework.views import status
from rest_framework import generics

from fyle_accounting_mappings.models import DestinationAttribute
from fyle_accounting_mappings.serializers import DestinationAttributeSerializer

from sageintacctsdk.exceptions import InvalidTokenError

from fyle_intacct_api.utils import assert_valid

from apps.fyle.models import ExpenseGroup
from apps.tasks.models import TaskLog
from apps.workspaces.models import SageIntacctCredential, Workspace
from apps.workspaces.serializers import WorkspaceSerializer

from .utils import SageIntacctConnector
from .tasks import create_expense_report, schedule_expense_reports_creation, create_bill, schedule_bills_creation, \
    create_charge_card_transaction, schedule_charge_card_transaction_creation, create_ap_payment, \
    create_sage_intacct_reimbursement, check_sage_intacct_object_status, process_fyle_reimbursements
from .models import ExpenseReport, Bill, ChargeCardTransaction
from .serializers import ExpenseReportSerializer, BillSerializer, ChargeCardTransactionSerializer, \
    SageIntacctFieldSerializer


class EmployeeView(generics.ListCreateAPIView):
    """
    Employee view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return DestinationAttribute.objects.filter(
            attribute_type='EMPLOYEE', workspace_id=self.kwargs['workspace_id']).order_by('value')

    def post(self, request, *args, **kwargs):
        """
        Get employees from Sage Intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connector = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            employees = sage_intacct_connector.sync_employees()

            return Response(
                data=self.serializer_class(employees, many=True).data,
                status=status.HTTP_200_OK
            )

        except InvalidTokenError as error:
            return Response(
                data={
                    'message': error.message
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class VendorView(generics.ListCreateAPIView):
    """
    Vendor view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return DestinationAttribute.objects.filter(
            attribute_type='VENDOR', workspace_id=self.kwargs['workspace_id']).order_by('value')

    def post(self, request, *args, **kwargs):
        """
        Get vendors from Sage Intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connector = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            vendors = sage_intacct_connector.sync_vendors(workspace_id=self.kwargs['workspace_id'])

            return Response(
                data=self.serializer_class(vendors, many=True).data,
                status=status.HTTP_200_OK
            )

        except InvalidTokenError as error:
            return Response(
                data={
                    'message': error.message
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class AccountView(generics.ListCreateAPIView):
    """
    Account view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return DestinationAttribute.objects.filter(
            attribute_type='ACCOUNT', workspace_id=self.kwargs['workspace_id']).order_by('value')

    def post(self, request, *args, **kwargs):
        """
        Get accounts from Sage Intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connector = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            accounts = sage_intacct_connector.sync_accounts(kwargs['workspace_id'])

            return Response(
                data=self.serializer_class(accounts, many=True).data,
                status=status.HTTP_200_OK
            )

        except InvalidTokenError as error:
            return Response(
                data={
                    'message': error.message
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class DepartmentView(generics.ListCreateAPIView):
    """
    Department view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return DestinationAttribute.objects.filter(
            attribute_type='DEPARTMENT', workspace_id=self.kwargs['workspace_id']).order_by('value')

    def post(self, request, *args, **kwargs):
        """
        Get departments from Sage Intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connector = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            departments = sage_intacct_connector.sync_departments()

            return Response(
                data=self.serializer_class(departments, many=True).data,
                status=status.HTTP_200_OK
            )

        except InvalidTokenError as error:
            return Response(
                data={
                    'message': error.message
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ExpenseTypeView(generics.ListCreateAPIView):
    """
    Expense Type view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return DestinationAttribute.objects.filter(
            attribute_type='EXPENSE_TYPE', workspace_id=self.kwargs['workspace_id']).order_by('value')

    def post(self, request, *args, **kwargs):
        """
        Get expense type from Sage Intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connector = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            expense_types = sage_intacct_connector.sync_expense_types()

            return Response(
                data=self.serializer_class(expense_types, many=True).data,
                status=status.HTTP_200_OK
            )

        except InvalidTokenError as error:
            return Response(
                data={
                    'message': error.message
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ChargeCardAccountView(generics.ListCreateAPIView):
    """
    Charge Card Account view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return DestinationAttribute.objects.filter(
            attribute_type='CHARGE_CARD_NUMBER', workspace_id=self.kwargs['workspace_id']).order_by('value')

    def post(self, request, *args, **kwargs):
        """
        Get Charge Card Account from Sage Intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connector = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            charge_card_account = sage_intacct_connector.sync_charge_card_accounts()

            return Response(
                data=self.serializer_class(charge_card_account, many=True).data,
                status=status.HTTP_200_OK
            )

        except InvalidTokenError as error:
            return Response(
                data={
                    'message': error.message
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentAccountView(generics.ListCreateAPIView):
    """
    Payment Account view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return DestinationAttribute.objects.filter(
            attribute_type='PAYMENT_ACCOUNT', workspace_id=self.kwargs['workspace_id']).order_by('value')

    def post(self, request, *args, **kwargs):
        """
        Get Payment Accounts from Sage Intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connector = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            payment_accounts = sage_intacct_connector.sync_payment_accounts()

            return Response(
                data=self.serializer_class(payment_accounts, many=True).data,
                status=status.HTTP_200_OK
            )

        except InvalidTokenError as error:
            return Response(
                data={
                    'message': error.message
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ItemView(generics.ListCreateAPIView):
    """
    Item view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return DestinationAttribute.objects.filter(
            attribute_type='ITEM', workspace_id=self.kwargs['workspace_id']).order_by('value')

    def post(self, request, *args, **kwargs):
        """
        Get items from Sage Intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connector = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            items = sage_intacct_connector.sync_items()

            return Response(
                data=self.serializer_class(items, many=True).data,
                status=status.HTTP_200_OK
            )

        except InvalidTokenError as error:
            return Response(
                data={
                    'message': error.message
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ProjectView(generics.ListCreateAPIView):
    """
    Project view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return DestinationAttribute.objects.filter(
            attribute_type='PROJECT', workspace_id=self.kwargs['workspace_id']).order_by('value')

    def post(self, request, *args, **kwargs):
        """
        Get projects from Sage Intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connector = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            projects = sage_intacct_connector.sync_projects()

            return Response(
                data=self.serializer_class(projects, many=True).data,
                status=status.HTTP_200_OK
            )

        except InvalidTokenError as error:
            return Response(
                data={
                    'message': error.message
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class LocationView(generics.ListCreateAPIView):
    """
    Location view
    """
    serializer_class = DestinationAttributeSerializer
    pagination_class = None

    def get_queryset(self):
        return DestinationAttribute.objects.filter(
            attribute_type='LOCATION', workspace_id=self.kwargs['workspace_id']).order_by('value')

    def post(self, request, *args, **kwargs):
        """
        Get locations from Sage Intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connector = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            locations = sage_intacct_connector.sync_locations()

            return Response(
                data=self.serializer_class(locations, many=True).data,
                status=status.HTTP_200_OK
            )

        except InvalidTokenError as error:
            return Response(
                data={
                    'message': error.message
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ExpenseReportView(generics.ListCreateAPIView):
    """
    Create Expense Report
    """
    serializer_class = ExpenseReportSerializer

    def get_queryset(self):
        return ExpenseReport.objects.filter(expense_group__workspace_id=self.kwargs['workspace_id'])\
            .order_by('-updated_at')

    def post(self, request, *args, **kwargs):
        """
        Create expense report from expense group
        """
        expense_group_id = request.data.get('expense_group_id')
        task_log_id = request.data.get('task_log_id')

        assert_valid(expense_group_id is not None, 'expense group id not found')
        assert_valid(task_log_id is not None, 'Task Log id not found')

        expense_group = ExpenseGroup.objects.get(pk=expense_group_id)
        task_log = TaskLog.objects.get(pk=task_log_id)

        create_expense_report(expense_group, task_log)

        return Response(
            data={},
            status=status.HTTP_200_OK
        )


class ExpenseReportScheduleView(generics.CreateAPIView):
    """
    Schedule expense reports create
    """

    def post(self, request, *args, **kwargs):
        expense_group_ids = request.data.get('expense_group_ids', [])

        schedule_expense_reports_creation(
            kwargs['workspace_id'], expense_group_ids)

        return Response(
            status=status.HTTP_200_OK
        )


class BillView(generics.ListCreateAPIView):
    """
    Create Bill
    """
    serializer_class = BillSerializer

    def get_queryset(self):
        return Bill.objects.filter(expense_group__workspace_id=self.kwargs['workspace_id'])\
            .order_by('-updated_at')

    def post(self, request, *args, **kwargs):
        """
        Create bill from expense group
        """
        expense_group_id = request.data.get('expense_group_id')
        task_log_id = request.data.get('task_log_id')

        assert_valid(expense_group_id is not None, 'expense group id not found')
        assert_valid(task_log_id is not None, 'Task Log id not found')

        expense_group = ExpenseGroup.objects.get(pk=expense_group_id)
        task_log = TaskLog.objects.get(pk=task_log_id)

        create_bill(expense_group, task_log)

        return Response(
            data={},
            status=status.HTTP_200_OK
        )


class BillScheduleView(generics.CreateAPIView):
    """
    Schedule bill create
    """

    def post(self, request, *args, **kwargs):
        expense_group_ids = request.data.get('expense_group_ids', [])

        schedule_bills_creation(
            kwargs['workspace_id'], expense_group_ids)

        return Response(
            status=status.HTTP_200_OK
        )


class ChargeCardTransactionsView(generics.ListCreateAPIView):
    """
    Create Charge Card Transactions
    """
    serializer_class = ChargeCardTransactionSerializer

    def get_queryset(self):
        return ChargeCardTransaction.objects.filter(expense_group__workspace_id=self.kwargs['workspace_id'])\
            .order_by('-updated_at')

    def post(self, request, *args, **kwargs):
        """
        Create Charge Card Transaction from expense group
        """
        expense_group_id = request.data.get('expense_group_id')
        task_log_id = request.data.get('task_log_id')

        assert_valid(expense_group_id is not None, 'expense group id not found')
        assert_valid(task_log_id is not None, 'Task Log id not found')

        expense_group = ExpenseGroup.objects.get(pk=expense_group_id)
        task_log = TaskLog.objects.get(pk=task_log_id)

        create_charge_card_transaction(expense_group, task_log)

        return Response(
            data={},
            status=status.HTTP_200_OK
        )


class ChargeCardTransactionsScheduleView(generics.CreateAPIView):
    """
    Schedule Charge Card Transaction create
    """

    def post(self, request, *args, **kwargs):
        expense_group_ids = request.data.get('expense_group_ids', [])

        schedule_charge_card_transaction_creation(
            kwargs['workspace_id'], expense_group_ids)

        return Response(
            status=status.HTTP_200_OK
        )


class SageIntacctFieldsView(generics.ListAPIView):
    pagination_class = None
    serializer_class = SageIntacctFieldSerializer

    def get_queryset(self):
        attributes = DestinationAttribute.objects.filter(
            ~Q(attribute_type='EMPLOYEE') & ~Q(attribute_type='VENDOR') & ~Q(attribute_type='CHARGE_CARD_NUMBER') &
            ~Q(attribute_type='EXPENSE_TYPE') & ~Q(attribute_type='ACCOUNT') & ~Q(attribute_type='CCC_ACCOUNT'),
            ~Q(attribute_type='PAYMENT_ACCOUNT'),
            workspace_id=self.kwargs['workspace_id']
        ).values('attribute_type', 'display_name').distinct()

        return attributes


class APPaymentView(generics.CreateAPIView):
    """
    Create AP Payment View
    """
    def post(self, request, *args, **kwargs):
        """
        Create AP Payment
        """
        create_ap_payment(workspace_id=self.kwargs['workspace_id'])

        return Response(
            data={},
            status=status.HTTP_200_OK
        )


class ReimbursementView(generics.ListCreateAPIView):
    """
    Create Sage Intacct Reimbursements View
    """
    def post(self, request, *args, **kwargs):
        """
        Create Sage Intacct Reimbursements View
        """
        create_sage_intacct_reimbursement(workspace_id=self.kwargs['workspace_id'])

        return Response(
            data={},
            status=status.HTTP_200_OK
        )


class FyleReimbursementsView(generics.ListCreateAPIView):
    """
    Create Fyle Reimbursements View
    """
    def post(self, request, *args, **kwargs):
        """
        Process Reimbursements in Fyle
        """
        check_sage_intacct_object_status(workspace_id=self.kwargs['workspace_id'])
        process_fyle_reimbursements(workspace_id=self.kwargs['workspace_id'])

        return Response(
            data={},
            status=status.HTTP_200_OK
        )


class SyncSageIntacctDimensionView(generics.ListCreateAPIView):
    """
    Sync Sage Intacct Dimension View
    """

    def post(self, request, *args, **kwargs):

        try:
            workspace = Workspace.objects.get(id=kwargs['workspace_id'])
            if workspace.destination_synced_at:
                time_interval = datetime.now(timezone.utc) - workspace.destination_synced_at

            if workspace.destination_synced_at is None or time_interval.days > 0:
                sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
                sage_intacct_connecter = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

                sage_intacct_connecter.sync_dimensions(kwargs['workspace_id'])

                workspace.destination_synced_at = datetime.now()
                workspace.save(update_fields=['destination_synced_at'])

            return Response(
                status=status.HTTP_200_OK
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct Credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class RefreshSageIntacctDimensionView(generics.ListCreateAPIView):
    """
    Refresh Sage Intacct Dimensions view
    """

    def post(self, request, *args, **kwargs):
        """
        Sync data from sage intacct
        """
        try:
            sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=kwargs['workspace_id'])
            sage_intacct_connecter = SageIntacctConnector(sage_intacct_credentials, workspace_id=kwargs['workspace_id'])

            sage_intacct_connecter.sync_dimensions(kwargs['workspace_id'])

            workspace = Workspace.objects.get(id=kwargs['workspace_id'])
            workspace.destination_synced_at = datetime.now()
            workspace.save(update_fields=['destination_synced_at'])

            return Response(
                status=status.HTTP_200_OK
            )

        except SageIntacctCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Sage Intacct credentials not found in workspace'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


