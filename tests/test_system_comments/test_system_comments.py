import pytest

from apps.fyle.models import ExpenseGroup
from apps.fyle.tasks import (
    delete_expense_group_and_related_data,
    handle_category_changes_for_expense,
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
    SystemCommentReasonEnum,
    SystemCommentSourceEnum
)
from apps.workspaces.system_comments import add_system_comment


def test_add_system_comment():
    """
    Test add_system_comment creates correct dict
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.GET_PROJECT_ID,
        intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=100,
        reason=SystemCommentReasonEnum.DEFAULT_PROJECT_APPLIED,
        info={'default_project_id': 'proj_123', 'default_project_name': 'Test Project'}
    )

    assert len(system_comments) == 1
    assert system_comments[0]['workspace_id'] == 1
    assert system_comments[0]['source'] == 'GET_PROJECT_ID'
    assert system_comments[0]['intent'] == 'DEFAULT_VALUE_APPLIED'
    assert system_comments[0]['entity_type'] == 'EXPENSE'
    assert system_comments[0]['entity_id'] == 100
    assert system_comments[0]['detail']['info']['default_project_id'] == 'proj_123'


def test_add_system_comment_handles_none_list():
    """
    Test add_system_comment handles None list gracefully
    """
    add_system_comment(
        system_comments=None,
        source=SystemCommentSourceEnum.GET_PROJECT_ID,
        intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=100
    )


def test_add_system_comment_expense_group_entity():
    """
    Test add_system_comment with expense group entity type
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.DELETE_EXPENSE_GROUP_AND_RELATED_DATA,
        intent=SystemCommentIntentEnum.DELETE_EXPENSE_GROUP,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE_GROUP,
        workspace_id=1,
        entity_id=50,
        reason=SystemCommentReasonEnum.EXPENSE_GROUP_AND_RELATED_DATA_DELETED
    )

    assert len(system_comments) == 1
    assert system_comments[0]['entity_type'] == 'EXPENSE_GROUP'
    assert system_comments[0]['detail']['reason'] == SystemCommentReasonEnum.EXPENSE_GROUP_AND_RELATED_DATA_DELETED.value


def test_add_system_comment_skip_expense():
    """
    Test add_system_comment for skip expense intent
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.FILTER_EXPENSE_GROUPS,
        intent=SystemCommentIntentEnum.SKIP_EXPENSE,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=100,
        reason=SystemCommentReasonEnum.NEGATIVE_EXPENSE_SKIPPED,
        info={'amount': -50.00}
    )

    assert len(system_comments) == 1
    assert system_comments[0]['intent'] == 'SKIP_EXPENSE'
    assert system_comments[0]['entity_type'] == 'EXPENSE'


def test_add_system_comment_reimbursable_not_configured():
    """
    Test add_system_comment for reimbursable not configured
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.GROUP_EXPENSES_AND_SAVE,
        intent=SystemCommentIntentEnum.SKIP_EXPENSE,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=100,
        reason=SystemCommentReasonEnum.REIMBURSABLE_EXPENSE_NOT_CONFIGURED
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == 'GROUP_EXPENSES_AND_SAVE'
    assert system_comments[0]['intent'] == 'SKIP_EXPENSE'
    assert system_comments[0]['entity_type'] == 'EXPENSE'
    assert system_comments[0]['entity_id'] == 100


def test_add_system_comment_ccc_not_configured():
    """
    Test add_system_comment for CCC not configured
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.GROUP_EXPENSES_AND_SAVE,
        intent=SystemCommentIntentEnum.SKIP_EXPENSE,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=100,
        reason=SystemCommentReasonEnum.CCC_EXPENSE_NOT_CONFIGURED
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == 'GROUP_EXPENSES_AND_SAVE'
    assert system_comments[0]['intent'] == 'SKIP_EXPENSE'
    assert system_comments[0]['entity_type'] == 'EXPENSE'
    assert system_comments[0]['entity_id'] == 100


def test_get_project_id_generates_comment(db, create_expense_group_expense):
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
    assert len(system_comments) >= 1
    comment = system_comments[0]
    assert comment['source'] == 'GET_PROJECT_ID'
    assert comment['intent'] == 'DEFAULT_VALUE_APPLIED'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.DEFAULT_PROJECT_APPLIED.value
    assert comment['detail']['info']['default_project_id'] == 'default_proj_123'
    assert comment['detail']['info']['default_project_name'] == 'Default Project'


def test_get_department_id_generates_comment(db, create_expense_group_expense):
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
    assert len(system_comments) >= 1
    comment = system_comments[0]
    assert comment['source'] == 'GET_DEPARTMENT_ID'
    assert comment['intent'] == 'DEFAULT_VALUE_APPLIED'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.DEFAULT_DEPARTMENT_APPLIED.value
    assert comment['detail']['info']['default_department_id'] == 'default_dept_123'
    assert comment['detail']['info']['default_department_name'] == 'Default Department'


def test_get_location_id_generates_comment(db, create_expense_group_expense):
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
    assert len(system_comments) >= 1
    comment = system_comments[0]
    assert comment['source'] == 'GET_LOCATION_ID'
    assert comment['intent'] == 'DEFAULT_VALUE_APPLIED'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.DEFAULT_LOCATION_APPLIED.value
    assert comment['detail']['info']['default_location_id'] == 'default_loc_123'
    assert comment['detail']['info']['default_location_name'] == 'Default Location'


def test_get_item_id_generates_comment(db, create_expense_group_expense):
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
    assert len(system_comments) >= 1
    comment = system_comments[0]
    assert comment['source'] == 'GET_ITEM_ID'
    assert comment['intent'] == 'DEFAULT_VALUE_APPLIED'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.DEFAULT_ITEM_APPLIED.value
    assert comment['detail']['info']['default_item_id'] == 'default_item_123'
    assert comment['detail']['info']['default_item_name'] == 'Default Item'


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
    _ = add_category_test_expense_group
    old_category = expense.category

    system_comments = []

    handle_category_changes_for_expense(
        expense=expense,
        new_category='New Test Category',
        system_comments=system_comments
    )

    assert len(system_comments) >= 1
    comment = system_comments[0]
    assert comment['source'] == 'HANDLE_EXPENSE_CATEGORY_CHANGE'
    assert comment['intent'] == 'UPDATE_EXPENSE_CATEGORY'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.CATEGORY_CHANGED.value.format(old=old_category, new='New Test Category')
    assert comment['detail']['info']['old_category'] == old_category
    assert comment['detail']['info']['new_category'] == 'New Test Category'


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
    comment = system_comments[0]
    assert comment['source'] == 'DELETE_EXPENSE_GROUP_AND_RELATED_DATA'
    assert comment['intent'] == 'DELETE_EXPENSE_GROUP'
    assert comment['entity_type'] == 'EXPENSE_GROUP'
    assert comment['entity_id'] == group_id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.EXPENSE_GROUP_AND_RELATED_DATA_DELETED.value
