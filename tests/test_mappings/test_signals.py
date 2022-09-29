from asyncio.log import logger
import json
from unittest import mock
from django_q.models import Schedule
from fyle_accounting_mappings.models import MappingSetting, Mapping
from apps.workspaces.models import Workspace
from fyle.platform.exceptions import WrongParamsError
from ..test_fyle.fixtures import data as fyle_data


def test_run_post_mapping_settings_triggers(db, mocker, test_connection):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.ExpenseFields.list_all',
        return_value=fyle_data['get_all_expense_fields']
    )

    workspace_id = 1

    mapping_setting = MappingSetting.objects.filter(source_field='PROJECT', destination_field='PROJECT').first()
    mapping_setting.delete()

    mapping_setting = MappingSetting(
        source_field='PROJECT',
        destination_field='PROJECT',
        workspace_id=workspace_id,
        import_to_fyle=True,
        is_custom=False
    )

    mapping_setting.save()

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.auto_create_project_mappings',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.auto_create_project_mappings'
    assert schedule.args == '1'

    mapping_setting = MappingSetting(
        source_field='COST_CENTER',
        destination_field='CLASS',
        workspace_id=workspace_id,
        import_to_fyle=True,
        is_custom=False
    )
    mapping_setting.save()

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.auto_create_cost_center_mappings',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.auto_create_cost_center_mappings'
    assert schedule.args == '1'

    mapping_setting = MappingSetting(
        source_field='SAMPLEs',
        destination_field='SAMPLEs',
        workspace_id=workspace_id,
        import_to_fyle=True,
        is_custom=True
    )
    mapping_setting.save()

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.async_auto_create_custom_field_mappings',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.async_auto_create_custom_field_mappings'
    assert schedule.args == '1'


def test_run_pre_mapping_settings_triggers(db, mocker, test_connection):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.ExpenseFields.list_all',
        return_value=fyle_data['get_all_expense_fields']
    )

    workspace_id = 1

    custom_mappings = Mapping.objects.filter(workspace_id=workspace_id, source_type='CUSTOM_INTENTs').count()
    assert custom_mappings == 0

    with mock.patch('apps.mappings.signals.upload_attributes_to_fyle') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response=json.dumps({'code': 400, 'message': 'duplicate key value violates unique constraint '
        '"idx_expense_fields_org_id_field_name_is_enabled_is_custom"', 'Detail': 'Invalid parametrs'}))
        mapping_setting = MappingSetting(
            source_field='CUSTOM_INTENTs',
            destination_field='CUSTOM_INTENTs',
            workspace_id=workspace_id,
            import_to_fyle=True,
            is_custom=True
        )
        try:
            mapping_setting.save()
        except:
            logger.info('Duplicate custom field name')
    custom_mappings = Mapping.objects.last()
    
    custom_mappings = Mapping.objects.filter(workspace_id=workspace_id, source_type='CUSTOM_INTENTs').count()
    assert custom_mappings == 0
