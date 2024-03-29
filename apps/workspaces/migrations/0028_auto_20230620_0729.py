# Generated by Django 3.1.14 on 2023-06-20 07:29

import apps.workspaces.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0027_auto_20230614_1010'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuration',
            name='reimbursable_expenses_object',
            field=models.CharField(choices=[('EXPENSE_REPORT', 'EXPENSE_REPORT'), ('BILL', 'BILL'), ('JOURNAL_ENTRY', 'JOURNAL_ENTRY')], help_text='Mapping Settings ( BILL / EXPENSE_REPORT )', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='workspace',
            name='onboarding_state',
            field=models.CharField(choices=[('CONNECTION', 'CONNECTION'), ('LOCATION_ENTITY_MAPPINGS', 'LOCATION_ENTITY_MAPPINGS'), ('EXPORT_SETTINGS', 'EXPORT_SETTINGS'), ('IMPORT_SETTINGS', 'IMPORT_SETTINGS'), ('ADVANCED_CONFIGURATION', 'ADVANCED_CONFIGURATION'), ('COMPLETE', 'COMPLETE')], default=apps.workspaces.models.get_default_onboarding_state, help_text='Onboarding status of the workspace', max_length=50, null=True),
        ),
    ]
