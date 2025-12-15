import logging
import traceback

from intacctsdk.exceptions import (
    BadRequestError as SageIntacctRESTBadRequestError,
    InvalidTokenError as SageIntacctRestInvalidTokenError,
    InternalServerError as SageIntacctRESTInternalServerError
)
from sageintacctsdk.exceptions import (
    InvalidTokenError,
    NoPrivilegeError,
    SageIntacctSDKError
)
from fyle.platform.exceptions import (
    WrongParamsError,
    InvalidTokenError as FyleInvalidTokenError,
    InternalServerError,
    RetryException as FyleRetryException
)

from fyle_integrations_imports.models import ImportLog
from apps.workspaces.models import SageIntacctCredential
from fyle_intacct_api.utils import invalidate_sage_intacct_credentials

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_import_exceptions_v2(func: callable) -> callable:
    """
    Decorator to handle exceptions while importing to Fyle
    :param func: function
    :return: function
    """
    def new_fn(expense_attribute_instance: any, *args, **kwargs) -> callable:
        import_log = None
        if isinstance(expense_attribute_instance, ImportLog):
            import_log: ImportLog = expense_attribute_instance
        else:
            import_log: ImportLog = args[0]
        workspace_id = import_log.workspace_id
        attribute_type = import_log.attribute_type
        error = {
            'task': 'Import {0} to Fyle and Auto Create Mappings'.format(attribute_type),
            'workspace_id': workspace_id,
            'message': None,
            'response': None
        }
        try:
            return func(expense_attribute_instance, *args, **kwargs)
        except WrongParamsError as exception:
            error['message'] = exception.message
            error['response'] = exception.response
            error['alert'] = True
            import_log.status = 'FAILED'

        except SageIntacctCredential.DoesNotExist:
            error['message'] = 'Sage Intacct credentials does not exist workspace_id - {0}'.format(workspace_id)
            error['alert'] = False
            import_log.status = 'FAILED'

        except (InvalidTokenError, SageIntacctRestInvalidTokenError):
            invalidate_sage_intacct_credentials(workspace_id)
            error['message'] = 'Invalid Sage Intacct Token Error for workspace_id - {0}'.format(workspace_id)
            error['alert'] = False
            import_log.status = 'FAILED'

        except (SageIntacctRESTBadRequestError, SageIntacctRESTInternalServerError) as e:
            error['message'] = 'Sage Intacct REST API error for workspace_id - {0}: {1}'.format(workspace_id, e.response)
            error['alert'] = False
            import_log.status = 'FAILED'

        except FyleInvalidTokenError:
            error['message'] = 'Invalid Token for fyle'
            error['alert'] = False
            import_log.status = 'FAILED'

        except FyleRetryException:
            error['message'] = 'Fyle Retry Exception occured'
            error['alert'] = False
            import_log.status = 'FAILED'

        except InternalServerError:
            error['message'] = 'Internal server error while importing to Fyle'
            error['alert'] = True
            import_log.status = 'FAILED'

        except NoPrivilegeError:
            error['message'] = 'Insufficient permission to access the requested module'
            error['alert'] = False
            import_log.status = 'FAILED'

        except SageIntacctSDKError as exception:
            error['message'] = exception.message
            error['alert'] = False
            import_log.status = 'FAILED'

        except Exception:
            response = traceback.format_exc()
            error['message'] = 'Something went wrong'
            error['response'] = response
            error['alert'] = False
            import_log.status = 'FATAL'

        if error['alert']:
            logger.error(error)
        else:
            logger.info(error)

        import_log.error_log = error
        import_log.save()

    return new_fn
