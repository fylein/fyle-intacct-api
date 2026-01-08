from enum import Enum


class CacheKeyEnum(str, Enum):
    """
    Cache key enum
    """
    FYLE_SYNC_DIMENSIONS = "sync_dimensions_{workspace_id}"
    SAGE_INTACCT_SYNC_DIMENSIONS = "sync_sage_intacct_dimensions_{workspace_id}"
    FEATURE_CONFIG_MIGRATED_TO_REST_API = "migrated_to_rest_api_{workspace_id}"
    FEATURE_CONFIG_IMPORT_BILLABLE_FIELD_FOR_PROJECTS = "import_billable_field_for_projects_{workspace_id}"
