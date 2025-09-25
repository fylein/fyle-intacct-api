from enum import Enum


class CacheKeyEnum(str, Enum):
    """
    Cache key enum
    """
    FYLE_SYNC_DIMENSIONS = "sync_dimensions_{workspace_id}"
    SAGE_INTACCT_SYNC_DIMENSIONS = "sync_sage_intacct_dimensions_{workspace_id}"
