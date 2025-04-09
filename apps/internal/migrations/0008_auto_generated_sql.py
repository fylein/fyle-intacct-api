# Generated by Django
from django.db import migrations
from apps.internal.helpers import safe_run_sql
sql_files = [
    'fyle-integrations-db-migrations/intacct/views/alerts/huge_export_failing_orgs_view.sql',
    'fyle-integrations-db-migrations/intacct/views/alerts/huge_export_volume_view.sql'
]
class Migration(migrations.Migration):
    dependencies = [('internal', '0007_auto_generated_sql')]
    operations = safe_run_sql(sql_files)
