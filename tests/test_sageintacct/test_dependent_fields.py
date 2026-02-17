import logging
from datetime import datetime, timedelta, timezone
from unittest import mock

from fyle.platform.exceptions import InvalidTokenError as FyleInvalidTokenError
from fyle_accounting_mappings.models import ExpenseAttribute
from fyle_integrations_platform_connector import PlatformConnector
from sageintacctsdk.exceptions import InvalidTokenError, NoPrivilegeError, SageIntacctSDKError

from apps.fyle.models import DependentFieldSetting
from apps.sage_intacct.dependent_fields import (
    construct_custom_field_placeholder,
    create_dependent_custom_field_in_fyle,
    disable_and_post_cost_code_from_cost_code_table,
    import_dependent_fields_to_fyle,
    post_dependent_cost_code,
    post_dependent_cost_code_standalone,
    post_dependent_cost_type,
    post_dependent_expense_field_values,
    remove_duplicate_payload_entries,
    reset_flag_and_disable_cost_type_field,
)
from apps.sage_intacct.models import CostCode, CostType
from apps.workspaces.models import FyleCredential
from fyle_integrations_imports.models import ImportLog
from tests.helper import dict_compare_keys
from tests.test_sageintacct.fixtures import data

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def test_create_dependent_custom_field_in_fyle(mocker, db):
    """
    Test create_dependent_custom_field_in_fyle
    """
    mocker.patch(
        'fyle.platform.apis.v1.admin.ExpenseFields.post',
        return_value={'id': 123}
    )
    workspace_id = 1
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)
    created_field = create_dependent_custom_field_in_fyle(workspace_id, 'Cost Code', platform, 123)

    assert created_field == {'id': 123}


def test_post_dependent_cost_type(mocker, db, create_cost_type, create_dependent_field_setting):
    """
    Test post_dependent_cost_type
    """
    workspace_id = 1
    mock = mocker.patch(
        'fyle.platform.apis.v1.admin.DependentExpenseFieldValues.bulk_post_dependent_expense_field_values',
        return_value=None
    )
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)

    import_log = ImportLog.update_or_create_in_progress_import_log(attribute_type='COST_TYPE', workspace_id=workspace_id)
    cost_types = CostType.objects.filter(workspace_id=workspace_id, is_imported=False)
    assert cost_types.count() == 1

    post_dependent_cost_type(import_log, create_dependent_field_setting, platform, {'workspace_id': 1})

    assert mock.call_count == 1
    assert import_log.status == 'COMPLETE'
    assert import_log.total_batches_count == 1
    assert import_log.processed_batches_count == 1

    import_log.status = 'IN_PROGRESS'
    import_log.save()
    CostType.objects.filter(workspace_id=workspace_id, is_imported=True).update(is_imported=False)

    mock.side_effect = Exception('Something went wrong')
    post_dependent_cost_type(import_log, create_dependent_field_setting, platform, {'workspace_id': 1})
    assert import_log.status == 'PARTIALLY_FAILED'

    import_log.status = 'IN_PROGRESS'
    import_log.save()

    cost_types = CostType.objects.filter(workspace_id=workspace_id, is_imported=True).update(is_imported=False)

    mocker.patch('apps.sage_intacct.dependent_fields.post_dependent_cost_code', side_effect=Exception('Something went wrong'))
    post_dependent_cost_type(import_log, create_dependent_field_setting, platform, {'workspace_id': 1})

    assert import_log.status == 'PARTIALLY_FAILED'


def test_post_dependent_cost_code(mocker, db, create_cost_type, create_dependent_field_setting):
    """
    Test post_dependent_cost_code
    """
    workspace_id = 1
    mock = mocker.patch(
        'fyle.platform.apis.v1.admin.DependentExpenseFieldValues.bulk_post_dependent_expense_field_values',
        return_value=None
    )
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)

    import_log = ImportLog.update_or_create_in_progress_import_log(attribute_type='COST_CODE', workspace_id=workspace_id)

    ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT', value='pro').update(active=True)
    posted_cost_types, is_errored = post_dependent_cost_code(import_log, create_dependent_field_setting, platform, {'workspace_id': 1})

    assert mock.call_count == 1
    assert posted_cost_types == {'task'}
    assert is_errored is False
    assert import_log.status == 'COMPLETE'
    assert import_log.total_batches_count == 1
    assert import_log.processed_batches_count == 1

    import_log.status = 'IN_PROGRESS'
    import_log.save()

    mock.side_effect = Exception('Something went wrong')
    posted_cost_types, is_errored = post_dependent_cost_code(import_log, create_dependent_field_setting, platform, {'workspace_id': 1})

    assert import_log.status == 'PARTIALLY_FAILED'

    import_log.status = 'IN_PROGRESS'
    import_log.save()

    mocker.patch('apps.sage_intacct.dependent_fields.sync_sage_intacct_attributes', side_effect=Exception('Something went wrong'))
    post_dependent_cost_code(import_log, create_dependent_field_setting, platform, {'workspace_id': 1})

    assert import_log.status == 'PARTIALLY_FAILED'


