from datetime import datetime, timedelta, timezone

from apps.fyle.models import ExpenseGroup
from apps.fyle.tasks import (
    delete_expense_group_and_related_data,
    handle_category_changes_for_expense,
)
from apps.internal.tasks import retrigger_stuck_exports
from apps.mappings.models import GeneralMapping
from apps.sage_intacct.models import (
    Bill,
    BillLineitem,
    ChargeCardTransaction,
    ChargeCardTransactionLineitem,
    Configuration,
    ExpenseReport,
    ExpenseReportLineitem,
    JournalEntry,
    JournalEntryLineitem,
    get_class_id_or_none,
    get_ccc_account_id,
    get_department_id_or_none,
    get_item_id_or_none,
    get_location_id_or_none,
    get_project_id_or_none,
)
from apps.sage_intacct.tasks import (
    create_bill,
    create_charge_card_transaction,
    create_expense_report,
)
from sageintacctsdk.exceptions import NoPrivilegeError, WrongParamsError
from intacctsdk.exceptions import (
    BadRequestError as IntacctRESTBadRequestError,
    InternalServerError as IntacctRESTInternalServerError
)
from fyle_intacct_api.exceptions import BulkError
from fyle_accounting_library.system_comments.models import SystemComment
from fyle_accounting_mappings.models import Mapping, EmployeeMapping, DestinationAttribute, ExpenseAttribute
from apps.workspaces.enums import (
    ExportTypeEnum,
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
    assert expense_group is not None, "No expense group available for test"

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


def test_add_system_comment_with_export_type():
    """
    Test add_system_comment with export_type parameter
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.CREATE_BILL,
        intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=100,
        export_type=ExportTypeEnum.BILL,
        reason=SystemCommentReasonEnum.DEFAULT_CLASS_APPLIED
    )

    assert len(system_comments) == 1
    assert system_comments[0]['export_type'] == 'BILL'


def test_add_system_comment_with_export_type_string():
    """
    Test add_system_comment with export_type as string
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.CREATE_BILL,
        intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=100,
        export_type='EXPENSE_REPORT',
        reason=SystemCommentReasonEnum.DEFAULT_CLASS_APPLIED
    )

    assert len(system_comments) == 1
    assert system_comments[0]['export_type'] == 'EXPENSE_REPORT'


def test_add_system_comment_with_is_user_visible():
    """
    Test add_system_comment with is_user_visible=True
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.HANDLE_REPORT_CHANGE,
        intent=SystemCommentIntentEnum.UPDATE_EXPENSE_REPORT,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=100,
        is_user_visible=True,
        reason=SystemCommentReasonEnum.EXPENSE_ADDED_TO_REPORT
    )

    assert len(system_comments) == 1
    assert system_comments[0]['is_user_visible'] is True


def test_add_system_comment_with_string_values():
    """
    Test add_system_comment with string values instead of enums
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source='CUSTOM_SOURCE',
        intent='CUSTOM_INTENT',
        entity_type='EXPENSE',
        workspace_id=1,
        entity_id=100,
        reason='Custom reason string',
        info={'custom_key': 'custom_value'}
    )

    assert len(system_comments) == 1
    assert system_comments[0]['source'] == 'CUSTOM_SOURCE'
    assert system_comments[0]['intent'] == 'CUSTOM_INTENT'
    assert system_comments[0]['entity_type'] == 'EXPENSE'
    assert system_comments[0]['detail']['reason'] == 'Custom reason string'
    assert system_comments[0]['detail']['info']['custom_key'] == 'custom_value'


def test_add_system_comment_with_none_entity_id():
    """
    Test add_system_comment with None entity_id
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.DELETE_EXPENSES,
        intent=SystemCommentIntentEnum.DELETE_EXPENSES,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=None,
        reason=SystemCommentReasonEnum.EXPENSES_DELETED_NO_EXPORT_SETTING
    )

    assert len(system_comments) == 1
    assert system_comments[0]['entity_id'] is None


def test_add_system_comment_with_none_reason():
    """
    Test add_system_comment with None reason
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.GET_PROJECT_ID,
        intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=100,
        reason=None
    )

    assert len(system_comments) == 1
    assert system_comments[0]['detail']['reason'] is None


