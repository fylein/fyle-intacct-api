# Generated by Django 3.1.13 on 2021-12-03 11:56

import apps.tasks.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_auto_20210208_0548'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tasklog',
            name='detail',
            field=models.JSONField(default=apps.tasks.models.get_default, help_text='Task Response', null=True),
        ),
        migrations.AlterField(
            model_name='tasklog',
            name='sage_intacct_errors',
            field=models.JSONField(help_text='Sage Intacct Errors', null=True),
        ),
    ]
