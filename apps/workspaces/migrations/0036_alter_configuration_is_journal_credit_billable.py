# Generated by Django 3.2.14 on 2024-08-06 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0035_configuration_auto_create_merchants_as_vendors'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuration',
            name='is_journal_credit_billable',
            field=models.BooleanField(default=False, help_text='Billable on journal entry credit line'),
        ),
    ]
