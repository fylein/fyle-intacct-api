# Generated by Django 4.2.20 on 2025-04-24 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0043_configuration_skip_accounting_export_summary_post'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='je_single_credit_line',
            field=models.BooleanField(default=False, help_text='Single credit line in journal entry'),
        ),
    ]
