# Generated by Django 3.0.3 on 2021-09-17 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0007_expense_org_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='reimbursement',
            name='payment_number',
            field=models.CharField(help_text='Fyle Payment Number', max_length=255, null=True),
        ),
    ]
