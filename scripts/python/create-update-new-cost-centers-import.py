from django.db import transaction
from datetime import datetime
from django_q.models import Schedule
from apps.workspaces.models import Configuration
from fyle_accounting_mappings.models import MappingSetting
existing_import_enabled_schedules = Schedule.objects.filter(
    func__in=['apps.mappings.tasks.auto_create_cost_center_mappings']
).values('args')
try:
    with transaction.atomic():
        for schedule in existing_import_enabled_schedules:
            mapping_setting = MappingSetting.objects.filter(source_field='COST_CENTER', workspace_id=schedule['args'], import_to_fyle=True).first()
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
        categories = Configuration.objects.filter(import_categories=True).values_list('workspace_id', flat=True)
        project = MappingSetting.objects.filter(source_field='PROJECT', import_to_fyle=True).values_list('workspace_id', flat=True)
        cost_center = MappingSetting.objects.filter(source_field='COST_CENTER', import_to_fyle=True).values_list('workspace_id', flat=True)
        unique_states = list(set(categories) | set(project) | set(cost_center))
        tot_count = len(unique_states)
        schedule_count = Schedule.objects.filter(func='apps.mappings.imports.queues.chain_import_fields_to_fyle').count()
        #make the sanity check a bit more clear
        print("tot_count: {}".format(tot_count))
        print("schedule_count: {}".format(schedule_count))
        raise Exception("This is a sanity check")
except Exception as e:
    print(e)
