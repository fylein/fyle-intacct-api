from datetime import datetime
from django_q.models import Schedule


def schedule_dependent_field_imports(workspace_id: int, is_import_enabled: bool):
    if is_import_enabled:
        Schedule.objects.update_or_create(
            func='apps.mappings.tasks.import_dependent_fields_to_fyle',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': datetime.now()
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.import_dependent_fields_to_fyle',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()
