from unittest import mock
from datetime import datetime, timezone

import pytest
from fyle.platform import Platform
from rest_framework.test import APIClient
from fyle_rest_auth.models import AuthToken, User

from fyle_intacct_api.tests import settings
from fyle_intacct_api.utils import get_access_token
from tests.test_fyle.fixtures import data as fyle_data
from apps.workspaces.models import FeatureConfig, Workspace
from apps.fyle.models import Expense, ExpenseGroup
from apps.mappings.models import GeneralMapping


@pytest.fixture
def api_client():
    """
    Returns an instance of APIClient
    """
    return APIClient()


@pytest.fixture(scope="session", autouse=True)
def default_session_fixture(request):
    """
    Default session fixture
    """
    patched_1 = mock.patch(
        'fyle_rest_auth.authentication.get_fyle_admin',
        return_value=fyle_data['get_my_profile']
    )
    patched_1.__enter__()

    patched_2 = mock.patch(
        'fyle.platform.internals.auth.Auth.update_access_token',
        return_value='asnfalsnkflanskflansfklsan'
    )
    patched_2.__enter__()

    patched_3 = mock.patch(
        'apps.fyle.helpers.post_request',
        return_value={
            'access_token': 'easnfkjo12233.asnfaosnfa.absfjoabsfjk',
            'cluster_domain': 'https://staging.fyle.tech'
        }
    )
    patched_3.__enter__()

    patched_4 = mock.patch(
        'fyle.platform.apis.v1.spender.MyProfile.get',
        return_value=fyle_data['get_my_profile']
    )
    patched_4.__enter__()

    patched_5 = mock.patch('sageintacctsdk.SageIntacctSDK.update_session_id')
    patched_5.__enter__()

    patched_6 = mock.patch(
        'tests.conftest.get_access_token',
        return_value='mock_header.mock_payload.mock_signature'
    )
    patched_6.__enter__()


@pytest.fixture()
def test_connection(db):
    """
    Creates a connection with Fyle
    """
    client_id = settings.FYLE_CLIENT_ID
    client_secret = settings.FYLE_CLIENT_SECRET
    token_url = settings.FYLE_TOKEN_URI
    refresh_token = settings.FYLE_REFRESH_TOKEN
    server_url = settings.FYLE_SERVER_URL

    fyle_connection = Platform(
        token_url=token_url,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        server_url=server_url
    )

    access_token = get_access_token(refresh_token)
    fyle_connection.access_token = access_token
    user_profile = fyle_connection.v1.spender.my_profile.get()['data']
    user = User(
        password='', last_login=datetime.now(tz=timezone.utc), id=1, email=user_profile['user']['email'],
        user_id=user_profile['user_id'], full_name='', active='t', staff='f', admin='t'
    )

    user.save()

    auth_token = AuthToken(
        id=1,
        refresh_token=refresh_token,
        user=user
    )
    auth_token.save()

    return fyle_connection


@pytest.fixture(autouse=True)
def setup_feature_config(db):
    """
    Setup FeatureConfig for workspace_id=1 that many tests use
    """
    # Ensure workspace with id=1 exists (it should from SQL fixtures)
    workspace, _ = Workspace.objects.get_or_create(
        id=1,
        defaults={
            'name': 'Fyle For Arkham Asylum',
            'fyle_org_id': 'or79Cob97KSh'
        }
    )

    # Create FeatureConfig for workspace_id=1 if it doesn't exist
    FeatureConfig.objects.get_or_create(
        workspace=workspace,
        defaults={
            'export_via_rabbitmq': False,
            'import_via_rabbitmq': False
        }
    )


@pytest.fixture(autouse=True)
def mock_rabbitmq():
    """
    Mock RabbitMQ
    """
    with mock.patch('workers.helpers.RabbitMQConnection.get_instance') as mock_rabbitmq:
        mock_instance = mock.Mock()
        mock_instance.publish.return_value = None
        mock_instance.connect.return_value = None
        mock_rabbitmq.return_value = mock_instance
        yield mock_rabbitmq


