import pytest

from apps.fyle.models import ExpenseGroup
from apps.fyle.tasks import (
    delete_expense_group_and_related_data,
    handle_category_changes_for_expense,
    recreate_expense_groups,
)
from apps.mappings.models import GeneralMapping
from apps.sage_intacct.models import (
    get_department_id_or_none,
    get_item_id_or_none,
    get_location_id_or_none,
    get_project_id_or_none,
)
from apps.workspaces.enums import (
    SystemCommentEntityTypeEnum,
    SystemCommentIntentEnum,
    SystemCommentSourceEnum
)
from apps.workspaces.system_comments import SystemCommentHelper


def test_system_comment_helper_add_default_project_applied():
    """
    Test SystemCommentHelper.add_default_project_applied creates correct dict
    """
    system_comments = []

    SystemCommentHelper.add_default_project_applied(
        system_comments=system_comments,
        workspace_id=1,
        expense_id=100,
        default_project_id='proj_123',
        default_project_name='Test Project'
    )

    assert len(system_comments) == 1
    assert system_comments[0]['workspace_id'] == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.GET_PROJECT_ID
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE
    assert system_comments[0]['entity_id'] == 100
    assert system_comments[0]['detail']['info']['default_project_id'] == 'proj_123'
    assert system_comments[0]['detail']['info']['default_project_name'] == 'Test Project'


def test_system_comment_helper_handles_none_list():
    """
    Test SystemCommentHelper methods handle None list gracefully
    """
    SystemCommentHelper.add_default_project_applied(
        system_comments=None,
        workspace_id=1,
        expense_id=100,
        default_project_id='proj_123',
        default_project_name='Test Project'
    )


