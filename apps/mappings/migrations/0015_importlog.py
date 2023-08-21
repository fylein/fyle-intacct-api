# Generated by Django 3.1.14 on 2023-07-19 10:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0030_lastexportdetail'),
        ('mappings', '0014_auto_20230531_1248'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportLog',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('attribute_type', models.CharField(help_text='Attribute type', max_length=150)),
                ('status', models.CharField(choices=[('FATAL', 'FATAL'), ('COMPLETE', 'COMPLETE'), ('IN_PROGRESS', 'IN_PROGRESS'), ('FAILED', 'FAILED')], help_text='Status', max_length=255, null=True)),
                ('error_log', models.JSONField(default=list, help_text='Error Log')),
                ('total_batches_count', models.IntegerField(default=0, help_text='Queued batches')),
                ('processed_batches_count', models.IntegerField(default=0, help_text='Processed batches')),
                ('last_successful_run_at', models.DateTimeField(help_text='Last successful run', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace')),
            ],
            options={
                'db_table': 'import_logs',
                'unique_together': {('workspace', 'attribute_type')},
            },
        ),
    ]