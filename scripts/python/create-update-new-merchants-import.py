from django.db import transaction
from datetime import datetime
from django_q.models import Schedule
from apps.workspaces.models import Configuration

existing_import_enabled_schedules = Schedule.objects.filter(
    func__in=['apps.mappings.tasks.auto_import_and_map_fyle_fields']
).values('args')
try:
    with transaction.atomic():
        for schedule in existing_import_enabled_schedules:
            configuration = Configuration.objects.filter(workspace_id=schedule['args'], import_vendors_as_merchants=True ).first()
            if configuration:
                Schedule.objects.update_or_create(
                    func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
                    args=schedule['args'],
                    defaults={
                        'schedule_type': Schedule.MINUTES,
                        'minutes':24 * 60,
                        'next_run':datetime.now()
                    }
                )
        raise Exception("This is a sanity check")
except Exception as e:
    print(e)
