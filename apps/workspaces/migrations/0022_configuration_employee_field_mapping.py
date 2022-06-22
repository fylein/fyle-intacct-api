# Generated by Django 3.1.14 on 2022-06-22 04:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0021_configuration_import_vendors_as_merchants'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='employee_field_mapping',
            field=models.CharField(choices=[('EMPLOYEE', 'EMPLOYEE'), ('VENDOR', 'VENDOR')], help_text='Employee field mapping', max_length=50, null=True),
        ),
    ]
