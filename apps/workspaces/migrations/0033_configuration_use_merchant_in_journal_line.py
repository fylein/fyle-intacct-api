# Generated by Django 3.1.14 on 2024-01-29 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0032_auto_20230810_0702'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='use_merchant_in_journal_line',
            field=models.BooleanField(default=False, help_text='Export merchant as vendor in journal entry line item'),
        ),
    ]
