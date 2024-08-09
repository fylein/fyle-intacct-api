import logging
import traceback
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
from apps.mappings.models import ImportLog
from apps.workspaces.models import SageIntacctCredential


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_import_exceptions(func):
    def new_fn(expense_attribute_instance, *args):
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
            return func(expense_attribute_instance, *args)
        except WrongParamsError as exception:
            error['message'] = exception.message
            error['response'] = exception.response
            error['alert'] = True
            import_log.status = 'FAILED'

        except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
            error['message'] = 'Invalid Token or Sage Intacct credentials does not exist workspace_id - {0}'.format(workspace_id)
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

        if import_log.attribute_type == 'COST_TYPE' and import_log.status in ['FAILED', 'FATAL']:
            cost_code_log = ImportLog.objects.filter(workspace_id=import_log.workspace_id, attribute_type='COST_CODE').first()
            if cost_code_log and cost_code_log.status == 'IN_PROGRESS':
                cost_code_log.status = 'FAILED'
                cost_code_log.error_log = error
                cost_code_log.save()

    return new_fn
