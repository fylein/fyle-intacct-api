# Generated by Django 3.1.14 on 2022-05-24 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0020_configuration_change_accounting_period'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='import_vendors_as_merchants',
            field=models.BooleanField(default=False, help_text='Auto import vendors from sage intacct as merchants to Fyle'),
        ),
    ]