@pytest.fixture
def add_expense_report_data(db):
    """
    Create test data for expense report change tests
    """
    workspace = Workspace.objects.get(id=1)  # Use workspace_id=1 like the existing tests

    # Create test expenses
    expense1 = Expense.objects.create(
        workspace_id=workspace.id,
        expense_id='tx_report_test_1',
        employee_email='test@fyle.in',
        employee_name='Test Employee',
        category='Meals',
        sub_category='Team Meals',
        project='Test Project',
        expense_number='E/2024/01/T/1',
        claim_number='C/2024/01/R/1',
        amount=100.0,
        currency='USD',
        foreign_amount=100.0,
        foreign_currency='USD',
        settlement_id='setl_test_1',
        reimbursable=True,
        billable=False,
        state='APPROVED',
        vendor='Test Vendor',
        cost_center='Test Cost Center',
        purpose='Test meal expense',
        report_id='rp_test_report_1',
        report_title='Test Report 1',
        spent_at='2024-01-01T00:00:00Z',
        approved_at='2024-01-01T00:00:00Z',
        expense_created_at='2024-01-01T00:00:00Z',
        expense_updated_at='2024-01-01T00:00:00Z',
        created_at='2024-01-01T00:00:00Z',
        updated_at='2024-01-01T00:00:00Z',
        fund_source='PERSONAL',
        verified_at='2024-01-01T00:00:00Z',
        custom_properties={},
        org_id=workspace.fyle_org_id,
        file_ids=[],
        accounting_export_summary={}
    )

    expense2 = Expense.objects.create(
        workspace_id=workspace.id,
        expense_id='tx_report_test_2',
        employee_email='test@fyle.in',
        employee_name='Test Employee',
        category='Travel',
        sub_category='Flight',
        project='Test Project',
        expense_number='E/2024/01/T/2',
        claim_number='C/2024/01/R/1',
        amount=200.0,
        currency='USD',
        foreign_amount=200.0,
        foreign_currency='USD',
        settlement_id='setl_test_2',
        reimbursable=True,
        billable=False,
        state='APPROVED',
        vendor='Test Airline',
        cost_center='Test Cost Center',
        purpose='Test travel expense',
        report_id='rp_test_report_1',
        report_title='Test Report 1',
        spent_at='2024-01-01T00:00:00Z',
        approved_at='2024-01-01T00:00:00Z',
        expense_created_at='2024-01-01T00:00:00Z',
        expense_updated_at='2024-01-01T00:00:00Z',
        created_at='2024-01-01T00:00:00Z',
        updated_at='2024-01-01T00:00:00Z',
        fund_source='PERSONAL',
        verified_at='2024-01-01T00:00:00Z',
        custom_properties={},
        org_id=workspace.fyle_org_id,
        file_ids=[],
        accounting_export_summary={}
    )

    # Create non-exported expense group
    expense_group = ExpenseGroup.objects.create(
        workspace_id=workspace.id,
        fund_source='PERSONAL',
        exported_at=None,
        description={
            'report_id': 'rp_test_report_1',
            'employee_email': 'test@fyle.in',
            'claim_number': 'C/2024/01/R/1',
            'fund_source': 'PERSONAL'
        }
    )
    expense_group.expenses.add(expense1, expense2)

    return {
        'workspace': workspace,
        'expenses': [expense1, expense2],
        'expense_group': expense_group
    }


@pytest.fixture
def create_expense_group_expense(db):
    """
    Create expense group and expense for system comments tests
    """
    workspace = Workspace.objects.get(id=1)

    expense_group = ExpenseGroup.objects.create(
        workspace_id=1,
        fund_source='PERSONAL',
        description={}
    )

    expense, _ = Expense.objects.update_or_create(
        expense_id='tx_sys_comment_test',
        defaults={
            'employee_email': 'test@fyle.in',
            'category': 'category',
            'sub_category': 'sub_category',
            'project': 'project',
            'expense_number': 'E/2024/01/T/1',
            'org_id': workspace.fyle_org_id,
            'claim_number': 'C/2024/01/R/1',
            'amount': 100.0,
            'currency': 'USD',
            'foreign_amount': 100.0,
            'foreign_currency': 'USD',
            'settlement_id': 'setl_test',
            'reimbursable': True,
            'billable': True,
            'state': 'APPROVED',
            'vendor': 'vendor',
            'cost_center': 'cost_center',
            'purpose': 'purpose',
            'report_id': 'rp_test',
            'report_title': 'Test Report',
            'spent_at': datetime.now(tz=timezone.utc),
            'approved_at': datetime.now(tz=timezone.utc),
            'expense_created_at': datetime.now(tz=timezone.utc),
            'expense_updated_at': datetime.now(tz=timezone.utc),
            'fund_source': 'PERSONAL',
            'verified_at': datetime.now(tz=timezone.utc),
            'custom_properties': {},
            'file_ids': [],
            'workspace_id': 1
        }
    )
    expense_group.expenses.add(expense)

    GeneralMapping.objects.get_or_create(
        workspace_id=1,
        defaults={
            'default_location_name': None,
            'default_location_id': None,
        }
    )

    return expense_group, expense


@pytest.fixture
def add_category_test_expense(db):
    """
    Create expense for category change tests
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
    Create expense group for category change tests
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