def test_system_comment_helper_add_category_changed():
    """
    Test SystemCommentHelper.add_category_changed creates correct dict with formatted reason
    """
    system_comments = []

    SystemCommentHelper.add_category_changed(
        system_comments=system_comments,
        workspace_id=1,
        expense_id=100,
        old_category='Old Category',
        new_category='New Category'
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.HANDLE_CATEGORY_CHANGE
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.UPDATE_EXPENSE_CATEGORY
    assert 'Old Category' in system_comments[0]['detail']['reason']
    assert 'New Category' in system_comments[0]['detail']['reason']
    assert system_comments[0]['detail']['info']['old_category'] == 'Old Category'
    assert system_comments[0]['detail']['info']['new_category'] == 'New Category'


def test_system_comment_helper_add_expense_group_deleted():
    """
    Test SystemCommentHelper.add_expense_group_deleted creates correct dict
    """
    system_comments = []

    SystemCommentHelper.add_expense_group_deleted(
        system_comments=system_comments,
        workspace_id=1,
        expense_group_id=50
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.DELETE_EXPENSE_GROUP_AND_RELATED_DATA
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.DELETE_EXPENSE_GROUP
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE_GROUP
    assert system_comments[0]['entity_id'] == 50


def test_get_project_id_generates_comment_for_default(db, create_expense_group_expense):
    """
    Test get_project_id_or_none generates system comment when default project is used
    """
    expense_group, expense = create_expense_group_expense
    general_mappings = GeneralMapping.objects.get(workspace_id=1)

    general_mappings.default_project_id = 'default_proj_123'
    general_mappings.default_project_name = 'Default Project'
    general_mappings.save()

    system_comments = []

    result = get_project_id_or_none(
        expense_group=expense_group,
        lineitem=expense,
        general_mappings=general_mappings,
        system_comments=system_comments
    )

    assert result == 'default_proj_123'
    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.GET_PROJECT_ID
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE
    assert system_comments[0]['entity_id'] == expense.id


def test_get_department_id_generates_comment_for_default(db, create_expense_group_expense):
    """
    Test get_department_id_or_none generates system comment when default department is used
    """
    expense_group, expense = create_expense_group_expense
    general_mappings = GeneralMapping.objects.get(workspace_id=1)

    general_mappings.default_department_id = 'default_dept_123'
    general_mappings.default_department_name = 'Default Department'
    general_mappings.save()

    system_comments = []

    result = get_department_id_or_none(
        expense_group=expense_group,
        lineitem=expense,
        general_mappings=general_mappings,
        system_comments=system_comments
    )

    assert result == 'default_dept_123'
    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.GET_DEPARTMENT_ID
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED


def test_get_location_id_generates_comment_for_default(db, create_expense_group_expense):
    """
    Test get_location_id_or_none generates system comment when default location is used
    """
    expense_group, expense = create_expense_group_expense
    general_mappings = GeneralMapping.objects.get(workspace_id=1)

    general_mappings.default_location_id = 'default_loc_123'
    general_mappings.default_location_name = 'Default Location'
    general_mappings.save()

    system_comments = []

    result = get_location_id_or_none(
        expense_group=expense_group,
        lineitem=expense,
        general_mappings=general_mappings,
        system_comments=system_comments
    )

    assert result == 'default_loc_123'
    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.GET_LOCATION_ID
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED


def test_get_item_id_generates_comment_for_default(db, create_expense_group_expense):
    """
    Test get_item_id_or_none generates system comment when default item is used
    """
    expense_group, expense = create_expense_group_expense
    general_mappings = GeneralMapping.objects.get(workspace_id=1)

    general_mappings.default_item_id = 'default_item_123'
    general_mappings.default_item_name = 'Default Item'
    general_mappings.save()

    system_comments = []

    result = get_item_id_or_none(
        expense_group=expense_group,
        lineitem=expense,
        general_mappings=general_mappings,
        system_comments=system_comments
    )

    assert result == 'default_item_123'
    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.GET_ITEM_ID
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED


def test_no_comment_when_system_comments_is_none(db, create_expense_group_expense):
    """
    Test no error when system_comments parameter is None
    """
    expense_group, expense = create_expense_group_expense
    general_mappings = GeneralMapping.objects.get(workspace_id=1)

    general_mappings.default_project_id = 'default_proj_123'
    general_mappings.save()

    result = get_project_id_or_none(
        expense_group=expense_group,
        lineitem=expense,
        general_mappings=general_mappings,
        system_comments=None
    )

    assert result == 'default_proj_123'


def test_category_change_generates_comment(db, add_category_test_expense, add_category_test_expense_group):
    """
    Test handle_category_changes_for_expense generates system comment
    """
    expense = add_category_test_expense
    old_category = expense.category
    new_category = 'New Category'

    system_comments = []

    handle_category_changes_for_expense(
        expense=expense,
        new_category=new_category,
        system_comments=system_comments
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.HANDLE_CATEGORY_CHANGE
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.UPDATE_EXPENSE_CATEGORY
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE
    assert system_comments[0]['entity_id'] == expense.id
    assert old_category in system_comments[0]['detail']['reason']
    assert new_category in system_comments[0]['detail']['reason']


def test_delete_expense_group_generates_comment(db, mocker):
    """
    Test delete_expense_group_and_related_data generates system comment
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()

    if not expense_group:
        pytest.skip("No expense group available for test")

    group_id = expense_group.id

    mocker.patch('apps.fyle.tasks.recreate_expense_groups', return_value=None)

    system_comments = []

    delete_expense_group_and_related_data(
        expense_group=expense_group,
        workspace_id=1,
        system_comments=system_comments
    )

    assert len(system_comments) >= 1

    delete_comments = [
        c for c in system_comments
        if c.get('source') == SystemCommentSourceEnum.DELETE_EXPENSE_GROUP_AND_RELATED_DATA
    ]

    assert len(delete_comments) == 1
    assert delete_comments[0]['intent'] == SystemCommentIntentEnum.DELETE_EXPENSE_GROUP
    assert delete_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE_GROUP
    assert delete_comments[0]['entity_id'] == group_id


def test_recreate_expense_groups_generates_comment(db, mocker, create_expense_group_expense):
    """
    Test recreate_expense_groups generates system comment
    """
    _, expense = create_expense_group_expense
    expense_ids = [expense.id]

    mocker.patch(
        'apps.fyle.models.ExpenseGroup.create_expense_groups_by_report_id_fund_source',
        return_value=[]
    )

    mocker.patch(
        'apps.fyle.tasks.skip_expenses_and_post_accounting_export_summary',
        return_value=None
    )

    system_comments = []

    recreate_expense_groups(
        workspace_id=1,
        expense_ids=expense_ids,
        system_comments=system_comments
    )

    assert len(system_comments) >= 1

    recreate_comments = [
        c for c in system_comments
        if c.get('source') == SystemCommentSourceEnum.RECREATE_EXPENSE_GROUPS
    ]

    assert len(recreate_comments) == 1
    assert recreate_comments[0]['intent'] == SystemCommentIntentEnum.RECREATE_EXPENSE_GROUPS


def test_system_comment_helper_add_negative_expense_skipped():
    """
    Test SystemCommentHelper.add_negative_expense_skipped creates correct dict
    """
    system_comments = []

    SystemCommentHelper.add_negative_expense_skipped(
        system_comments=system_comments,
        workspace_id=1,
        expense_id=100,
        amount=-50.0,
        is_grouped_by_expense=True
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.FILTER_EXPENSE_GROUPS
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.SKIP_EXPENSE
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE
    assert system_comments[0]['entity_id'] == 100
    assert system_comments[0]['detail']['info']['amount'] == -50.0
    assert system_comments[0]['detail']['info']['is_grouped_by_expense'] is True


def test_system_comment_helper_add_reimbursable_expense_not_configured():
    """
    Test SystemCommentHelper.add_reimbursable_expense_not_configured creates correct dict
    """
    system_comments = []

    SystemCommentHelper.add_reimbursable_expense_not_configured(
        system_comments=system_comments,
        workspace_id=1,
        expense_id=100
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.GROUP_EXPENSES_AND_SAVE
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.SKIP_EXPENSE
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE


def test_system_comment_helper_add_ccc_expense_not_configured():
    """
    Test SystemCommentHelper.add_ccc_expense_not_configured creates correct dict
    """
    system_comments = []

    SystemCommentHelper.add_ccc_expense_not_configured(
        system_comments=system_comments,
        workspace_id=1,
        expense_id=100
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.GROUP_EXPENSES_AND_SAVE
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.SKIP_EXPENSE


def test_system_comment_helper_add_expense_filter_rule_applied():
    """
    Test SystemCommentHelper.add_expense_filter_rule_applied creates correct dict
    """
    system_comments = []

    SystemCommentHelper.add_expense_filter_rule_applied(
        system_comments=system_comments,
        workspace_id=1,
        expense_id=100
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.GROUP_EXPENSES_AND_SAVE
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.SKIP_EXPENSE


def test_system_comment_helper_add_export_skipped_mapping_errors():
    """
    Test SystemCommentHelper.add_export_skipped_mapping_errors creates correct dict
    """
    system_comments = []

    SystemCommentHelper.add_export_skipped_mapping_errors(
        system_comments=system_comments,
        workspace_id=1,
        expense_group_id=50,
        error_id=123,
        error_type='EMPLOYEE_MAPPING'
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == SystemCommentSourceEnum.VALIDATE_FAILING_EXPORT
    assert system_comments[0]['intent'] == SystemCommentIntentEnum.SKIP_EXPORT
    assert system_comments[0]['entity_type'] == SystemCommentEntityTypeEnum.EXPENSE_GROUP
    assert system_comments[0]['entity_id'] == 50
    assert system_comments[0]['detail']['info']['error_id'] == 123
    assert system_comments[0]['detail']['info']['error_type'] == 'EMPLOYEE_MAPPING'
