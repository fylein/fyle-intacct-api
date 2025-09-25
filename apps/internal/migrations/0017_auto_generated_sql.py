from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [('internal', '0015_auto_generated_sql')]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Insert new merged schedule per workspace
                INSERT INTO django_q_schedule (func, args, schedule_type, minutes, next_run, repeats)
                SELECT
                    'apps.sage_intacct.queues.trigger_sync_payments',
                    args,
                    'I',
                    '1440',
                    MAX(next_run) AS next_run,           -- next_run is max of old schedules
                    -1
                FROM django_q_schedule
                WHERE func IN (
                    'apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
                    'apps.sage_intacct.tasks.process_fyle_reimbursements',
                    'apps.sage_intacct.tasks.check_sage_intacct_object_status',
                    'apps.sage_intacct.tasks.create_ap_payment'
                )
                GROUP BY args
                HAVING NOT EXISTS (
                    SELECT 1
                    FROM django_q_schedule dqs2
                    WHERE dqs2.func = 'apps.sage_intacct.queues.trigger_sync_payments'
                    AND dqs2.args = django_q_schedule.args
                );

                -- Delete old schedules
                DELETE FROM django_q_schedule
                WHERE func IN (
                    'apps.sage_intacct.tasks.create_sage_intacct_reimbursement',
                    'apps.sage_intacct.tasks.process_fyle_reimbursements',
                    'apps.sage_intacct.tasks.check_sage_intacct_object_status',
                    'apps.sage_intacct.tasks.create_ap_payment'
                );
            """,
            reverse_sql="""
                -- Delete the merged schedule on rollback
                DELETE FROM django_q_schedule
                WHERE func = 'apps.sage_intacct.queues.trigger_sync_payments';
            """
        )
    ]
