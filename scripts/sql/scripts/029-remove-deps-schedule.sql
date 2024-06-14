rollback;
begin;

delete from django_q_schedule where func in (
    'apps.mappings.tasks.auto_import_and_map_fyle_fields',
    'apps.sage_intacct.dependent_fields.import_dependent_fields_to_fyle'
);