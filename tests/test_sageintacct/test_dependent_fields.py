import logging
from datetime import datetime

from unittest import mock


from fyle_integrations_platform_connector import PlatformConnector

from sageintacctsdk.exceptions import InvalidTokenError, NoPrivilegeError, SageIntacctSDKError
from fyle.platform.exceptions import InvalidTokenError as FyleInvalidTokenError

from apps.fyle.models import DependentFieldSetting
from apps.sage_intacct.dependent_fields import (
    create_dependent_custom_field_in_fyle,
    post_dependent_cost_type, post_dependent_cost_code, post_dependent_expense_field_values,
    import_dependent_fields_to_fyle
)
from apps.workspaces.models import FyleCredential

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def test_create_dependent_custom_field_in_fyle(mocker, db):
    mocker.patch(
        'fyle.platform.apis.v1beta.admin.ExpenseFields.post',
        return_value={'id': 123}
    )
    workspace_id = 1
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)
    created_field = create_dependent_custom_field_in_fyle(workspace_id, 'Cost Code', platform, 123)

    assert created_field == {'id': 123}


def test_post_dependent_cost_type(mocker, db, create_cost_type, create_dependent_field_setting):
    workspace_id = 1
    mock = mocker.patch(
        'fyle.platform.apis.v1beta.admin.DependentExpenseFieldValues.bulk_post_dependent_expense_field_values',
        return_value=None
    )
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)

    post_dependent_cost_type(create_dependent_field_setting, platform, {'workspace_id': 1})

    assert mock.call_count == 1


def test_post_dependent_cost_code(mocker, db, create_cost_type, create_dependent_field_setting):
    workspace_id = 1
    mock = mocker.patch(
        'fyle.platform.apis.v1beta.admin.DependentExpenseFieldValues.bulk_post_dependent_expense_field_values',
        return_value=None
    )
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)

    posted_cost_types = post_dependent_cost_code(create_dependent_field_setting, platform, {'workspace_id': 1})

    assert mock.call_count == 1
    assert posted_cost_types == ['task']


def test_post_dependent_expense_field_values(db, mocker, create_cost_type, create_dependent_field_setting):
    workspace_id = 1
    mock = mocker.patch(
        'fyle.platform.apis.v1beta.admin.DependentExpenseFieldValues.bulk_post_dependent_expense_field_values',
        return_value=None
    )

    current_datetime = datetime.now()
    post_dependent_expense_field_values(workspace_id, create_dependent_field_setting)
    assert DependentFieldSetting.objects.get(id=create_dependent_field_setting.id).last_successful_import_at != current_datetime
    
    # There should be 2 post calls, 1 for cost_type and 1 for cost_code
    assert mock.call_count == 2

    create_dependent_field_setting.last_successful_import_at = current_datetime
    create_dependent_field_setting.save()
    post_dependent_expense_field_values(workspace_id, create_dependent_field_setting)

    # Since we've updated timestamp and there would no new cost_types, the mock call count should still exist as 2
    assert mock.call_count == 2


def test_import_dependent_fields_to_fyle(db, mocker, create_cost_type, create_dependent_field_setting):
    workspace_id = 1
    with mock.patch('fyle.platform.apis.v1beta.admin.DependentExpenseFieldValues.bulk_post_dependent_expense_field_values') as mock_call:
        mock_call.side_effect = InvalidTokenError(msg='invalid params', response='invalid params')
        import_dependent_fields_to_fyle(workspace_id)

        mock_call.side_effect = Exception('something went wrong')
        import_dependent_fields_to_fyle(workspace_id)

        mock_call.side_effect = NoPrivilegeError(msg='no prev', response='invalid login')
        import_dependent_fields_to_fyle(workspace_id)

        mock_call.side_effect = None
        import_dependent_fields_to_fyle(workspace_id)

        mock_call.side_effect = FyleInvalidTokenError('Invalid Token')
        import_dependent_fields_to_fyle(workspace_id)

        mock_call.side_effect = SageIntacctSDKError('something went wrong')
        import_dependent_fields_to_fyle(workspace_id)

        assert mock_call.call_count == 0
