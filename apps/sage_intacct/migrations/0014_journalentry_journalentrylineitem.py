# Generated by Django 3.1.13 on 2021-12-29 13:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0011_auto_20211203_1156'),
        ('sage_intacct', '0013_auto_20211203_1156'),
    ]

    operations = [
        migrations.CreateModel(
            name='JournalEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('entity_id', models.CharField(help_text='Sage Intacct Entity ID', max_length=255)),
                ('description', models.TextField(help_text='Sage Intacct ExpenseReport Description')),
                ('memo', models.TextField(help_text='Sage Intacct memo', null=True)),
                ('currency', models.CharField(help_text='Expense Report Currency', max_length=5)),
                ('supdoc_id', models.CharField(help_text='Sage Intacct Attachments ID', max_length=255, null=True)),
                ('transaction_date', models.DateTimeField(help_text='Expense Report transaction date', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('expense_group', models.OneToOneField(help_text='Expense group reference', on_delete=django.db.models.deletion.PROTECT, to='fyle.expensegroup')),
            ],
            options={
                'db_table': 'journal_entries',
            },
        ),
        migrations.CreateModel(
            name='JournalEntryLineitem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('gl_account_number', models.CharField(help_text='Sage Intacct gl account number', max_length=255, null=True)),
                ('project_id', models.CharField(help_text='Sage Intacct project id', max_length=255, null=True)),
                ('location_id', models.CharField(help_text='Sage Intacct location id', max_length=255, null=True)),
                ('class_id', models.CharField(help_text='Sage Intacct class id', max_length=255, null=True)),
                ('department_id', models.CharField(help_text='Sage Intacct department id', max_length=255, null=True)),
                ('customer_id', models.CharField(help_text='Sage Intacct customer id', max_length=255, null=True)),
                ('item_id', models.CharField(help_text='Sage Intacct iten id', max_length=255, null=True)),
                ('memo', models.TextField(help_text='Sage Intacct lineitem description', null=True)),
                ('user_defined_dimensions', models.JSONField(help_text='Sage Intacct User Defined Dimensions', null=True)),
                ('amount', models.FloatField(help_text='Bill amount')),
                ('billable', models.BooleanField(help_text='Expense Billable or not', null=True)),
                ('transaction_date', models.DateTimeField(help_text='Expense Report transaction date', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('expense', models.OneToOneField(help_text='Reference to Expense', on_delete=django.db.models.deletion.PROTECT, to='fyle.expense')),
                ('journal_entry', models.ForeignKey(help_text='Reference to Journal Entry', on_delete=django.db.models.deletion.PROTECT, to='sage_intacct.journalentry')),
            ],
            options={
                'db_table': 'journal_entry_lineitems',
            },
        ),
    ]
