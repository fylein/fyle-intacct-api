# Generated by Django 3.1.14 on 2022-01-07 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sage_intacct', '0015_auto_20220103_0843'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargecardtransaction',
            name='payee',
            field=models.CharField(help_text='Sage Intacct Payee', max_length=255, null=True),
        ),
    ]
