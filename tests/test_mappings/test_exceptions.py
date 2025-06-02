from fyle.platform.exceptions import (
    WrongParamsError,
    InvalidTokenError as FyleInvalidTokenError,
    InternalServerError
)
from sageintacctsdk.exceptions import (
    InvalidTokenError,
    NoPrivilegeError,
    SageIntacctSDKError
)

from apps.mappings.models import ImportLog
from apps.workspaces.models import SageIntacctCredential
from apps.mappings.imports.modules.projects import Project
from apps.exceptions import handle_view_exceptions
from apps.mappings.exceptions import handle_import_exceptions


def test_handle_import_exceptions(db):
    """
    Test handle_import_exceptions decorator
    """
    ImportLog.objects.create(
        workspace_id=1,
        status = 'IN_PROGRESS',
        attribute_type = 'PROJECT',
        total_batches_count = 10,
        processed_batches_count = 2,
        error_log = []
    )
    import_log = ImportLog.objects.get(workspace_id=1, attribute_type='PROJECT')
    project = Project(1, 'PROJECT', None)

    # WrongParamsError
    @handle_import_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise WrongParamsError('This is WrongParamsError')

    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['message'] == 'This is WrongParamsError'
    assert import_log.error_log['alert'] == True

    # FyleInvalidTokenError
    @handle_import_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise FyleInvalidTokenError('This is FyleInvalidTokenError')

    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['message'] == 'Invalid Token for fyle'
    assert import_log.error_log['alert'] == False

    # InternalServerError
    @handle_import_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise InternalServerError('This is InternalServerError')

    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['message'] == 'Internal server error while importing to Fyle'
    assert import_log.error_log['alert'] == True

    # InvalidTokenError
    @handle_import_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise InvalidTokenError('This is InvalidTokenError')

    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['message'] == 'Invalid Sage Intacct Token Error for workspace_id - 1'
    assert import_log.error_log['alert'] == False

    # SageIntacctCredential.DoesNotExist
    @handle_import_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise SageIntacctCredential.DoesNotExist('This is SageIntacctCredential.DoesNotExist')

    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['message'] == 'Sage Intacct credentials does not exist workspace_id - 1'
    assert import_log.error_log['alert'] == False

    # NoPrivilegeError
    @handle_import_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise NoPrivilegeError('This is NoPrivilegeError')

    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['message'] == 'Insufficient permission to access the requested module'
    assert import_log.error_log['alert'] == False

    # SageIntacctSDKError
    @handle_import_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise SageIntacctSDKError('This is a sage intacct sdk error')

    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['message'] == 'This is a sage intacct sdk error'
    assert import_log.error_log['alert'] == False

    # Exception
    @handle_import_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise Exception('This is a general Exception')

    to_be_decoreated(project, import_log)

    assert import_log.status == 'FATAL'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['message'] == 'Something went wrong'
    assert import_log.error_log['alert'] == False


def test_handle_views_exception():
    """
    Test handle_views_exception decorator
    """
    # Exception
    @handle_view_exceptions()
    def to_be_decorated():
        raise Exception('This is Exception')

    response = to_be_decorated()

    assert response.status_code == 400
    assert response.data['message'] == 'An unhandled error has occurred, please re-try later'
