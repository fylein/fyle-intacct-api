# Generated by Django 3.1.14 on 2022-02-10 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sage_intacct', '0016_chargecardtransaction_payee'),
    ]

    operations = [
        migrations.AddField(
            model_name='billlineitem',
            name='tax_amount',
            field=models.FloatField(help_text='Tax amount', null=True),
        ),
        migrations.AddField(
            model_name='billlineitem',
            name='tax_code',
            field=models.CharField(help_text='Tax Group ID', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='chargecardtransactionlineitem',
            name='tax_amount',
            field=models.FloatField(help_text='Tax amount', null=True),
        ),
        migrations.AddField(
            model_name='chargecardtransactionlineitem',
            name='tax_code',
            field=models.CharField(help_text='Tax Group ID', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='expensereportlineitem',
            name='tax_amount',
            field=models.FloatField(help_text='Tax amount', null=True),
        ),
        migrations.AddField(
            model_name='expensereportlineitem',
            name='tax_code',
            field=models.CharField(help_text='Tax Group ID', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='journalentrylineitem',
            name='tax_amount',
            field=models.FloatField(help_text='Tax amount', null=True),
        ),
        migrations.AddField(
            model_name='journalentrylineitem',
            name='tax_code',
            field=models.CharField(help_text='Tax Group ID', max_length=255, null=True),
        ),
    ]
