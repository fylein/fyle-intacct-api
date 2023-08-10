import logging
import traceback
from sageintacctsdk.exceptions import (
    InvalidTokenError,
    NoPrivilegeError
)
from fyle.platform.exceptions import (
    WrongParamsError,
    InvalidTokenError as FyleInvalidTokenError,
    InternalServerError
)
from apps.mappings.models import ImportLog
from apps.workspaces.models import SageIntacctCredential


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_exceptions(func):
    def new_fn(expense_attribute_instance, *args):
        import_log: ImportLog = args[0]
        workspace_id = import_log.workspace_id
        attribute_type = import_log.attribute_type
        error = {
            'task': 'Import {0} to Fyle and Auto Create Mappings'.format(attribute_type),
            'workspace_id': workspace_id,
            'alert': False,
            'type':None,
            'message': None,
            'response': None
        }
        try:
            return func(expense_attribute_instance, *args)
        except WrongParamsError as exception:
            error['message'] = exception.message
            error['response'] = exception.response
            error['alert'] = True
            error['type'] = 'WrongParamsError'

        except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
            error['message'] = 'Invalid Token or Sage Intacct credentials does not exist workspace_id - {0}'.format(workspace_id)
            error['alert'] = True
            error['type'] = 'SageIntacctCredential.DoesNotExist/InvalidTokenError'

        except FyleInvalidTokenError:
            error['message'] = 'Invalid Token for fyle'
            error['type'] = 'FyleInvalidTokenError'
        
        except InternalServerError:
            error['message'] = 'Internal server error while importing to Fyle'
            error['type'] = 'InternalServerError'
            error['alert'] = True
        
        except NoPrivilegeError:
            error['message'] = 'Insufficient permission to access the requested module'
            error['type'] = 'NoPrivilegeError'


        except Exception:
            response = traceback.format_exc()
            error['message'] = 'Something went wrong'
            error['response'] = response
            error['alert'] = True
            error['type'] = 'Uknown Exception'

        if error['alert']:
            logger.error(error)
        else:
            logger.info(error)
        
        import_log.status = 'FAILED'
        import_log.error_log = error
        import_log.save()

    return new_fn
