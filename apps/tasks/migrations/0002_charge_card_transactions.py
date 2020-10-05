import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion

import apps.tasks.models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sage_intacct', '0001_initial'),
        ('workspaces', '0001_initial'),
        ('fyle', '0001_initial'),
        ('tasks', '0001_initial')
    ]

    operations = [
        migrations.AddField(
            model_name='TaskLog',
            name='charge_card_transaction',
            field=models.ForeignKey(help_text='Reference to ChargeCardTransaction', null=True, \
                on_delete=django.db.models.deletion.PROTECT, to='sage_intacct.ChargeCardTransaction'),
        ),
        migrations.AlterField(
            model_name='tasklog',
            name='type',
            field=models.CharField(help_text=\
                'Task type (FETCH_EXPENSES / CREATE_BILL / CREATE_EXPENSE_REPORT / CREATE_CHARGE_CARD_TRANSACTION)', \
                max_length=50),
        ),
        migrations.AlterField(
            model_name='tasklog',
            name='detail',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=apps.tasks.models.get_default, \
                help_text='Task Response', null=True),
        ),
    ]
