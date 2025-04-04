from apps.tasks.models import TaskLog
import pytest

from unittest import mock
from asyncio.log import logger

from django.db.models import Q
from django.conf import settings
from rest_framework.views import status
from rest_framework.response import Response

from fyle_accounting_library.common_resources.models import DimensionDetail
from fyle_accounting_library.common_resources.enums import DimensionDetailSourceTypeEnum

from apps.workspaces.models import Configuration, Workspace
from apps.fyle.models import Expense, ExpenseFilter
from apps.fyle.actions import __bulk_update_expenses
from apps.fyle.helpers import (
    get_source_account_type,
    get_updated_accounting_export_summary,
    handle_import_exception,
    post_request,
    get_request,
    get_fyle_orgs,
    get_fund_source,
    construct_expense_filter,
    update_dimension_details,
    handle_refresh_dimensions,
    construct_expense_filter_query,
    check_interval_and_sync_dimension,
)


def test_post_request(mocker):
    """
    Test post request
    """
    mocker.patch(
        'apps.fyle.helpers.requests.post',
        return_value=mock.MagicMock(status_code=200, text="{'key': 'dfghjk'}")
    )
    try:
        response = post_request(url='sdfghjk', body={}, refresh_token='srtyu')
        assert response == {'key': 'dfghjk'}
    except Exception:
        logger.info('Error in post request')

    mocker.patch(
        'apps.fyle.helpers.requests.post',
        return_value=Response(
            {
                'message': 'Post request'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    )
    try:
        post_request(url='sdfghjk', body={}, refresh_token='srtyu')
    except Exception:
        logger.info('Error in post request')


def test_get_request(mocker):
    """
    Test get request
    """
    mocker.patch(
        'apps.fyle.helpers.requests.get',
        return_value=mock.MagicMock(status_code=200, text="{'key': 'dfghjk'}")
    )
    try:
        response = get_request(url='sdfghjk', params={'key': 'dfghjk'}, refresh_token='srtyu')
        assert response == {'key': 'dfghjk'}
    except Exception:
        logger.info('Error in post request')

    mocker.patch(
        'apps.fyle.helpers.requests.get',
        return_value=Response(
            {
                'message': 'Get request'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    )
    try:
        get_request(url='sdfghjk', params={'sample': True}, refresh_token='srtyu')
    except Exception:
        logger.info('Error in post request')


def test_get_fyle_orgs(mocker):
    """
    Test get Fyle orgs
    """
    mocker.patch(
        'apps.fyle.helpers.requests.get',
        return_value=mock.MagicMock(status_code=200, text="{'orgs': 'dfghjk'}")
    )
    try:
        response = get_fyle_orgs(refresh_token='srtyu', cluster_domain='erty')
        assert response == {'orgs': 'dfghjk'}
    except Exception:
        logger.info('Error in post request')


@pytest.mark.django_db()
def test_construct_expense_filter():
    """
    Test construct expense filter
    """
    # employee-email-is-equal
    expense_filter = ExpenseFilter(
        condition = 'employee_email',
        operator = 'in',
        values = ['killua.z@fyle.in', 'naruto.u@fyle.in'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'employee_email__in':['killua.z@fyle.in', 'naruto.u@fyle.in']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # employee-email-is-equal-one-email-only
    expense_filter = ExpenseFilter(
        condition = 'employee_email',
        operator = 'in',
        values = ['killua.z@fyle.in'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'employee_email__in':['killua.z@fyle.in']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # claim-number-is-equal
    expense_filter = ExpenseFilter(
        condition = 'claim_number',
        operator = 'in',
        values = ['ajdnwjnadw', 'ajdnwjnlol'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'claim_number__in':['ajdnwjnadw', 'ajdnwjnlol']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # claim-number-is-equal-one-claim_number-only
    expense_filter = ExpenseFilter(
        condition = 'claim_number',
        operator = 'in',
        values = ['ajdnwjnadw'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'claim_number__in':['ajdnwjnadw']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # report-name-is-equal
    expense_filter = ExpenseFilter(
        condition = 'report_title',
        operator = 'iexact',
        values = ['#17:  Dec 2022'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'report_title__iexact':'#17:  Dec 2022'}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # report-name-contains
    expense_filter = ExpenseFilter(
        condition = 'report_title',
        operator = 'icontains',
        values = ['Dec 2022'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'report_title__icontains':'Dec 2022'}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # spent-at-is-before
    expense_filter = ExpenseFilter(
        condition = 'spent_at',
        operator = 'lt',
        values = ['2020-04-20 23:59:59+00'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'spent_at__lt':'2020-04-20 23:59:59+00'}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # spent-at-is-on-or-before
    expense_filter = ExpenseFilter(
        condition = 'spent_at',
        operator = 'lte',
        values = ['2020-04-20 23:59:59+00'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'spent_at__lte':'2020-04-20 23:59:59+00'}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # category_in
    expense_filter = ExpenseFilter(
        condition = 'category',
        operator = 'in',
        values = ['anish'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'category__in':['anish']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # category_not_in
    expense_filter = ExpenseFilter(
        condition = 'category',
        operator = 'not_in',
        values = ['anish', 'singh'],
        rank = 1
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'category__in':['anish', 'singh']}
    response = ~Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-number-is-equal
    expense_filter = ExpenseFilter(
        condition = 'Gon Number',
        operator = 'in',
        values = [102,108],
        rank = 1,
        is_custom = True
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Gon Number__in':[102, 108]}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-number-is-not-empty
    expense_filter = ExpenseFilter(
        condition = 'Gon Number',
        operator = 'isnull',
        values = ['False'],
        rank = 1,
        is_custom = True
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Gon Number__exact': None}
    response = ~Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-number-is--empty
    expense_filter = ExpenseFilter(
        condition = 'Gon Number',
        operator = 'isnull',
        values = ['True'],
        rank = 1,
        is_custom = True
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Gon Number__isnull': True}
    filter_2 = {'custom_properties__Gon Number__exact': None}
    response = Q(**filter_1) | Q(**filter_2)

    assert constructed_expense_filter == response

    # custom-properties-text-is-equal
    expense_filter = ExpenseFilter(
        condition = 'Killua Text',
        operator = 'in',
        values = ['hunter', 'naruto', 'sasuske'],
        rank = 1,
        is_custom = True
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Killua Text__in':['hunter', 'naruto', 'sasuske']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-text-is-not-empty
    expense_filter = ExpenseFilter(
        condition = 'Killua Text',
        operator = 'isnull',
        values = ['False'],
        rank = 1,
        is_custom = True
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Killua Text__exact': None}
    response = ~Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-text-is--empty
    expense_filter = ExpenseFilter(
        condition = 'Killua Text',
        operator = 'isnull',
        values = ['True'],
        rank = 1,
        is_custom = True
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Killua Text__isnull': True}
    filter_2 = {'custom_properties__Killua Text__exact': None}
    response = Q(**filter_1) | Q(**filter_2)

    assert constructed_expense_filter == response

    # custom-properties-select-is-equal
    expense_filter = ExpenseFilter(
        condition = 'Kratos',
        operator = 'in',
        values = ['BOOK', 'Dev-D'],
        rank = 1,
        is_custom = True
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__in':['BOOK', 'Dev-D']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-select-is-equal-one-value
    expense_filter = ExpenseFilter(
        condition = 'Kratos',
        operator = 'in',
        values = ['BOOK'],
        rank = 1,
        is_custom = True
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__in':['BOOK']}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-select-is-not-empty
    expense_filter = ExpenseFilter(
        condition = 'Kratos',
        operator = 'isnull',
        values = ['False'],
        rank = 1,
        is_custom = True
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__exact': None}
    response = ~Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-select-is--empty
    expense_filter = ExpenseFilter(
        condition = 'Kratos',
        operator = 'isnull',
        values = ['True'],
        rank = 1,
        is_custom = True
    )
    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__isnull': True}
    filter_2 = {'custom_properties__Kratos__exact': None}
    response = Q(**filter_1) | Q(**filter_2)

    assert constructed_expense_filter == response

    # custom-properties-checkbok--yes
    expense_filter = ExpenseFilter(
        condition = 'Kratos',
        operator = 'exact',
        values = ['true'],
        rank = 1,
        is_custom = True,
        custom_field_type = 'BOOLEAN'
    )

    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__exact': True}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-number
    expense_filter = ExpenseFilter(
        condition = 'Kratos',
        operator = 'exact',
        values = ['1'],
        rank = 1,
        is_custom = True,
        custom_field_type = 'NUMBER'
    )

    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__exact': 1}
    response = Q(**filter_1)

    assert constructed_expense_filter == response

    # custom-properties-selete
    expense_filter = ExpenseFilter(
        condition = 'Kratos',
        operator = 'not_in',
        values = ['BOOK', 'Dev-D'],
        rank = 1,
        is_custom = True,
        custom_field_type = 'SELECT'
    )

    constructed_expense_filter = construct_expense_filter(expense_filter)

    filter_1 = {'custom_properties__Kratos__in': ['BOOK', 'Dev-D']}
    response = ~Q(**filter_1)

    assert constructed_expense_filter == response


@pytest.mark.django_db()
def test_multiple_construct_expense_filter():
    """
    Test multiple construct expense filter
    """
    # employee-email-is-equal and claim-number-is-equal
    expense_filters = [
        ExpenseFilter(
            condition = 'employee_email',
            operator = 'in',
            values = ['killua.z@fyle.in', 'naruto.u@fyle.in'],
            rank = 1,
            join_by = 'AND'
        ),
        ExpenseFilter(
            condition = 'claim_number',
            operator = 'in',
            values = ['ajdnwjnadw', 'ajdnwjnlol'],
            rank = 2,
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_1 = {'employee_email__in':['killua.z@fyle.in', 'naruto.u@fyle.in']}
    filter_2 = {'claim_number__in':['ajdnwjnadw', 'ajdnwjnlol']}
    response = Q(**filter_1) & Q(**filter_2)

    assert final_filter == response

    # employee-email-is-equal or claim-number-is-equal
    expense_filters = [
        ExpenseFilter(
            condition = 'employee_email',
            operator = 'in',
            values = ['killua.z@fyle.in', 'naruto.u@fyle.in'],
            rank = 1,
            join_by = 'OR'
        ),
        ExpenseFilter(
            condition = 'claim_number',
            operator = 'in',
            values = ['ajdnwjnadw', 'ajdnwjnlol'],
            rank = 2,
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_1 = {'employee_email__in':['killua.z@fyle.in', 'naruto.u@fyle.in']}
    filter_2 = {'claim_number__in':['ajdnwjnadw', 'ajdnwjnlol']}
    response = Q(**filter_1) | Q(**filter_2)

    assert final_filter == response

    # employee-email-is-equal or report-title-contains
    expense_filters = [
        ExpenseFilter(
            condition = 'employee_email',
            operator = 'in',
            values = ['killua.z@fyle.in', 'naruto.u@fyle.in'],
            rank = 1,
            join_by = 'OR'
        ),
        ExpenseFilter(
            condition = 'report_title',
            operator = 'icontains',
            values = ['Dec 2022'],
            rank = 2
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_1 = {'employee_email__in':['killua.z@fyle.in', 'naruto.u@fyle.in']}
    filter_2 = {'report_title__icontains':'Dec 2022'}
    response = Q(**filter_1) | Q(**filter_2)

    assert final_filter == response

    # custom-properties-number-is-empty and spent-at-less-than
    expense_filters = [
        ExpenseFilter(
            condition = 'Gon Number',
            operator = 'isnull',
            values = ['True'],
            rank = 1,
            is_custom = True,
            join_by = 'AND'
        ),
        ExpenseFilter(
            condition = 'spent_at',
            operator = 'lt',
            values = ['2020-04-20 23:59:59+00'],
            rank = 2
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_1 = {'custom_properties__Gon Number__isnull': True}
    filter_2 = {'custom_properties__Gon Number__exact': None}
    filter_3 = {'spent_at__lt':'2020-04-20 23:59:59+00'}
    response = (Q(**filter_1) | Q(**filter_2)) & (Q(**filter_3))

    assert final_filter == response

    # custom-properties-number-is-empty and custom-properties-select-is-not-empty
    expense_filters = [
        ExpenseFilter(
            condition = 'Gon Number',
            operator = 'isnull',
            values = ['True'],
            rank = 1,
            is_custom = True,
            join_by = 'AND'
        ),
        ExpenseFilter(
            condition = 'Kratos',
            operator = 'isnull',
            values = ['False'],
            rank = 2,
            is_custom = True
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_1 = {'custom_properties__Gon Number__isnull': True}
    filter_2 = {'custom_properties__Gon Number__exact': None}
    filter_3 = {'custom_properties__Kratos__exact': None}
    response = (Q(**filter_1) | Q(**filter_2)) & (~Q(**filter_3))

    assert final_filter == response

    # report-name-is-equal or custom-properties-number-is-equal
    expense_filters = [
        ExpenseFilter(
            condition = 'report_title',
            operator = 'iexact',
            values = ['#17:  Dec 2022'],
            rank = 1,
            join_by = 'OR'
        ),
        ExpenseFilter(
            condition = 'Gon Number',
            operator = 'in',
            values = [102,108],
            rank = 2,
            is_custom = True
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_1 = {'report_title__iexact':'#17:  Dec 2022'}
    filter_2 = {'custom_properties__Gon Number__in':[102, 108]}
    response = (Q(**filter_1)) | (Q(**filter_2))

    assert final_filter == response

    # custom-properties-number-is-equal and custom-properties-text-is-equal
    expense_filters = [
        ExpenseFilter(
            condition = 'Gon Number',
            operator = 'in',
            values = [102,108],
            rank = 1,
            is_custom = True,
            join_by='AND'
        ),
        ExpenseFilter(
            condition = 'Killua Text',
            operator = 'in',
            values = ['hunter', 'naruto', 'sasuske'],
            rank = 2,
            is_custom = True
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_1 = {'custom_properties__Gon Number__in':[102, 108]}
    filter_2 = {'custom_properties__Killua Text__in':['hunter', 'naruto', 'sasuske']}
    response = (Q(**filter_1)) & (Q(**filter_2))

    assert final_filter == response

    # custom-properties-select-is-equal and custom-properties-text-is--empty
    expense_filters = [
        ExpenseFilter(
            condition = 'Kratos',
            operator = 'in',
            values = ['BOOK', 'Dev-D'],
            rank = 1,
            is_custom = True,
            join_by = 'AND'
        ),
        ExpenseFilter(
            condition = 'Killua Text',
            operator = 'isnull',
            values = ['True'],
            rank = 2,
            is_custom = True
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_1 = {'custom_properties__Kratos__in':['BOOK', 'Dev-D']}
    filter_2 = {'custom_properties__Killua Text__isnull': True}
    filter_3 = {'custom_properties__Killua Text__exact': None}
    response = (Q(**filter_1)) & (Q(**filter_2) | Q(**filter_3))

    assert final_filter == response

    # custom-properties-select-is-equal
    expense_filters = [
        ExpenseFilter(
            condition = 'Kratos',
            operator = 'in',
            values = ['BOOK', 'Dev-D'],
            rank = 1,
            is_custom = True,
            join_by = 'AND'
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_1 = {'custom_properties__Kratos__in':['BOOK', 'Dev-D']}
    response = (Q(**filter_1))

    assert final_filter == response
    # custom-properties-text-is-null
    expense_filters = [
        ExpenseFilter(
            condition = 'Killua Text',
            operator = 'isnull',
            values = ['True'],
            rank = 1,
            is_custom = True
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_2 = {'custom_properties__Killua Text__isnull': True}
    filter_3 = {'custom_properties__Killua Text__exact': None}
    response = (Q(**filter_2) | Q(**filter_3))

    assert final_filter == response

    # custom-properties-checkbok--no with rank 2
    expense_filters = [
        ExpenseFilter(
            condition = 'Kratos',
            operator = 'in',
            values = ['BOOK', 'Dev-D'],
            rank = 1,
            is_custom = True,
            join_by = 'AND'
        ),
        ExpenseFilter(
            condition = 'Kratoss',
            operator = 'exact',
            values = ['false'],
            rank = 2,
            is_custom = True,
            custom_field_type = 'BOOLEAN'
        )
    ]

    final_filter = construct_expense_filter_query(expense_filters)

    filter_1 = {'custom_properties__Kratos__in':['BOOK', 'Dev-D']}
    filter_2 = {'custom_properties__Kratoss__exact': False}

    response = (Q(**filter_1)) & Q(**filter_2)

    assert final_filter == response


def test_bulk_update_expenses(db):
    """
    Test bulk update expenses
    """
    expenses = Expense.objects.filter(org_id='or79Cob97KSh')
    for expense in expenses:
        expense.accounting_export_summary = get_updated_accounting_export_summary(
            expense.expense_id,
            'SKIPPED',
            None,
            '{}/main/export_log'.format(settings.INTACCT_INTEGRATION_APP_URL),
            True
        )
        expense.save()

    __bulk_update_expenses(expenses)

    expenses = Expense.objects.filter(org_id='or79Cob97KSh')

    for expense in expenses:
        assert expense.accounting_export_summary['synced'] == True
        assert expense.accounting_export_summary['state'] == 'SKIPPED'
        assert expense.accounting_export_summary['error_type'] == None
        assert expense.accounting_export_summary['url'] == '{}/main/export_log'.format(
            settings.INTACCT_INTEGRATION_APP_URL
        )
        assert expense.accounting_export_summary['id'] == expense.expense_id


def test_handle_refresh_dimensions(db, mocker):
    """
    Test handle refresh dimensions
    """
    mocker.patch(
        'apps.fyle.helpers.sync_dimensions',
        return_value=None
    )

    res = handle_refresh_dimensions(workspace_id=1)
    assert res == None

    workspace = Workspace.objects.get(id=1)
    assert workspace.source_synced_at != None

    configuration = Configuration.objects.get(workspace_id=1)
    configuration.import_categories = True
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    res = handle_refresh_dimensions(workspace_id=1)
    assert res == None

    workspace = Workspace.objects.get(id=1)
    assert workspace.source_synced_at != None


def test_check_interval_and_sync_dimension(db, mocker):
    """
    Test check interval and sync dimension
    """
    mocker.patch(
        'apps.fyle.helpers.sync_dimensions',
        return_value=None
    )

    res = check_interval_and_sync_dimension(workspace_id=1)
    assert res == None

    workspace = Workspace.objects.get(id=1)
    assert workspace.source_synced_at != None


def test_get_fund_source(db):
    """
    Test get fund source
    """
    workspace_id = 1
    Configuration.objects.filter(workspace_id=workspace_id).update(
        reimbursable_expenses_object='BILL',
        corporate_credit_card_expenses_object='JOURNAL_ENTRY'
    )
    fund_source = get_fund_source(workspace_id)

    assert fund_source == ['PERSONAL', 'CCC']


def test_update_dimension_details(db, mocker):
    """
    Test update dimension details
    """
    platform = mocker.patch('apps.fyle.helpers.PlatformConnector', return_value=mocker.MagicMock())

    def mock_list_all(params=None):
        if params:
            return []
        return [{
            'column_name': 'project_id',
            'field_name': 'Project 123',
            'type': 'SELECT'
        },{
            'column_name': 'cost_center_id',
            'field_name': 'Cost Center 123',
            'type': 'SELECT'
        },{
            'column_name': 'something',
            'field_name': 'Test 123',
            'type': 'SELECT'
        }]

    platform.expense_custom_fields.list_all.side_effect = mock_list_all

    workspace_id = 1
    update_dimension_details(platform=platform, workspace_id=workspace_id)

    dimension_detail = DimensionDetail.objects.filter(workspace_id=workspace_id, source_type=DimensionDetailSourceTypeEnum.FYLE.value)

    assert dimension_detail.filter(attribute_type='PROJECT').exists() is True
    assert dimension_detail.filter(attribute_type='COST_CENTER').exists() is True

    assert dimension_detail.filter(attribute_type='PROJECT').first().display_name == 'Project 123'
    assert dimension_detail.filter(attribute_type='COST_CENTER').first().display_name == 'Cost Center 123'

    assert dimension_detail.filter(attribute_type='TEST_123').first().display_name == 'Test 123'


def test_get_source_account_type():
    """
    Test get source account type
    """
    fund_sources = ['PERSONAL', 'CCC']
    source_account_type = get_source_account_type(fund_sources)
    assert source_account_type == ['PERSONAL_CASH_ACCOUNT', 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT']


def test_handle_import_exception(db):
    """
    Test handle import exception
    """
    workspace_id = 1
    task_log = TaskLog.objects.filter(workspace_id=workspace_id).first()

    handle_import_exception(task_log=task_log)
    assert task_log.status == 'FATAL'