def test_post_dependent_cost_code_2(mocker, db, add_project_mappings, create_dependent_field_setting):
    """
    Test post_dependent_cost_code
    """
    workspace_id = 1
    mock = mocker.patch(
        'fyle.platform.apis.v1.admin.DependentExpenseFieldValues.bulk_post_dependent_expense_field_values',
        return_value=None
    )
    fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)

    import_log = ImportLog.update_or_create_in_progress_import_log(attribute_type='COST_CODE', workspace_id=workspace_id)

    CostCode.objects.create(
        workspace_id=workspace_id,
        task_name='cost code 123',
        task_id='1',
        project_id='10064',
        project_name='Direct Mail Campaign'
    )

    CostCode.objects.create(
        workspace_id=workspace_id,
        task_name='cost code 123',
        task_id='1',
        project_id='10065',
        project_name='CRE Platform'
    )

    CostCode.objects.create(
        workspace_id=workspace_id,
        task_name='cost code 234',
        task_id='2',
        project_id='10065',
        project_name='CRE Platform'
    )
    DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(last_successful_import_at=None, is_cost_type_import_enabled=False)
    dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=workspace_id).first()
    assert ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT', value__in=['CRE Platform', 'Direct Mail Campaign']).count() == 2

    ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT', value__in=['CRE Platform', 'Direct Mail Campaign']).update(active=True)
    posted_cost_types, is_errored = post_dependent_cost_code(import_log, dependent_field_setting, platform, {'workspace_id': 1})

    assert mock.call_count == 2
    assert posted_cost_types == {'cost code 123', 'cost code 234'}
    assert is_errored is False
    assert import_log.status == 'COMPLETE'
    assert import_log.total_batches_count == 2
    assert import_log.processed_batches_count == 2

    import_log.status = 'IN_PROGRESS'
    import_log.save()

    mock.side_effect = Exception('Something went wrong')
    posted_cost_types, is_errored = post_dependent_cost_code(import_log, dependent_field_setting, platform, {'workspace_id': 1})

    assert import_log.status == 'PARTIALLY_FAILED'

    import_log.status = 'IN_PROGRESS'
    import_log.save()

    mocker.patch('apps.sage_intacct.dependent_fields.sync_sage_intacct_attributes', side_effect=Exception('Something went wrong'))
    post_dependent_cost_code(import_log, dependent_field_setting, platform, {'workspace_id': 1})

    assert import_log.status == 'PARTIALLY_FAILED'


def test_post_dependent_expense_field_values(db, mocker, create_cost_type, create_dependent_field_setting):
    """
    Test post_dependent_expense_field_values
    """
    workspace_id = 1
    mock = mocker.patch(
        'fyle.platform.apis.v1.admin.DependentExpenseFieldValues.bulk_post_dependent_expense_field_values',
        return_value=None
    )

    cost_code_import_log = ImportLog.update_or_create_in_progress_import_log(attribute_type='COST_CODE', workspace_id=workspace_id)
    cost_type_import_log = ImportLog.update_or_create_in_progress_import_log(attribute_type='COST_TYPE', workspace_id=workspace_id)
    ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT', value='pro').update(active=True)

    current_datetime = datetime.now()
    post_dependent_expense_field_values(workspace_id, create_dependent_field_setting, cost_code_import_log=cost_code_import_log, cost_type_import_log=cost_type_import_log)
    assert DependentFieldSetting.objects.get(id=create_dependent_field_setting.id).last_successful_import_at != current_datetime

    # There should be 2 post calls, 1 for cost_type and 1 for cost_code
    assert mock.call_count == 2

    cost_code_import_log.status = 'IN_PROGRESS'
    cost_code_import_log.save()
    cost_type_import_log.status = 'IN_PROGRESS'
    cost_type_import_log.save()

    create_dependent_field_setting.last_successful_import_at = current_datetime
    create_dependent_field_setting.save()
    post_dependent_expense_field_values(workspace_id, create_dependent_field_setting, cost_code_import_log=cost_code_import_log, cost_type_import_log=cost_type_import_log)

    assert mock.call_count == 3
    assert cost_code_import_log.status == 'COMPLETE'
    assert cost_type_import_log.status == 'COMPLETE'
    assert DependentFieldSetting.objects.get(id=create_dependent_field_setting.id).last_successful_import_at >= datetime.now(timezone.utc) - timedelta(minutes=1)


