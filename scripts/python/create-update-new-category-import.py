from django.db import transaction
from datetime import datetime
from django_q.models import Schedule
from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import MappingSetting
existing_import_enabled_schedules = Schedule.objects.filter(
    func__in=['apps.mappings.tasks.auto_import_and_map_fyle_fields']
).values('args')
try:
    with transaction.atomic():
        for schedule in existing_import_enabled_schedules:
            configuration = Configuration.objects.get(workspace_id=schedule['args'])
            if configuration.import_categories:
                Schedule.objects.update_or_create(
                    func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
                    args=schedule['args'],
                    defaults={
                        'schedule_type': Schedule.MINUTES,
                        'minutes':24 * 60,
                        'next_run':datetime.now()
                    }
                )
        categories_count = Configuration.objects.filter(import_categories=True).count()
        schedule_count = Schedule.objects.filter(func='apps.mappings.imports.queues.chain_import_fields_to_fyle').count()
        project_count = MappingSetting.objects.filter(source_field='PROJECT', import_to_fyle=True).count()
        #make the sanity check a bit more clear
        print("categoreis_count: {}".format(categories_count))
        print("project_count: {}".format(project_count))
        print("schedule_count: {}".format(schedule_count))
        raise Exception("This is a sanity check")
except Exception as e:
    print(e)