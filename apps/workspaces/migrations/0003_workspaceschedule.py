# Generated by Django 3.0.3 on 2020-11-11 07:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_q', '0009_auto_20171009_0915'),
        ('workspaces', '0002_ccc'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkspaceSchedule',
            fields=[
                ('id', models.AutoField(help_text='Unique Id to identify a schedule', primary_key=True, serialize=False)),
                ('enabled', models.BooleanField(default=False)),
                ('start_datetime', models.DateTimeField(help_text='Datetime for start of schedule', null=True)),
                ('interval_hours', models.IntegerField(null=True)),
                ('schedule', models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='django_q.Schedule')),
                ('workspace', models.OneToOneField(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.Workspace')),
            ],
            options={
                'db_table': 'workspace_schedules',
            },
        ),
    ]