def test_import_dependent_fields_to_fyle(db, mocker, create_cost_type, create_dependent_field_setting):
    """
    Test import_dependent_fields_to_fyle
    """
    workspace_id = 1
    with mock.patch('fyle_integrations_platform_connector.PlatformConnector') as mock_call:
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

        cost_code_import_log = ImportLog.objects.filter(attribute_type='COST_CODE', workspace_id=workspace_id).first()
        assert cost_code_import_log.status == 'FAILED'
        assert cost_code_import_log.error_log == 'Sage Intacct SDK Error'

        cost_type_import_log = ImportLog.objects.filter(attribute_type='COST_TYPE', workspace_id=workspace_id).first()
        assert cost_type_import_log.status == 'FAILED'
        assert cost_type_import_log.error_log == 'Sage Intacct SDK Error'


def test_import_dependent_fields_to_fyle_generic_exception(db, mocker, create_cost_type, create_dependent_field_setting):
    """
    Test import_dependent_fields_to_fyle with generic exception to cover traceback.format_exc()
    """
    workspace_id = 1

    mocker.patch('apps.sage_intacct.dependent_fields.connect_to_platform', return_value=mocker.MagicMock())
    mocker.patch('apps.sage_intacct.dependent_fields.sync_sage_intacct_attributes', side_effect=Exception('Unexpected error'))

    import_dependent_fields_to_fyle(workspace_id)

    cost_code_import_log = ImportLog.objects.filter(attribute_type='COST_CODE', workspace_id=workspace_id).first()
    assert cost_code_import_log.status == 'FAILED'
    assert 'Unexpected error' in cost_code_import_log.error_log

    cost_type_import_log = ImportLog.objects.filter(attribute_type='COST_TYPE', workspace_id=workspace_id).first()
    assert cost_type_import_log.status == 'FAILED'
    assert 'Unexpected error' in cost_type_import_log.error_log


def test_construct_custom_field_placeholder():
    """
    Test construct_custom_field_placeholder
    """
    # Test case 1: Both source_placeholder and placeholder are None, fyle_attribute is provided
    new_placeholder = construct_custom_field_placeholder(None, "PROJECT_CUSTOM", None)
    assert new_placeholder == "Select PROJECT_CUSTOM"

    # Test case 2: source_placeholder is None, placeholder is not None
    existing_attribute = {"placeholder": "Existing Placeholder"}
    new_placeholder = construct_custom_field_placeholder(None, "PROJECT_CUSTOM", existing_attribute)
    assert new_placeholder == "Existing Placeholder"

    # Test case 3: source_placeholder is not None, placeholder is None
    new_placeholder = construct_custom_field_placeholder("Source Placeholder", "PROJECT_CUSTOM", None)
    assert new_placeholder == "Source Placeholder"

    # Test case 4: Both source_placeholder and placeholder are not None
    existing_attribute = {"placeholder": "Existing Placeholder"}
    new_placeholder = construct_custom_field_placeholder("Source Placeholder", "PROJECT_CUSTOM", existing_attribute)
    assert new_placeholder == "Source Placeholder"

    # Test case 5: Neither source_placeholder nor placeholder nor fyle_attribute are provided
    new_placeholder = construct_custom_field_placeholder(None, None, None)
    assert new_placeholder == 'Select None'

    # Test case 6: source_placeholder is provided, placeholder is None, and fyle_attribute is provided
    new_placeholder = construct_custom_field_placeholder("Source Placeholder", "PROJECT_CUSTOM", None)
    assert new_placeholder == "Source Placeholder"


