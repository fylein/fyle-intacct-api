import logging
import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fyle_intacct_api.settings")
django.setup()

from apps.fyle.helpers import sync_dimensions as sync_fyle_dimensions
from apps.sage_intacct.helpers import sync_dimensions as sync_intacct_dimensions
from apps.workspaces.models import SageIntacctCredential, FyleCredential


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def sync_dimensions(workspace_id: int) -> None:
    """
    Sync dimensions from Fyle and Sage Intacct
    """
    try:
        logger.info('Syncing dimensions for workspace - {}'.format(workspace_id))
        fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
        sync_fyle_dimensions(fyle_credentials)
        logger.info('Synced Fyle dimensions for workspace - {}'.format(workspace_id))
    except Exception as e:
        logger.info('Error while syncing Fyle dimensions for workspace - {}'.format(workspace_id))

    try:
        logger.info('Syncing Sage Intacct dimensions for workspace - {}'.format(workspace_id))
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
        sync_intacct_dimensions(sage_intacct_credentials, workspace_id)
        logger.info('Synced Sage Intacct dimensions for workspace - {}'.format(workspace_id))
    except Exception as e:
        logger.info('Error while syncing Sage Intacct dimensions for workspace - {}'.format(workspace_id))
