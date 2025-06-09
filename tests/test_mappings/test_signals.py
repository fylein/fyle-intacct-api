import pytest

from unittest import mock
from asyncio.log import logger
from datetime import datetime, timedelta, timezone

from django.db import transaction
from django_q.models import Schedule

from fyle.platform.exceptions import WrongParamsError
from fyle_accounting_mappings.models import (
    MappingSetting,
    Mapping,
    ExpenseAttribute,
    EmployeeMapping,
    CategoryMapping
)

from apps.tasks.models import Error
from apps.workspaces.models import Configuration, Workspace
from apps.mappings.models import LocationEntityMapping
from fyle_integrations_imports.models import ImportLog

from tests.test_fyle.fixtures import data as fyle_data


def test_pre_save_category_mappings(test_connection, mocker, db):
    """
    Test pre save category mappings
    """
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


@pytest.mark.django_db()
def test_resolve_post_employees_mapping_errors(test_connection):
    """
    Test resolve post employees mapping errors
    """
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
    """
    Test resolve post category mapping errors
    """
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
    """
    Test run post location entity mappings
    """
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
    """
    Test run post mapping settings triggers
    """
    # Patch SYNC_METHODS to include 'SAMPLEs' and 'HEHEHE' for this test
    import apps.mappings.constants as mapping_constants
    mapping_constants.SYNC_METHODS['SAMPLEs'] = 'sample_sync_method'
    mapping_constants.SYNC_METHODS['HEHEHE'] = 'hehehe_sync_method'

    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.ExpenseFields.list_all',
        return_value=fyle_data['get_all_expense_fields']
    )

    mocker.patch('apps.fyle.helpers.DimensionDetail.bulk_create_or_update_dimension_details', return_value=None)

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
        func='apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle'
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
        func='apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle'
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
        func='apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle'
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
    """
    Test run pre mapping settings triggers
    """
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )

    mocker.patch(
        'fyle.platform.apis.v1.admin.ExpenseFields.list_all',
        return_value=fyle_data['get_all_expense_fields']
    )

    mocker.patch('apps.fyle.helpers.DimensionDetail.bulk_create_or_update_dimension_details', return_value=None)

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
    except Exception:
        logger.info('Duplicate custom field name')

    custom_mappings = Mapping.objects.last()

    custom_mappings = Mapping.objects.filter(workspace_id=workspace_id, source_type='CUSTOM_INTENTS').count()
    assert custom_mappings == 0

    import_log = ImportLog.objects.filter(
        workspace_id=1,
        attribute_type='CUSTOM_INTENTS'
    ).first()

    assert import_log.status == 'IN_PROGRESS'

    time_difference = datetime.now() - timedelta(hours=2)
    offset_aware_time_difference = time_difference.replace(tzinfo=timezone.utc)
    import_log.last_successful_run_at = offset_aware_time_difference
    import_log.save()

    ImportLog.objects.filter(workspace_id=1, attribute_type='CUSTOM_INTENTS').delete()

    # case where error will occur but we reach the case where there are no destination attributes
    # so we mark the import as complete
    with mock.patch('fyle_integrations_platform_connector.apis.ExpenseCustomFields.post') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response={'code': 400, 'message': 'duplicate key value violates unique constraint '
        '"idx_expense_fields_org_id_field_name_is_enabled_is_custom"', 'Detail': 'Invalid parametrs'})

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
        except Exception:
            logger.info('duplicate key value violates unique constraint')

    with mock.patch('fyle_integrations_platform_connector.apis.ExpenseCustomFields.post') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response={'data': None, 'error': 'InvalidUsage', 'message': 'text_column cannot be added as it exceeds the maximum limit(15) of columns of a single type'})

        mapping_setting = MappingSetting(
            source_field='CUSTOM_INTENTS',
            destination_field='CUSTOM_INTENTS',
            workspace_id=workspace_id,
            import_to_fyle=True,
            is_custom=True
        )

        try:
            mapping_setting.save()
        except Exception:
            logger.info('text_column cannot be added as it exceeds the maximum limit(15) of columns of a single type')

    with mock.patch('fyle_integrations_platform_connector.apis.ExpenseCustomFields.post') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response={'data': None,'error': 'IntegrityError','message': 'The values ("or79Cob97KSh", "text_column15", "1") already exists'})

        mapping_setting = MappingSetting(
            source_field='CUSTOM_INTENTS',
            destination_field='CUSTOM_INTENTS',
            workspace_id=workspace_id,
            import_to_fyle=True,
            is_custom=True
        )

        try:
            mapping_setting.save()
        except Exception:
            logger.info('The values ("or79Cob97KSh", "text_column15", "1") already exists')
