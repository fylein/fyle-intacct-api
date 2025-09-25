from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [('internal', '0015_auto_generated_sql')]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Insert new merged schedule per workspace
                INSERT INTO django_q_schedule (func, args, schedule_type, minutes, next_run, repeats)
                SELECT
                    'apps.mappings.tasks.auto_map_accounting_fields',
                    args,
                    'I',
                    '1440',
                    MAX(next_run) AS next_run,           -- next_run is max of old schedules
                    -1
                FROM django_q_schedule
                WHERE func IN (
                    'apps.mappings.tasks.async_auto_map_employees',
                    'apps.mappings.tasks.async_auto_map_charge_card_account'
                )
                GROUP BY args
                HAVING NOT EXISTS (
                    SELECT 1
                    FROM django_q_schedule dqs2
                    WHERE dqs2.func = 'apps.mappings.tasks.auto_map_accounting_fields'
                    AND dqs2.args = django_q_schedule.args
                );

                -- Delete old schedules
                DELETE FROM django_q_schedule
                WHERE func IN (
                    'apps.mappings.tasks.async_auto_map_employees',
                    'apps.mappings.tasks.async_auto_map_charge_card_account'
                );
            """,
            reverse_sql="""
                -- Delete the merged schedule on rollback
                DELETE FROM django_q_schedule
                WHERE func = 'apps.mappings.tasks.auto_map_accounting_fields';
            """
        )
    ]
