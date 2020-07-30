from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('workspaces', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneralMapping',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('default_location_name', models.CharField(max_length=255, \
                    help_text='Default location name', null=True)),
                ('default_location_id', models.CharField(max_length=255, help_text='Default location ID', null=True)),
                ('default_department_name', models.CharField(max_length=255, \
                    help_text='Default department name', null=True)),
                ('default_department_id', models.CharField(max_length=255, \
                    help_text='Default department ID', null=True)),
                ('default_project_name', models.CharField(max_length=255, help_text='Default project name', null=True)),
                ('default_project_id', models.CharField(max_length=255, help_text='Default project ID', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace model', \
                    on_delete=django.db.models.deletion.PROTECT, to='workspaces.Workspace')),
            ],
        ),
        migrations.AlterModelTable(
            name='GeneralMapping',
            table='general_mappings',
        ),
    ]
