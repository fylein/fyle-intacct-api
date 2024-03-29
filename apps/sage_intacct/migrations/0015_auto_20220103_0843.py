# Generated by Django 3.1.13 on 2022-01-03 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sage_intacct', '0014_journalentry_journalentrylineitem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='journalentry',
            name='entity_id',
        ),
        migrations.AddField(
            model_name='journalentrylineitem',
            name='employee_id',
            field=models.CharField(help_text='Sage Intacct employee id', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='journalentrylineitem',
            name='vendor_id',
            field=models.CharField(help_text='Sage Intacct vendor id', max_length=255, null=True),
        ),
    ]
