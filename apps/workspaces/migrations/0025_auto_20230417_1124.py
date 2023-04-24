# Generated by Django 3.1.14 on 2023-04-17 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0024_auto_20230321_0740'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuration',
            name='reimbursable_expenses_object',
            field=models.CharField(choices=[('EXPENSE_REPORT', 'EXPENSE_REPORT'), ('BILL', 'BILL'), ('JOURNAL_ENTRY', 'JOURNAL_ENTRY')], help_text='Mapping Settings ( BILL / EXPENSE_REPORT )', max_length=50),
        ),
    ]