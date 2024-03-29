# Generated by Django 3.0.3 on 2021-06-03 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mappings', '0005_auto_20210517_1650'),
    ]

    operations = [
        migrations.AddField(
            model_name='generalmapping',
            name='use_intacct_employee_departments',
            field=models.BooleanField(default=False, help_text='Use SageIntacct Employee Default Department'),
        ),
        migrations.AddField(
            model_name='generalmapping',
            name='use_intacct_employee_locations',
            field=models.BooleanField(default=False, help_text='Use SageIntacct Employee Default Location'),
        ),
    ]
