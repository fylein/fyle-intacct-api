# Generated by Django 3.2.14 on 2024-07-23 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sage_intacct', '0026_billlineitem_allocation_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='journalentrylineitem',
            name='allocation_id',
            field=models.CharField(help_text='Sage Intacct Allocation id', max_length=255, null=True),
        ),
    ]