def test_add_system_comment_with_none_info():
    """
    Test add_system_comment with None info (should use empty dict)
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
        info=None
    )

    assert len(system_comments) == 1
    assert system_comments[0]['detail']['info'] == {}


def test_add_system_comment_with_none_export_type():
    """
    Test add_system_comment with None export_type
    """
    system_comments = []

    add_system_comment(
        system_comments=system_comments,
        source=SystemCommentSourceEnum.GET_PROJECT_ID,
        intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
        entity_type=SystemCommentEntityTypeEnum.EXPENSE,
        workspace_id=1,
        entity_id=100,
        export_type=None,
        reason=SystemCommentReasonEnum.DEFAULT_PROJECT_APPLIED
    )

    assert len(system_comments) == 1
    assert system_comments[0]['export_type'] is None


def test_get_class_id_generates_comment(db, create_expense_group_expense):
    """
    Test get_class_id_or_none generates system comment when default class is used
    """
    expense_group, expense = create_expense_group_expense
    general_mappings = GeneralMapping.objects.get(workspace_id=1)

    general_mappings.default_class_id = 'default_class_123'
    general_mappings.default_class_name = 'Default Class'
    general_mappings.save()

    system_comments = []

    result = get_class_id_or_none(
        expense_group=expense_group,
        lineitem=expense,
        general_mappings=general_mappings,
        system_comments=system_comments
    )

    assert result == 'default_class_123'
    assert len(system_comments) >= 1
    comment = system_comments[0]
    assert comment['source'] == 'GET_CLASS_ID'
    assert comment['intent'] == 'DEFAULT_VALUE_APPLIED'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.DEFAULT_CLASS_APPLIED.value
    assert comment['detail']['info']['default_class_id'] == 'default_class_123'
    assert comment['detail']['info']['default_class_name'] == 'Default Class'


def test_get_ccc_account_id_generates_comment(db, create_expense_group_expense, mocker):
    """
    Test get_ccc_account_id generates system comment when employee CCC account is used
    """
    expense_group, expense = create_expense_group_expense
    general_mappings = GeneralMapping.objects.get(workspace_id=1)

    employee_email = expense_group.description.get('employee_email', 'test@example.com')
    expense_group.description['employee_email'] = employee_email
    expense_group.save()

    general_mappings.default_charge_card_id = None
    general_mappings.save()

    expense_attribute = ExpenseAttribute.objects.first()
    expense_attribute.value = employee_email
    expense_attribute.save()

    destination_attr = DestinationAttribute.objects.first()
    destination_attr.destination_id = 'ccc_account_123'
    destination_attr.display_name = 'Employee CCC Account'
    destination_attr.attribute_type = 'CHARGE_CARD_NUMBER'
    destination_attr.save()

    employee_mapping = EmployeeMapping.objects.first()
    employee_mapping.source_employee = expense_attribute
    employee_mapping.destination_card_account = destination_attr
    employee_mapping.workspace_id = general_mappings.workspace
    employee_mapping.save()

    expense.corporate_card_id = 999
    expense.save()

    Mapping.objects.filter(
        source_type='CORPORATE_CARD',
        destination_type='CHARGE_CARD_NUMBER',
        source__source_id=999,
        workspace_id=general_mappings.workspace
    ).delete()

    system_comments = []

    result = get_ccc_account_id(
        general_mappings=general_mappings,
        expense=expense,
        description=expense_group.description,
        system_comments=system_comments
    )

    assert result == 'ccc_account_123'
    assert len(system_comments) >= 1
    comment = system_comments[0]
    assert comment['source'] == 'GET_CCC_ACCOUNT_ID'
    assert comment['intent'] == 'EMPLOYEE_DEFAULT_VALUE_APPLIED'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.EMPLOYEE_CCC_ACCOUNT_APPLIED.value
    assert comment['detail']['info']['employee_ccc_account_id'] == 'ccc_account_123'
    assert comment['detail']['info']['employee_ccc_account_name'] == 'Employee CCC Account'


def test_billable_disabled_expense_report_lineitem(db, create_expense_group_expense, mocker):
    """
    Test create_expense_report_lineitems generates system comment when billable is set to False due to missing customer_id or item_id
    """
    expense_group, expense = create_expense_group_expense

    expense.billable = True
    expense.save()

    employee_email = 'test@fyle.in'
    expense_group.description['employee_email'] = employee_email
    expense_group.save()

    expense_attribute = ExpenseAttribute.objects.first()
    expense_attribute.value = employee_email
    expense_attribute.save()

    destination_attr = DestinationAttribute.objects.first()
    destination_attr.destination_id = 'emp_123'
    destination_attr.attribute_type = 'EMPLOYEE'
    destination_attr.save()

    employee_mapping = EmployeeMapping.objects.first()
    employee_mapping.source_employee = expense_attribute
    employee_mapping.destination_employee = destination_attr
    employee_mapping.workspace_id = expense_group.workspace_id
    employee_mapping.save()

    configuration = Configuration.objects.get(workspace_id=1)
    mocker.patch('apps.sage_intacct.models.import_string', return_value=lambda *args, **kwargs: (None, False))
    mocker.patch('apps.sage_intacct.models.get_customer_id_or_none', return_value=None)
    mocker.patch('apps.sage_intacct.models.get_item_id_or_none', return_value=None)

    ExpenseReport.create_expense_report(expense_group)

    system_comments = []

    ExpenseReportLineitem.create_expense_report_lineitems(
        expense_group=expense_group,
        configuration=configuration,
        system_comments=system_comments
    )

    billable_comments = [c for c in system_comments if c.get('intent') == 'BILLABLE_DISABLED']
    assert len(billable_comments) >= 1
    comment = billable_comments[0]
    assert comment['source'] == 'CREATE_EXPENSE_REPORT_LINEITEMS'
    assert comment['intent'] == 'BILLABLE_DISABLED'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.BILLABLE_SET_TO_FALSE_MISSING_DIMENSIONS.value
    assert 'missing_fields' in comment['detail']['info']
    assert comment['detail']['info']['original_billable'] is True


def test_billable_disabled_bill_lineitem(db, create_expense_group_expense, mocker):
    """
    Test create_bill_lineitems generates system comment when billable is set to False due to missing customer_id or item_id
    """
    expense_group, expense = create_expense_group_expense

    expense.billable = True
    expense.save()

    employee_email = 'test@fyle.in'
    expense_group.description['employee_email'] = employee_email
    expense_group.save()

    expense_attribute = ExpenseAttribute.objects.first()
    expense_attribute.value = employee_email
    expense_attribute.save()

    destination_attr = DestinationAttribute.objects.first()
    destination_attr.destination_id = 'vendor_123'
    destination_attr.attribute_type = 'VENDOR'
    destination_attr.save()

    employee_mapping = EmployeeMapping.objects.first()
    employee_mapping.source_employee = expense_attribute
    employee_mapping.destination_vendor = destination_attr
    employee_mapping.workspace_id = expense_group.workspace_id
    employee_mapping.save()

    configuration = Configuration.objects.get(workspace_id=1)
    mocker.patch('apps.sage_intacct.models.get_customer_id_or_none', return_value=None)
    mocker.patch('apps.sage_intacct.models.get_item_id_or_none', return_value=None)

    Bill.create_bill(expense_group)

    system_comments = []

    BillLineitem.create_bill_lineitems(
        expense_group=expense_group,
        configuration=configuration,
        system_comments=system_comments
    )

    billable_comments = [c for c in system_comments if c.get('intent') == 'BILLABLE_DISABLED']
    assert len(billable_comments) >= 1
    comment = billable_comments[0]
    assert comment['source'] == 'CREATE_BILL_LINEITEMS'
    assert comment['intent'] == 'BILLABLE_DISABLED'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.BILLABLE_SET_TO_FALSE_MISSING_DIMENSIONS.value
    assert 'missing_fields' in comment['detail']['info']
    assert comment['detail']['info']['original_billable'] is True


def test_billable_disabled_journal_entry_lineitem(db, create_expense_group_expense, mocker):
    """
    Test create_journal_entry_lineitems generates system comment when billable is set to False due to missing customer_id or item_id
    """
    expense_group, expense = create_expense_group_expense

    expense.billable = True
    expense.save()

    employee_email = 'test@fyle.in'
    expense_group.description['employee_email'] = employee_email
    expense_group.save()

    expense_attribute = ExpenseAttribute.objects.first()
    expense_attribute.value = employee_email
    expense_attribute.save()

    destination_attr = DestinationAttribute.objects.first()
    destination_attr.destination_id = 'emp_123'
    destination_attr.attribute_type = 'EMPLOYEE'
    destination_attr.save()

    employee_mapping = EmployeeMapping.objects.first()
    employee_mapping.source_employee = expense_attribute
    employee_mapping.destination_employee = destination_attr
    employee_mapping.workspace_id = expense_group.workspace_id
    employee_mapping.save()

    configuration = Configuration.objects.get(workspace_id=1)
    mocker.patch('apps.sage_intacct.models.import_string', return_value=lambda *args, **kwargs: (None, False))
    mocker.patch('apps.sage_intacct.models.get_customer_id_or_none', return_value=None)
    mocker.patch('apps.sage_intacct.models.get_item_id_or_none', return_value=None)

    JournalEntry.create_journal_entry(expense_group)
    sage_intacct_connection = mocker.MagicMock()

    system_comments = []

    JournalEntryLineitem.create_journal_entry_lineitems(
        expense_group=expense_group,
        configuration=configuration,
        sage_intacct_connection=sage_intacct_connection,
        system_comments=system_comments
    )

    billable_comments = [c for c in system_comments if c.get('intent') == 'BILLABLE_DISABLED']
    assert len(billable_comments) >= 1
    comment = billable_comments[0]
    assert comment['source'] == 'CREATE_JOURNAL_ENTRY_LINEITEMS'
    assert comment['intent'] == 'BILLABLE_DISABLED'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.BILLABLE_SET_TO_FALSE_MISSING_DIMENSIONS.value
    assert 'missing_fields' in comment['detail']['info']
    assert comment['detail']['info']['original_billable'] is True


def test_billable_disabled_charge_card_transaction_lineitem(db, create_expense_group_expense, mocker):
    """
    Test create_charge_card_transaction_lineitems generates system comment when billable is set to False due to missing customer_id or item_id
    """
    expense_group, expense = create_expense_group_expense

    expense.billable = True
    expense.save()

    expense_group.description['employee_email'] = 'test@fyle.in'
    expense_group.save()

    configuration = Configuration.objects.get(workspace_id=1)
    mocker.patch('apps.sage_intacct.models.import_string', return_value=lambda *args, **kwargs: (None, False))
    mocker.patch('apps.sage_intacct.models.get_customer_id_or_none', return_value=None)
    mocker.patch('apps.sage_intacct.models.get_item_id_or_none', return_value=None)

    ChargeCardTransaction.create_charge_card_transaction(expense_group, 'Test Vendor')
    sage_intacct_connection = mocker.MagicMock()

    system_comments = []

    ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems(
        expense_group=expense_group,
        configuration=configuration,
        sage_intacct_connection=sage_intacct_connection,
        system_comments=system_comments
    )

    billable_comments = [c for c in system_comments if c.get('intent') == 'BILLABLE_DISABLED']
    assert len(billable_comments) >= 1
    comment = billable_comments[0]
    assert comment['source'] == 'CREATE_CHARGE_CARD_TRANSACTION_LINEITEMS'
    assert comment['intent'] == 'BILLABLE_DISABLED'
    assert comment['entity_type'] == 'EXPENSE'
    assert comment['entity_id'] == expense.id
    assert comment['detail']['reason'] == SystemCommentReasonEnum.BILLABLE_SET_TO_FALSE_MISSING_DIMENSIONS.value
    assert 'missing_fields' in comment['detail']['info']
    assert comment['detail']['info']['original_billable'] is True


def test_export_summary_not_updated_expense_report(db, mocker, get_or_create_task_log):
    """
    Test create_expense_report generates single system comment per expense group when previous export state is ERROR
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ExpenseReport.create_expense_report')
    mocker.patch('apps.sage_intacct.models.ExpenseReportLineitem.create_expense_report_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_expense_report')
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_expense_report(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_EXPENSE_REPORT'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['entity_type'] == 'EXPENSE_GROUP'
    assert comment['entity_id'] == expense_group.id
    assert comment['export_type'] == 'EXPENSE_REPORT'
    assert comment['detail']['reason'] == SystemCommentReasonEnum.EXPORT_SUMMARY_NOT_UPDATED_ERROR_STATE.value
    assert comment['detail']['info']['previous_export_state'] == 'ERROR'
    assert comment['detail']['info']['is_auto_export'] is True


def test_export_summary_not_updated_bill(db, mocker, get_or_create_task_log):
    """
    Test create_bill generates single system comment per expense group when previous export state is ERROR
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.Bill.create_bill')
    mocker.patch('apps.sage_intacct.models.BillLineitem.create_bill_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_bill')
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_bill(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_BILL'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['entity_type'] == 'EXPENSE_GROUP'
    assert comment['entity_id'] == expense_group.id
    assert comment['export_type'] == 'BILL'
    assert comment['detail']['reason'] == SystemCommentReasonEnum.EXPORT_SUMMARY_NOT_UPDATED_ERROR_STATE.value
    assert comment['detail']['info']['previous_export_state'] == 'ERROR'
    assert comment['detail']['info']['is_auto_export'] is True


def test_export_summary_not_updated_charge_card_transaction(db, mocker, get_or_create_task_log):
    """
    Test create_charge_card_transaction generates single system comment per expense group when previous export state is ERROR
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ChargeCardTransaction.create_charge_card_transaction')
    mocker.patch('apps.sage_intacct.models.ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_charge_card_transaction')
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_charge_card_transaction(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_CHARGE_CARD_TRANSACTION_LINEITEMS'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['entity_type'] == 'EXPENSE_GROUP'
    assert comment['entity_id'] == expense_group.id
    assert comment['export_type'] == 'CHARGE_CARD_TRANSACTION'
    assert comment['detail']['reason'] == SystemCommentReasonEnum.EXPORT_SUMMARY_NOT_UPDATED_ERROR_STATE.value
    assert comment['detail']['info']['previous_export_state'] == 'ERROR'
    assert comment['detail']['info']['is_auto_export'] is True


def test_retrigger_stuck_exports_system_comment(db, mocker, get_or_create_task_log):
    """
    Test retrigger_stuck_exports generates system comment with stuck_duration_seconds
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense_group.updated_at = datetime.now(timezone.utc) - timedelta(hours=2)
    expense_group.save()

    get_or_create_task_log(
        expense_group,
        task_type='FETCHING_EXPENSES',
        status='ENQUEUED',
        updated_at=datetime.now() - timedelta(minutes=90)
    )

    captured_comments = []
    mocker.patch('apps.internal.tasks.export_to_intacct')
    mocker.patch('apps.internal.tasks.update_failed_expenses')
    mocker.patch('apps.internal.tasks.post_accounting_export_summary')
    mocker.patch('apps.internal.tasks.Schedule.objects.filter', return_value=mocker.MagicMock(filter=mocker.MagicMock(return_value=None)))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    retrigger_stuck_exports()

    retrigger_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_RETRIGGERED']
    if retrigger_comments:
        comment = retrigger_comments[0]
        assert comment['source'] == 'RETRIGGER_STUCK_EXPORTS'
        assert comment['intent'] == 'EXPORT_RETRIGGERED'
        assert comment['entity_type'] == 'EXPENSE_GROUP'
        assert comment['detail']['reason'] == SystemCommentReasonEnum.EXPORT_RETRIGGERED_STUCK.value
        assert 'stuck_duration_seconds' in comment['detail']['info']
        assert isinstance(comment['detail']['info']['stuck_duration_seconds'], (int, float))
        assert comment['detail']['info']['stuck_duration_seconds'] > 0


def test_export_summary_not_updated_expense_report_wrong_params_error(db, mocker, get_or_create_task_log):
    """
    Test create_expense_report flushes system comments when WrongParamsError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ExpenseReport.create_expense_report')
    mocker.patch('apps.sage_intacct.models.ExpenseReportLineitem.create_expense_report_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_expense_report', return_value={'key': '123'})
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.get_expense_report', side_effect=WrongParamsError('Some of the parameters are wrong', {}))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_expense_report(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_EXPENSE_REPORT'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'EXPENSE_REPORT'


def test_export_summary_not_updated_expense_report_bulk_error(db, mocker, get_or_create_task_log):
    """
    Test create_expense_report flushes system comments when BulkError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ExpenseReport.create_expense_report')
    mocker.patch('apps.sage_intacct.models.ExpenseReportLineitem.create_expense_report_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_expense_report', side_effect=BulkError({'error': ['Bulk error']}))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_expense_report(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_EXPENSE_REPORT'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'EXPENSE_REPORT'


def test_export_summary_not_updated_bill_wrong_params_error(db, mocker, get_or_create_task_log):
    """
    Test create_bill flushes system comments when WrongParamsError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.Bill.create_bill')
    mocker.patch('apps.sage_intacct.models.BillLineitem.create_bill_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_bill', return_value={'data': {'apbill': {'key': '123'}}})
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.get_bill', side_effect=WrongParamsError('Some of the parameters are wrong', {}))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_bill(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_BILL'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'BILL'


def test_export_summary_not_updated_bill_bulk_error(db, mocker, get_or_create_task_log):
    """
    Test create_bill flushes system comments when BulkError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.Bill.create_bill')
    mocker.patch('apps.sage_intacct.models.BillLineitem.create_bill_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_bill', side_effect=BulkError({'error': ['Bulk error']}))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_bill(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_BILL'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'BILL'


def test_export_summary_not_updated_charge_card_transaction_wrong_params_error(db, mocker, get_or_create_task_log):
    """
    Test create_charge_card_transaction flushes system comments when WrongParamsError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ChargeCardTransaction.create_charge_card_transaction')
    mocker.patch('apps.sage_intacct.models.ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_charge_card_transaction', return_value={'data': {'cctransaction': {'key': '123'}}})
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.get_charge_card_transaction', side_effect=WrongParamsError('Some of the parameters are wrong', {}))
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor', return_value=(mocker.MagicMock(destination_id='vendor123'), False))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_charge_card_transaction(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_CHARGE_CARD_TRANSACTION_LINEITEMS'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'CHARGE_CARD_TRANSACTION'


def test_export_summary_not_updated_charge_card_transaction_bulk_error(db, mocker, get_or_create_task_log):
    """
    Test create_charge_card_transaction flushes system comments when BulkError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ChargeCardTransaction.create_charge_card_transaction')
    mocker.patch('apps.sage_intacct.models.ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_charge_card_transaction', side_effect=BulkError({'error': ['Bulk error']}))
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor', return_value=(mocker.MagicMock(destination_id='vendor123'), False))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_charge_card_transaction(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_CHARGE_CARD_TRANSACTION_LINEITEMS'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'CHARGE_CARD_TRANSACTION'


def test_export_summary_not_updated_expense_report_no_privilege_error(db, mocker, get_or_create_task_log):
    """
    Test create_expense_report flushes system comments when NoPrivilegeError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ExpenseReport.create_expense_report')
    mocker.patch('apps.sage_intacct.models.ExpenseReportLineitem.create_expense_report_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_expense_report', side_effect=NoPrivilegeError('No privilege', {}))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_expense_report(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_EXPENSE_REPORT'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'EXPENSE_REPORT'


def test_export_summary_not_updated_bill_no_privilege_error(db, mocker, get_or_create_task_log):
    """
    Test create_bill flushes system comments when NoPrivilegeError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.Bill.create_bill')
    mocker.patch('apps.sage_intacct.models.BillLineitem.create_bill_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_bill', side_effect=NoPrivilegeError('No privilege', {}))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_bill(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_BILL'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'BILL'


def test_export_summary_not_updated_charge_card_transaction_no_privilege_error(db, mocker, get_or_create_task_log):
    """
    Test create_charge_card_transaction flushes system comments when NoPrivilegeError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ChargeCardTransaction.create_charge_card_transaction')
    mocker.patch('apps.sage_intacct.models.ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_charge_card_transaction', side_effect=NoPrivilegeError('No privilege', {}))
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor', return_value=(mocker.MagicMock(destination_id='vendor123'), False))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_charge_card_transaction(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_CHARGE_CARD_TRANSACTION_LINEITEMS'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'CHARGE_CARD_TRANSACTION'


def test_export_summary_not_updated_expense_report_rest_bad_request_error(db, mocker, get_or_create_task_log):
    """
    Test create_expense_report flushes system comments when IntacctRESTBadRequestError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ExpenseReport.create_expense_report')
    mocker.patch('apps.sage_intacct.models.ExpenseReportLineitem.create_expense_report_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_expense_report', side_effect=IntacctRESTBadRequestError('Bad request', {}))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_expense_report(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_EXPENSE_REPORT'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'EXPENSE_REPORT'


def test_export_summary_not_updated_bill_rest_bad_request_error(db, mocker, get_or_create_task_log):
    """
    Test create_bill flushes system comments when IntacctRESTBadRequestError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.Bill.create_bill')
    mocker.patch('apps.sage_intacct.models.BillLineitem.create_bill_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_bill', side_effect=IntacctRESTBadRequestError('Bad request', {}))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_bill(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_BILL'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'BILL'


def test_export_summary_not_updated_charge_card_transaction_rest_bad_request_error(db, mocker, get_or_create_task_log):
    """
    Test create_charge_card_transaction flushes system comments when IntacctRESTBadRequestError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ChargeCardTransaction.create_charge_card_transaction')
    mocker.patch('apps.sage_intacct.models.ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_charge_card_transaction', side_effect=IntacctRESTBadRequestError('Bad request', {}))
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor', return_value=(mocker.MagicMock(destination_id='vendor123'), False))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_charge_card_transaction(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_CHARGE_CARD_TRANSACTION_LINEITEMS'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'CHARGE_CARD_TRANSACTION'


def test_export_summary_not_updated_expense_report_rest_internal_server_error(db, mocker, get_or_create_task_log):
    """
    Test create_expense_report flushes system comments when IntacctRESTInternalServerError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ExpenseReport.create_expense_report')
    mocker.patch('apps.sage_intacct.models.ExpenseReportLineitem.create_expense_report_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_expense_report', side_effect=IntacctRESTInternalServerError('Internal server error', {}))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_expense_report(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_EXPENSE_REPORT'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'EXPENSE_REPORT'


def test_export_summary_not_updated_bill_rest_internal_server_error(db, mocker, get_or_create_task_log):
    """
    Test create_bill flushes system comments when IntacctRESTInternalServerError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.Bill.create_bill')
    mocker.patch('apps.sage_intacct.models.BillLineitem.create_bill_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_bill', side_effect=IntacctRESTInternalServerError('Internal server error', {}))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_bill(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_BILL'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'BILL'


def test_export_summary_not_updated_charge_card_transaction_rest_internal_server_error(db, mocker, get_or_create_task_log):
    """
    Test create_charge_card_transaction flushes system comments when IntacctRESTInternalServerError occurs
    """
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    assert expense_group is not None, "No expense group available for test"

    expense = expense_group.expenses.first()
    expense.previous_export_state = 'ERROR'
    expense.save()

    task_log = get_or_create_task_log(expense_group)

    captured_comments = []
    mocker.patch('apps.sage_intacct.models.ChargeCardTransaction.create_charge_card_transaction')
    mocker.patch('apps.sage_intacct.models.ChargeCardTransactionLineitem.create_charge_card_transaction_lineitems')
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.post_charge_card_transaction', side_effect=IntacctRESTInternalServerError('Internal server error', {}))
    mocker.patch('apps.sage_intacct.utils.SageIntacctConnector.get_or_create_vendor', return_value=(mocker.MagicMock(destination_id='vendor123'), False))
    mocker.patch.object(SystemComment, 'bulk_create_comments', side_effect=lambda comments: captured_comments.extend(comments))

    create_charge_card_transaction(
        expense_group_id=expense_group.id,
        task_log_id=task_log.id,
        last_export=True,
        is_auto_export=True
    )

    export_summary_comments = [c for c in captured_comments if c.get('intent') == 'EXPORT_SUMMARY_NOT_UPDATED']
    assert len(export_summary_comments) == 1
    comment = export_summary_comments[0]
    assert comment['source'] == 'CREATE_CHARGE_CARD_TRANSACTION_LINEITEMS'
    assert comment['intent'] == 'EXPORT_SUMMARY_NOT_UPDATED'
    assert comment['export_type'] == 'CHARGE_CARD_TRANSACTION'
