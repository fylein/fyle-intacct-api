import pytest
from apps.mappings.exceptions import handle_exceptions
from apps.mappings.models import ImportLog
from apps.mappings.imports.modules.projects import Project
from fyle.platform.exceptions import (
    WrongParamsError,
    InvalidTokenError as FyleInvalidTokenError,
    InternalServerError
)
from sageintacctsdk.exceptions import InvalidTokenError, NoPrivilegeError
from apps.workspaces.models import SageIntacctCredential

def test_handle_exceptions(db):
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
    @handle_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise WrongParamsError('This is WrongParamsError')
    
    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['type'] == 'WrongParamsError'
    assert import_log.error_log['message'] == 'This is WrongParamsError'
    assert import_log.error_log['alert'] == True

    # FyleInvalidTokenError 
    @handle_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise FyleInvalidTokenError('This is FyleInvalidTokenError')
    
    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['type'] == 'FyleInvalidTokenError'
    assert import_log.error_log['message'] == 'Invalid Token for fyle'
    assert import_log.error_log['alert'] == False

    # InternalServerError 
    @handle_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise InternalServerError('This is InternalServerError')
    
    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['type'] == 'InternalServerError'
    assert import_log.error_log['message'] == 'Internal server error while importing to Fyle'
    assert import_log.error_log['alert'] == True

    # InvalidTokenError 
    @handle_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise InvalidTokenError('This is InvalidTokenError')
    
    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['type'] == 'SageIntacctCredential.DoesNotExist/InvalidTokenError'
    assert import_log.error_log['message'] == 'Invalid Token or Sage Intacct credentials does not exist workspace_id - 1'
    assert import_log.error_log['alert'] == True

    # SageIntacctCredential.DoesNotExist
    @handle_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise SageIntacctCredential.DoesNotExist('This is SageIntacctCredential.DoesNotExist')
    
    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['type'] == 'SageIntacctCredential.DoesNotExist/InvalidTokenError'
    assert import_log.error_log['message'] == 'Invalid Token or Sage Intacct credentials does not exist workspace_id - 1'
    assert import_log.error_log['alert'] == True

    # NoPrivilegeError
    @handle_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise NoPrivilegeError('This is NoPrivilegeError')
    
    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['type'] == 'NoPrivilegeError'
    assert import_log.error_log['message'] == 'Insufficient permission to access the requested module'
    assert import_log.error_log['alert'] == False

    # Exception
    @handle_exceptions
    def to_be_decoreated(expense_attribute_instance, import_log):
        raise Exception('This is a general Exception')
    
    to_be_decoreated(project, import_log)

    assert import_log.status == 'FAILED'
    assert import_log.error_log['task'] == 'Import PROJECT to Fyle and Auto Create Mappings'
    assert import_log.error_log['type'] == 'Uknown Exception'
    assert import_log.error_log['message'] == 'Something went wrong'
    assert import_log.error_log['alert'] == True
