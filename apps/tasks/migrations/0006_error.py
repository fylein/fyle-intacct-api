# Generated by Django 3.1.14 on 2023-07-01 11:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0023_expense_posted_at'),
        ('fyle_accounting_mappings', '0018_auto_20220419_0709'),
        ('workspaces', '0028_auto_20230620_0729'),
        ('tasks', '0005_tasklog_journal_entry'),
    ]

    operations = [
        migrations.CreateModel(
            name='Error',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('EMPLOYEE_MAPPING', 'EMPLOYEE_MAPPING'), ('CATEGORY_MAPPING', 'CATEGORY_MAPPING'), ('INTACCT_ERROR', 'INTACCT_ERROR')], help_text='Error type', max_length=50)),
                ('is_resolved', models.BooleanField(default=False, help_text='Is resolved')),
                ('error_title', models.CharField(help_text='Error title', max_length=255)),
                ('error_detail', models.TextField(help_text='Error detail')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('expense_attribute', models.OneToOneField(help_text='Reference to Expense Attribute', null=True, on_delete=django.db.models.deletion.PROTECT, to='fyle_accounting_mappings.expenseattribute')),
                ('expense_group', models.ForeignKey(help_text='Reference to Expense group', null=True, on_delete=django.db.models.deletion.PROTECT, to='fyle.expensegroup')),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace')),
            ],
            options={
                'db_table': 'errors',
            },
        ),
    ]