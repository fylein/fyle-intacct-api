import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion

import apps.tasks.models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sage_intacct', '0001_initial'),
        ('sage_intacct', '0002_charge_card_transactions'),
        ('workspaces', '0001_initial'),
        ('fyle', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskLog',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type', models.CharField(help_text='Task type (FETCH_EXPENSES / CREATE_BILL / \
                    CREATE_EXPENSE_REPORTS)', max_length=50)),
                ('task_id', models.CharField(help_text='Fyle Jobs task reference', max_length=255, null=True)),
                ('status', models.CharField(help_text='Task Status', max_length=255)),
                ('detail', django.contrib.postgres.fields.jsonb.JSONField(default=apps.tasks.models.get_default, \
                    help_text='Task response', null=True)),
                ('sage_intacct_errors', django.contrib.postgres.fields.jsonb.JSONField(\
                    help_text='Sage Intacct Errors', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('bill', models.ForeignKey(help_text='Reference to Bill', null=True,
                                           on_delete=django.db.models.deletion.PROTECT, to='sage_intacct.Bill')),
                ('expense_report', models.ForeignKey(help_text='Reference to ExpenseReport', null=True, \
                    on_delete=django.db.models.deletion.PROTECT, to='sage_intacct.ExpenseReport')),
                ('expense_group', models.ForeignKey(help_text='Reference to Expense group', null=True, \
                    on_delete=django.db.models.deletion.PROTECT, to='fyle.ExpenseGroup')),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace model', \
                    on_delete=django.db.models.deletion.PROTECT, to='workspaces.Workspace')),
            ],
        ),
        migrations.AlterModelTable(
            name='TaskLog',
            table='task_logs',
        ),
    ]
