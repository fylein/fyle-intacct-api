# Generated by Django 3.0.3 on 2021-08-31 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sage_intacct', '0010_expensereportlineitem_expense_payment_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='billlineitem',
            name='class_id',
            field=models.CharField(help_text='Sage Intacct class id', max_length=255, null=True),
        ),
    ]
