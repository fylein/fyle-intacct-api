from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('fyle', '0001_initial'),
        ('sage_intacct', '0001_initial')
    ]

    operations = [
        migrations.CreateModel(
            name='ChargeCardTransaction',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('charge_card_id', models.CharField(help_text='Sage Intacct Charge Card ID', max_length=255)),
                ('description', models.TextField(help_text='Sage Intacct Charge Card Transaction Description')),
                ('supdoc_id', models.CharField(help_text='Sage Intacct Attachments ID', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('expense_group', models.OneToOneField(help_text='Expense group reference', \
                    on_delete=django.db.models.deletion.PROTECT, to='fyle.ExpenseGroup')),
            ],
        ),
        migrations.CreateModel(
            name='ChargeCardTransactionLineitem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('gl_account_number', models.CharField(help_text='Sage Intacct gl account number', \
                    max_length=255, null=True)),
                ('project_id', models.CharField(help_text='Sage Intacct project id', max_length=255, null=True)),
                ('location_id', models.CharField(help_text='Sage Intacct location id', max_length=255, null=True)),
                ('department_id', models.CharField(help_text='Sage Intacct department id', max_length=255, null=True)),
                ('amount', models.FloatField(help_text='Charge Card Transaction amount')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('charge_card_transaction', models.ForeignKey(help_text='Reference to ChargeCardTransaction', \
                    on_delete=django.db.models.deletion.PROTECT, to='sage_intacct.ChargeCardTransaction')),
                ('expense', models.OneToOneField(help_text='Reference to Expense', \
                    on_delete=django.db.models.deletion.PROTECT, to='fyle.Expense')),
            ],
        ),
        migrations.AlterModelTable(
            name='ChargeCardTransaction',
            table='charge_card_transactions',
        ),
        migrations.AlterModelTable(
            name='ChargeCardTransactionLineitem',
            table='charge_card_transaction_lineitems',
        ),
        migrations.RemoveField(
            model_name='ExpenseReportLineitem',
            name='cost_type_id',
        ),
        migrations.AddField(
            model_name='ExpenseReport',
            name='memo',
            field=models.CharField(help_text='Sage Intacct memo', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='Bill',
            name='memo',
            field=models.CharField(help_text='Sage Intacct docnumber', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='ChargeCardTransaction',
            name='memo',
            field=models.CharField(help_text='Sage Intacct referenceno', max_length=255, null=True),
        ),
    ]
