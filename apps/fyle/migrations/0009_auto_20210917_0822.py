# Generated by Django 3.0.3 on 2021-09-17 08:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0013_auto_20210723_1010'),
        ('fyle', '0008_reimbursement_payment_number'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='reimbursement',
            unique_together={('workspace', 'payment_number')},
        ),
    ]
