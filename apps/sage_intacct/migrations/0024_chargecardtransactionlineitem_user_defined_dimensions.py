# Generated by Django 3.2.14 on 2024-04-01 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sage_intacct', '0023_auto_20230626_1430'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargecardtransactionlineitem',
            name='user_defined_dimensions',
            field=models.JSONField(help_text='Sage Intacct User Defined Dimensions', null=True),
        ),
    ]
