# Generated by Django 3.1.14 on 2023-06-07 09:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0025_auto_20230417_1124'),
        ('sage_intacct', '0019_auto_20230307_1746'),
    ]

    operations = [
        migrations.CreateModel(
            name='CostTypes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_number', models.CharField(help_text='Sage Intacct Record No', max_length=255)),
                ('project_key', models.CharField(help_text='Sage Intacct Project Key', max_length=255)),
                ('project_id', models.CharField(help_text='Sage Intacct Project ID', max_length=255)),
                ('project_name', models.CharField(help_text='Sage Intacct Project Name', max_length=255)),
                ('task_key', models.CharField(help_text='Sage Intacct Task Key', max_length=255)),
                ('task_id', models.CharField(help_text='Sage Intacct Task ID', max_length=255)),
                ('status', models.CharField(help_text='Sage Intacct Status', max_length=255, null=True)),
                ('task_name', models.CharField(help_text='Sage Intacct Task Name', max_length=255)),
                ('cost_type_id', models.CharField(help_text='Sage Intacct Cost Type ID', max_length=255)),
                ('name', models.CharField(help_text='Sage Intacct Cost Type Name', max_length=255)),
                ('when_created', models.CharField(help_text='Sage Intacct When Created', max_length=255, null=True)),
                ('when_modified', models.CharField(help_text='Sage Intacct When Modified', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace')),
            ],
            options={
                'db_table': 'cost_types',
                'unique_together': {('record_number', 'workspace_id')},
            },
        ),
    ]
