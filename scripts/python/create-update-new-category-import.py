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
        categories = Configuration.objects.filter(import_categories=True).values_list('workspace_id', flat=True)
        project = MappingSetting.objects.filter(source_field='PROJECT', import_to_fyle=True).values_list('workspace_id', flat=True)
        unique_workspace_ids = list(set(categories) | set(project))
        total_count = len(unique_workspace_ids)
        schedule_count = Schedule.objects.filter(func='apps.mappings.imports.queues.chain_import_fields_to_fyle').count()
        print("total_count: {}".format(total_count))
        print("schedule_count: {}".format(schedule_count))
        raise Exception("This is a sanity check")
except Exception as e:
    print(e)
