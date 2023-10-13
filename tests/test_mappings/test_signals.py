from asyncio.log import logger
from datetime import datetime, timedelta, timezone
import pytest
import json
from unittest import mock
from django.db import transaction
from django_q.models import Schedule
from fyle_accounting_mappings.models import (
    MappingSetting,
    Mapping,
    ExpenseAttribute,
    EmployeeMapping,
    CategoryMapping,
    DestinationAttribute
)
from apps.tasks.models import Error
from apps.workspaces.models import Configuration, Workspace
from apps.mappings.models import LocationEntityMapping, ImportLog
from fyle.platform.exceptions import WrongParamsError
from ..test_fyle.fixtures import data as fyle_data



def test_pre_save_category_mappings(test_connection, mocker, db):

    category_mapping, _ = CategoryMapping.objects.update_or_create(
       source_category_id=106,
       destination_expense_head_id=926,
       workspace_id=1
    )

    assert category_mapping.destination_expense_head_id == 926
    assert category_mapping.destination_account_id == 796

    category_mapping.destination_expense_head_id = None
    category_mapping.save()
    
    category_mapping, _ = CategoryMapping.objects.update_or_create(
        source_category_id=106,
        destination_account_id=796,
        workspace_id=1
    )
    
    assert category_mapping.destination_account_id == 796
    assert category_mapping.destination_expense_head_id == None
    

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

def test_run_post_location_entity_mappings(db, mocker, test_connection):

    workspace = Workspace.objects.get(id=1)
    assert workspace.onboarding_state == 'IMPORT_SETTINGS'
    LocationEntityMapping.objects.update_or_create(
        workspace_id=1,
        defaults={
            "country_name": "USA"
        }
    )
    workspace = Workspace.objects.get(id=1)
    assert workspace.onboarding_state == 'EXPORT_SETTINGS'

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

    MappingSetting.objects.all().delete()
    Schedule.objects.all().delete()

    mapping_setting = MappingSetting(
        source_field='PROJECT',
        destination_field='PROJECT',
        workspace_id=workspace_id,
        import_to_fyle=True,
        is_custom=False
    )
    mapping_setting.save()

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.imports.queues.chain_import_fields_to_fyle'
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
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.imports.queues.chain_import_fields_to_fyle'
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
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.imports.queues.chain_import_fields_to_fyle'
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
    custom_mappings = Mapping.objects.filter(workspace_id=workspace_id, source_type='CUSTOM_INTENTS').count()
    assert custom_mappings == 0

    try:
        mapping_setting = MappingSetting.objects.create(
            source_field='CUSTOM_INTENTS',
            destination_field='CUSTOM_INTENTS',
            workspace_id=workspace_id,
            import_to_fyle=True,
            is_custom=True
        )
    except:
        logger.info('Duplicate custom field name')

    custom_mappings = Mapping.objects.last()
    
    custom_mappings = Mapping.objects.filter(workspace_id=workspace_id, source_type='CUSTOM_INTENTS').count()
    assert custom_mappings == 0

    import_log = ImportLog.objects.filter(
        workspace_id=1,
        attribute_type='CUSTOM_INTENTS'
    ).first()

    assert import_log.status == 'COMPLETE'

    time_difference = datetime.now() - timedelta(hours=2)
    offset_aware_time_difference = time_difference.replace(tzinfo=timezone.utc)
    import_log.last_successful_run_at = offset_aware_time_difference
    import_log.save()

    # case where error will occur but we reach the case where there are no destination attributes 
    # so we mark the import as complete
    with mock.patch('fyle_integrations_platform_connector.apis.ExpenseCustomFields.post') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response=json.dumps({'code': 400, 'message': 'duplicate key value violates unique constraint '
        '"idx_expense_fields_org_id_field_name_is_enabled_is_custom"', 'Detail': 'Invalid parametrs'}))

        mapping_setting = MappingSetting(
            source_field='CUSTOM_INTENTS',
            destination_field='CUSTOM_INTENTS',
            workspace_id=workspace_id,
            import_to_fyle=True,
            is_custom=True
        )

        try:
            with transaction.atomic():
                mapping_setting.save()
        except:
            logger.info('Duplicate custom field name')

        import_log = ImportLog.objects.get(
            workspace_id=1,
            attribute_type='CUSTOM_INTENTS'
        )

        assert import_log.status == 'COMPLETE'
        assert import_log.error_log == []
        assert import_log.total_batches_count == 0
        assert import_log.processed_batches_count == 0

    # case where error will occur but we reach the case where there are destination attributes 
    # so we mark the import as FAILED
    with mock.patch('fyle_integrations_platform_connector.apis.ExpenseCustomFields.post') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response=json.dumps({'code': 400, 'message': 'duplicate key value violates unique constraint '
        '"idx_expense_fields_org_id_field_name_is_enabled_is_custom"', 'Detail': 'Invalid parametrs'}))

        mapping_setting = MappingSetting(
            source_field='CUSTOM_INTENTS',
            destination_field='CUSTOM_INTENTS',
            workspace_id=workspace_id,
            import_to_fyle=True,
            is_custom=True
        )

        DestinationAttribute.objects.create(
            attribute_type='CUSTOM_INTENTS',
            display_name='Custom Intents',
            value='Labhvam',
            destination_id='890812',
            workspace_id=1
        )

        try:
            mapping_setting.save()
        except:
            logger.info('Duplicate custom field name')

        import_log = ImportLog.objects.get(
            workspace_id=1,
            attribute_type='CUSTOM_INTENTS'
        )

        # set import_log status to FAILED
        assert import_log.status == 'FAILED'