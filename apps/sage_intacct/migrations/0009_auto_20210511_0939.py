# Generated by Django 3.0.3 on 2021-05-11 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sage_intacct', '0008_auto_20210408_0812'),
    ]

    operations = [
        migrations.AddField(
            model_name='billlineitem',
            name='task_id',
            field=models.CharField(help_text='Sage Intacct task id', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='chargecardtransactionlineitem',
            name='task_id',
            field=models.CharField(help_text='Sage Intacct task id', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='expensereportlineitem',
            name='task_id',
            field=models.CharField(help_text='Sage Intacct task id', max_length=255, null=True),
        ),
    ]
