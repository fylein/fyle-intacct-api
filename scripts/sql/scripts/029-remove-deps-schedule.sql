rollback;
begin;

delete from django_q_schedule where func = 'apps.mappings.tasks.auto_import_and_map_fyle_fields';