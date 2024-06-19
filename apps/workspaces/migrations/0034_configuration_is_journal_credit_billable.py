# Generated by Django 3.2.14 on 2024-06-19 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0033_configuration_use_merchant_in_journal_line'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='is_journal_credit_billable',
            field=models.BooleanField(default=True, help_text='Project on journal entry credit line'),
        ),
    ]
