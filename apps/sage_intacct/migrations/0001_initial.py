from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('fyle', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('vendor_id', models.CharField(help_text='Sage Intacct Vendor ID', max_length=255)),
                ('description', models.TextField(help_text='Sage Intacct Bill Description')),
                ('supdoc_id', models.CharField(help_text='Sage Intacct Attachments ID', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('expense_group', models.OneToOneField(help_text='Expense group reference', on_delete=django.db.models.deletion.PROTECT, to='fyle.ExpenseGroup')),
            ],
        ),
        migrations.CreateModel(
            name='BillLineitem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('expense_type_id', models.CharField(help_text='Sage Intacct expense type id', max_length=255, null=True)),
                ('gl_account_number', models.CharField(help_text='Sage Intacct gl account number', max_length=255, null=True)),
                ('project_id', models.CharField(help_text='Sage Intacct project id', max_length=255, null=True)),
                ('location_id', models.CharField(help_text='Sage Intacct location id', max_length=255, null=True)),
                ('department_id', models.CharField(help_text='Sage Intacct department id', max_length=255, null=True)),
                ('memo', models.CharField(help_text='Sage Intacct lineitem description', max_length=255, null=True)),
                ('amount', models.FloatField(help_text='Bill amount')),
                ('spent_at', models.DateTimeField(help_text='Spent at')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('bill', models.ForeignKey(help_text='Reference to Bill', on_delete=django.db.models.deletion.PROTECT, to='sage_intacct.Bill')),
                ('expense', models.OneToOneField(help_text='Reference to Expense', on_delete=django.db.models.deletion.PROTECT, to='fyle.Expense')),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseReport',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('employee_id', models.CharField(help_text='Sage Intacct Employee ID', max_length=255)),
                ('description', models.TextField(help_text='Sage Intacct ExpenseReport Description')),
                ('supdoc_id', models.CharField(help_text='Sage Intacct Attachments ID', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('expense_group', models.OneToOneField(help_text='Expense group reference', on_delete=django.db.models.deletion.PROTECT, to='fyle.ExpenseGroup')),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseReportLineitem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('expense_type_id', models.CharField(help_text='Sage Intacct expense type id', max_length=255, null=True)),
                ('gl_account_number', models.CharField(help_text='Sage Intacct gl account number', max_length=255, null=True)),
                ('project_id', models.CharField(help_text='Sage Intacct project id', max_length=255, null=True)),
                ('cost_type_id', models.CharField(help_text='Sage Intacct cost type id', max_length=255, null=True)),
                ('location_id', models.CharField(help_text='Sage Intacct location id', max_length=255, null=True)),
                ('department_id', models.CharField(help_text='Sage Intacct department id', max_length=255, null=True)),
                ('memo', models.CharField(help_text='Sage Intacct lineitem description', max_length=255, null=True)),
                ('amount', models.FloatField(help_text='Expense amount')),
                ('spent_at', models.DateTimeField(help_text='Spent at')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('expense_report', models.ForeignKey(help_text='Reference to ExpenseReport', on_delete=django.db.models.deletion.PROTECT, to='sage_intacct.ExpenseReport')),
                ('expense', models.OneToOneField(help_text='Reference to Expense', on_delete=django.db.models.deletion.PROTECT, to='fyle.Expense')),
            ],
        ),
        migrations.AlterModelTable(
            name='ExpenseReport',
            table='expense_reports',
        ),
        migrations.AlterModelTable(
            name='ExpenseReportLineitem',
            table='expense_report_lineitems',
        ),
        migrations.AlterModelTable(
            name='Bill',
            table='bills',
        ),
        migrations.AlterModelTable(
            name='BillLineitem',
            table='bill_lineitems',
        ),

    ]
