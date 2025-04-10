# Generated by Django 4.2.20 on 2025-04-10 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0040_expense_expenses_account_ff34f0_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='imported_from',
            field=models.CharField(choices=[('WEBHOOK', 'WEBHOOK'), ('DASHBOARD_SYNC', 'DASHBOARD_SYNC'), ('DIRECT_EXPORT', 'DIRECT_EXPORT'), ('BACKGROUND_SCHEDULE', 'BACKGROUND_SCHEDULE'), ('INTERNAL', 'INTERNAL')], help_text='Imported from source', max_length=255, null=True),
        ),
    ]
