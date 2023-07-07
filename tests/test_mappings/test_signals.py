from asyncio.log import logger
import pytest
import json
from unittest import mock
from django_q.models import Schedule
from fyle_accounting_mappings.models import MappingSetting, Mapping, ExpenseAttribute, EmployeeMapping, CategoryMapping
from apps.workspaces.models import Configuration
from apps.tasks.models import Error
from fyle.platform.exceptions import WrongParamsError
from ..test_fyle.fixtures import data as fyle_data


def test_resolve_post_mapping_errors(test_connection, mocker, db):
    tax_group = ExpenseAttribute.objects.filter(
        value='GST on capital @0%',
        workspace_id=1,
        attribute_type='TAX_GROUP'
    ).first()

    Error.objects.update_or_create(
        workspace_id=1,
        expense_attribute=tax_group,
        defaults={
            'type': 'TAX_GROUP_MAPPING',
            'error_title': tax_group.value,
            'error_detail': 'Tax group mapping is missing',
            'is_resolved': False
        }
    )

    mapping = Mapping(
        source_type='TAX_GROUP',
        destination_type='TAX_DETAIL',
        # source__value=source_value,
        source_id=2775,
        destination_id=544,
        workspace_id=1
    )
    mapping.save()
    error = Error.objects.filter(expense_attribute_id=mapping.source_id).first()

    assert error.is_resolved == True


@pytest.mark.django_db()
def test_resolve_post_employees_mapping_errors(test_connection):
    source_employee = ExpenseAttribute.objects.filter(
        value='user2@fyleforgotham.in',
        workspace_id=1,
        attribute_type='EMPLOYEE'
    ).first()

    Error.objects.update_or_create(
        workspace_id=1,
        expense_attribute=source_employee,
        defaults={
            'type': 'EMPLOYEE_MAPPING',
            'error_title': source_employee.value,
            'error_detail': 'Employee mapping is missing',
            'is_resolved': False
        }
    )
    employee_mapping, _ = EmployeeMapping.objects.update_or_create(
       source_employee_id=3,
       destination_employee_id=719,
       workspace_id=1
    )

    error = Error.objects.filter(expense_attribute_id=employee_mapping.source_employee_id).first()

    assert error.is_resolved == True


@pytest.mark.django_db()
def test_resolve_post_category_mapping_errors(test_connection):
    source_category = ExpenseAttribute.objects.filter(
        id=106,
        workspace_id=1,
        attribute_type='CATEGORY'
    ).first()

    Error.objects.update_or_create(
        workspace_id=1,
        expense_attribute=source_category,
        defaults={
            'type': 'CATEGORY_MAPPING',
            'error_title': source_category.value,
            'error_detail': 'Category mapping is missing',
            'is_resolved': False
        }
    )
    category_mapping, _ = CategoryMapping.objects.update_or_create(
       source_category_id=106,
       destination_account_id=791,
       destination_expense_head_id=791,
       workspace_id=1
    )

    error = Error.objects.filter(expense_attribute_id=category_mapping.source_category_id).first()
    assert error.is_resolved == True


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


    mapping_setting = MappingSetting.objects.filter(
        source_field='PROJECT',
        workspace_id=workspace_id
    ).delete()
    configuration = Configuration.objects.filter(workspace_id=workspace_id).first()
    configuration.import_categories = False
    configuration.import_vendors_as_merchants = False
    configuration.save()

    mapping_setting = MappingSetting(
        source_field='LOLOOO',
        destination_field='HEHEHE',
        workspace_id=workspace_id,
        import_to_fyle=True,
        is_custom=False
    )
    mapping_setting.save()

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None


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
