from django_q.models import Schedule
from fyle_accounting_mappings.models import MappingSetting
from apps.workspaces.models import Configuration
from apps.mappings.imports.schedules import schedule_or_delete_fyle_import_tasks


def test_schedule_projects_creation(db):
    workspace_id = 1

    # Test schedule projects creation
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.import_categories = True
    configuration.import_projects = True
    configuration.import_vendors_as_merchants = True
    configuration.import_tax_codes = True
    configuration.save()

    mapping_setting = MappingSetting.objects.filter(workspace_id=workspace_id, source_field='PROJECT', destination_field='PROJECT', import_to_fyle=True ).first()

    schedule_or_delete_fyle_import_tasks(configuration, mapping_setting)

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()
    
    assert schedule.func == 'apps.mappings.imports.queues.chain_import_fields_to_fyle'

    # Test delete schedule projects creation
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.import_categories = False
    configuration.import_vendors_as_merchants = False
    configuration.import_projects = False
    configuration.import_tax_codes = False
    configuration.save()

    mapping_setting = MappingSetting.objects.filter(workspace_id=workspace_id, source_field='PROJECT', destination_field='PROJECT', import_to_fyle=True ).first()
    mapping_setting.import_to_fyle = False
    mapping_setting.save()

    schedule_or_delete_fyle_import_tasks(configuration, mapping_setting)

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None

    # Test schedule categories creation adding the new schedule and not adding the old one
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.import_categories = True
    configuration.import_vendors_as_merchants = False
    configuration.import_projects = False
    configuration.import_tax_codes = False
    configuration.save()

    schedule_or_delete_fyle_import_tasks(configuration, mapping_setting)

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.imports.queues.chain_import_fields_to_fyle'

    schedule = Schedule.objects.filter(
        func='apps.mappings.auto_import_and_map_fyle_fields',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None
