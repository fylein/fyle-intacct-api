from django.db import transaction
from datetime import datetime
from django_q.models import Schedule
from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import MappingSetting
existing_import_enabled_schedules = Schedule.objects.filter(
    func__in=['apps.mappings.tasks.auto_create_tax_codes_mappings']
).values('args')
try:
    with transaction.atomic():
        for schedule in existing_import_enabled_schedules:
            mapping_setting = MappingSetting.objects.filter(workspace_id=schedule['args'], import_to_fyle=True).first()
            if mapping_setting:
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

# Delete all the schedules for tax-groups-import via SQL after running this script
# rollback;
# begin;
# delete from django_q_schedule where func = 'apps.mappings.tasks.auto_create_tax_codes_mappings';
# commit;