def test_reset_flag_and_disable_cost_type_field(db, mocker, create_cost_type, create_dependent_field_setting):
    """
    Test reset_flag_and_disable_cost_type_field
    """
    workspace_id = 1
    mocker.patch(
        'fyle_integrations_platform_connector.PlatformConnector',
        return_value=mock.MagicMock()
    )

    create_dep_field = mocker.patch('apps.sage_intacct.dependent_fields.create_dependent_custom_field_in_fyle')

    # When reset flag is True and cost type is not imported
    DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(is_cost_type_import_enabled=True)
    reset_flag_and_disable_cost_type_field(workspace_id, True)

    assert create_dep_field.call_count == 1
    assert create_dep_field.called_with(workspace_id, mocker.ANY, mocker.ANY, mocker.ANY, mocker.ANY, mocker.ANY, True)

    # When reset flag is True and cost type is not imported
    DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(is_cost_type_import_enabled=False)

    reset_flag_and_disable_cost_type_field(workspace_id, True)
    assert create_dep_field.call_count == 2
    assert create_dep_field.called_with(workspace_id, mocker.ANY, mocker.ANY, mocker.ANY, mocker.ANY, mocker.ANY, False)

    # When reset flag is False and cost type is not imported
    DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(is_cost_type_import_enabled=True)

    reset_flag_and_disable_cost_type_field(workspace_id, False)

    assert create_dep_field.call_count == 2
    assert create_dep_field.not_called()

    # When reset flag is False and cost type is imported
    DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(is_cost_type_import_enabled=False)

    reset_flag_and_disable_cost_type_field(workspace_id, False)

    assert create_dep_field.call_count == 2
    assert create_dep_field.not_called()


def test_post_dependent_cost_code_standalone(db, mocker, add_project_mappings, create_dependent_field_setting):
    """
    Test post_dependent_cost_code standalone
    """
    workspace_id = 1
    platform = mocker.patch(
        'fyle_integrations_platform_connector.PlatformConnector',
        return_value=mocker.MagicMock()
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.DependentExpenseFieldValues.bulk_post_dependent_expense_field_values',
        return_value=None
    )

    CostCode.objects.create(
        workspace_id=workspace_id,
        task_name='cost code 123',
        task_id='1',
        project_id='10065',
        project_name='CRE Platform'
    )

    DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(is_cost_type_import_enabled=False, last_successful_import_at=None)
    dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=workspace_id).first()

    cost_code_import_log = ImportLog.update_or_create_in_progress_import_log(attribute_type='COST_CODE', workspace_id=workspace_id)

    post_dependent_cost_code_standalone(workspace_id, dependent_field_setting, platform, cost_code_import_log)

    cost_code_import_log.refresh_from_db()
    assert cost_code_import_log.status == 'COMPLETE'


def test_disable_and_post_cost_code_from_cost_code_table(db, mocker, add_project_mappings, create_dependent_field_setting):
    """
    Test disable_and_post_cost_code_from_cost_code_table
    """
    workspace_id = 1
    platform = mocker.patch(
        'fyle_integrations_platform_connector.PlatformConnector',
        return_value=mocker.MagicMock()
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.DependentExpenseFieldValues.bulk_post_dependent_expense_field_values',
        return_value=None
    )

    cost_codes_to_disable = {
        '10065': {
            'value': 'CRE Platform',
            'updated_value': 'CRE Platform',
            'code': '10065',
            'updated_code': '10066'
        }
    }

    CostCode.objects.create(
        workspace_id=workspace_id,
        task_name='cost code 123',
        task_id='1',
        project_id='10065',
        project_name='CRE Platform'
    )

    DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(is_cost_type_import_enabled=False)
    dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=workspace_id).first()

    disable_and_post_cost_code_from_cost_code_table(workspace_id, cost_codes_to_disable, platform, dependent_field_setting)

    cost_code_attribute = CostCode.objects.filter(workspace_id=workspace_id, task_name='cost code 123').first()

    assert cost_code_attribute.project_id == '10066'
    assert cost_code_attribute.project_name == 'CRE Platform'


def test_remove_duplicate_payload_entries():
    """
    Test remove_duplicate_payload_entries
    """
    payload = data["cost_type_payload_duplicate"]

    unique_payload = remove_duplicate_payload_entries(payload)
    assert len(unique_payload) == 2
    assert dict_compare_keys(unique_payload, [{'parent_expense_field_id': 379240, 'expense_field_id': 379241, 'parent_expense_field_value': 'Administrative', 'is_enabled': True, 'expense_field_value': 'Contingency Costs'}, {'parent_expense_field_id': 379240, 'expense_field_id': 379241, 'expense_field_value': 'Bond', 'parent_expense_field_value': 'Administrative', 'is_enabled': True}]) == [], "Payload is not unique"
