import logging
import traceback

from sageintacctsdk.exceptions import InvalidTokenError, NoPrivilegeError
from fyle.platform.exceptions import WrongParamsError, InvalidTokenError, InternalServerError
from apps.mappings.models import ImportLog
import requests


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_exceptions():
    def decorator(func):
        def new_fn(import_log: ImportLog, *args):
            workspace_id = import_log.workspace_id
            error = {
                'task': 'Import {0} to Fyle and Auto Create Mappings'.format(import_log.attribute_type),
                'workspace_id': workspace_id,
                'alert': False,
                'message': None,
                'response': None
            }
            try:
                return func(*args)
            except InvalidTokenError:
                error['message'] = 'Invalid Fyle refresh token'

            except WrongParamsError as exception:
                error['message'] = exception.message
                error['response'] = exception.response
                error['alert'] = True

            except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
                error['message'] = 'Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id
    
            except FyleInvalidTokenError:
                error['message'] = 'Invalid Token for fyle'
            
            except InternalServerError:
                error['message'] = 'Internal server error while importing to Fyle'
                error['alert'] = True
            
            except NoPrivilegeError:
                error['message'] = 'Insufficient permission to access the requested module'

            except WrongParamsError as exception:
                logger.error(
                    'Error while creating projects workspace_id - %s in Fyle %s %s',
                    workspace_id, exception.message, {'error': exception.response}
                )

            except Exception:
                response = traceback.format_exc()
                error['message'] = 'Something went wrong'
                error['response'] = response
                error['alert'] = True

            if error['alert']:
                logger.error(error)
            else:
                logger.info(error)

        return new_fn

    return decorator