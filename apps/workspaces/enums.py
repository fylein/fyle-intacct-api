from enum import Enum


class CacheKeyEnum(str, Enum):
    """
    Cache key enum
    """
    FYLE_SYNC_DIMENSIONS = "sync_dimensions_{workspace_id}"
    FEATURE_CONFIG_MIGRATED_TO_REST_API = "migrated_to_rest_api_{workspace_id}"
    SAGE_INTACCT_SYNC_DIMENSIONS = "sync_sage_intacct_dimensions_{workspace_id}"
    FEATURE_CONFIG_IMPORT_BILLABLE_FIELD_FOR_PROJECTS = "import_billable_field_for_projects_{workspace_id}"


class SystemCommentSourceEnum(str, Enum):
    """
    Source function/method that generated the comment
    """
    # Dimension resolution functions
    GET_PROJECT_ID = 'GET_PROJECT_ID'
    GET_DEPARTMENT_ID = 'GET_DEPARTMENT_ID'
    GET_LOCATION_ID = 'GET_LOCATION_ID'
    GET_ITEM_ID = 'GET_ITEM_ID'
    GET_CLASS_ID = 'GET_CLASS_ID'
    GET_TAX_CODE_ID = 'GET_TAX_CODE_ID'
    GET_CCC_ACCOUNT_ID = 'GET_CCC_ACCOUNT_ID'

    # Export functions
    CREATE_BILL = 'CREATE_BILL'

    # Import/sync functions
    HANDLE_CATEGORY_CHANGE = 'HANDLE_CATEGORY_CHANGE'
    HANDLE_FUND_SOURCE_CHANGE = 'HANDLE_FUND_SOURCE_CHANGE'
    HANDLE_REPORT_CHANGE = 'HANDLE_REPORT_CHANGE'
    RECREATE_EXPENSE_GROUPS = 'RECREATE_EXPENSE_GROUPS'
    DELETE_EXPENSE_GROUP_AND_RELATED_DATA = 'DELETE_EXPENSE_GROUP_AND_RELATED_DATA'
    DELETE_EXPENSES = 'DELETE_EXPENSES'


class SystemCommentIntentEnum(str, Enum):
    """
    Intent describing the action taken
    """
    DEFAULT_VALUE_APPLIED = 'DEFAULT_VALUE_APPLIED'
    EMPLOYEE_DEFAULT_VALUE_APPLIED = 'EMPLOYEE_DEFAULT_VALUE_APPLIED'
    UPDATE_EXPENSE_FUND_SOURCE = 'UPDATE_EXPENSE_FUND_SOURCE'
    UPDATE_EXPENSE_CATEGORY = 'UPDATE_EXPENSE_CATEGORY'
    UPDATE_EXPENSE_REPORT = 'UPDATE_EXPENSE_REPORT'
    RECREATE_EXPENSE_GROUPS = 'RECREATE_EXPENSE_GROUPS'
    DELETE_EXPENSE_GROUP = 'DELETE_EXPENSE_GROUP'
    DELETE_EXPENSES = 'DELETE_EXPENSES'


class SystemCommentReasonEnum(str, Enum):
    """
    Human readable reason explaining why a particular action was taken
    """
    # Default values applied - explaining WHY
    DEFAULT_ITEM_APPLIED = 'No item mapping found for expense category. Using default item from general mappings.'
    DEFAULT_CLASS_APPLIED = 'No class mapping found for the mapped source field. Using default class from general mappings.'
    DEFAULT_PROJECT_APPLIED = 'No project mapping found for the mapped source field. Using default project from general mappings.'
    DEFAULT_TAX_CODE_APPLIED = 'No tax code mapping found for expense tax group. Using default tax code from general mappings.'
    DEFAULT_LOCATION_APPLIED = 'No location mapping found for the mapped source field. Using default location from general mappings.'
    DEFAULT_DEPARTMENT_APPLIED = 'No department mapping found for the mapped source field. Using default department from general mappings.'
    DEFAULT_CCC_VENDOR_APPLIED = 'No corporate card to vendor mapping found. Using default CCC vendor from general mappings for bill creation.'
    DEFAULT_CREDIT_CARD_APPLIED = 'No corporate card mapping found and no employee card account set. Using default charge card from general mappings.'

    # Fallback values applied - explaining WHY
    EMPLOYEE_LOCATION_APPLIED = 'No location mapping found for expense. Using employee location from Sage Intacct as configured in general mappings.'
    EMPLOYEE_DEPARTMENT_APPLIED = 'No department mapping found for expense. Using employee department from Sage Intacct as configured in general mappings.'

    # Fund source & report changes - explaining WHY
    FUND_SOURCE_CHANGED = 'Expense payment source was changed in Fyle from {old} to {new}.'
    CATEGORY_CHANGED = 'Expense category was updated in Fyle from {old} to {new}.'
    EXPENSE_ADDED_TO_REPORT = 'Expense was added to a report in Fyle.'
    EXPENSE_EJECTED_FROM_REPORT = 'Expense was removed from its report in Fyle. Expense has been removed from its expense group.'
    EXPENSE_GROUPS_RECREATED = 'Expense groups were recreated after fund source change.'
    EXPENSE_GROUP_AND_RELATED_DATA_DELETED = 'Expense group and all related data (task logs, errors) were deleted.'
    EXPENSES_DELETED_NO_EXPORT_SETTING = 'Expenses were deleted because no export setting is configured for their fund source (reimbursable/corporate card).'


class SystemCommentEntityTypeEnum(str, Enum):
    """
    Type of entity the comment is associated with
    """
    EXPENSE = 'EXPENSE'
    EXPENSE_GROUP = 'EXPENSE_GROUP'


class SystemCommentExportTypeEnum(str, Enum):
    """
    Export type for the comment
    """
    BILL = 'BILL'
    EXPENSE_REPORT = 'EXPENSE_REPORT'
    JOURNAL_ENTRY = 'JOURNAL_ENTRY'
    CHARGE_CARD_TRANSACTION = 'CHARGE_CARD_TRANSACTION'
