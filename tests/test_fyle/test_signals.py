from django_q.models import Schedule

from apps.fyle.models import DependentFieldSetting
from apps.fyle.signals import run_post_save_dependent_field_settings_triggers

def test_run_post_save_dependent_field_settings_triggers(mocker, db):
    dependent_field = DependentFieldSetting(
        workspace_id=1,
        is_import_enabled=True,
        project_field_id=123,
        cost_code_field_name='Cost Code',
        cost_code_field_id=0,
        cost_type_field_name='Cost Type',
        cost_type_field_id=789
    )
    run_post_save_dependent_field_settings_triggers(None, dependent_field)

    assert Schedule.objects.filter(func='apps.sage_intacct.dependent_fields.import_dependent_fields_to_fyle', args='1').exists()
