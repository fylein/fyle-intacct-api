# -- if only project mapping then replace no import_vendors_as_merchants and import_categories and no dependant field
# -- if both projects and import_categories or auto_create_vendors or dependant_fields then insert

from django.db import transaction
from datetime import datetime
from django_q.models import Schedule
from apps.workspaces.models import Configuration
from apps.fyle.models import DependentFieldSetting
from fyle_accounting_mappings.models import MappingSetting

# TODO: take a backup of the schedules table before running this script

# grouping by workspace_id
existing_import_enabled_schedules = Schedule.objects.filter(
    func__in=['apps.mappings.tasks.auto_import_and_map_fyle_fields']
).values('args')

try:
    # Create/update new schedules in a transaction block
    with transaction.atomic():
        for schedule in existing_import_enabled_schedules:
            configuration = Configuration.objects.get(workspace_id=schedule['args'])
            dependent_field_settings = DependentFieldSetting.objects.filter(workspace_id=schedule['args'])
            mapping_setting = MappingSetting.objects.filter(source_field='PROJECT', workspace_id=schedule['args'], import_to_fyle=True).first()

            if not configuration.import_categories and not configuration.import_vendors_as_merchants \
                and (not dependent_field_settings or (dependent_field_settings and not dependent_field_settings.is_import_enabled))\
                and mapping_setting:
                #replace the schedule
                Schedule.objects.filter(
                    func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
                    args=schedule['args']
                ).first().update(func='apps.mappings.imports.queues.chain_import_fields_to_fyle')

            if configuration.import_categories or configuration.import_vendors_as_merchants \
                or (dependent_field_settings and dependent_field_settings.is_import_enabled)\
                and mapping_setting:
                #insert the schedule
                Schedule.objects.create(
                    func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
                    args=schedule['args'],
                    schedule_type= Schedule.MINUTES,
                    minutes=24 * 60,
                    next_run=datetime.now()
                )

except Exception as e:
    print(e)
