# Generated by Django 3.1.14 on 2022-12-13 08:57

import apps.fyle.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0015_expensegroup_export_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='expensegroupsettings',
            name='ccc_expense_state',
            field=models.CharField(choices=[('APPROVED', 'APPROVED'), ('PAID', 'PAID'), ('PAYMENT_PROCESSING', 'PAYMENT_PROCESSING')], default=apps.fyle.models.get_default_ccc_expense_state, help_text='state at which the ccc expenses are fetched (APPROVED/PAID)', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='expense',
            name='expense_updated_at',
            field=models.DateTimeField(help_text='Expense updated at'),
        ),
    ]
