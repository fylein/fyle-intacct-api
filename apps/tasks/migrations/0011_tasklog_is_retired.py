# Generated by Django 4.2.18 on 2025-03-05 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0010_alter_tasklog_expense_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasklog',
            name='is_retired',
            field=models.BooleanField(default=False, help_text='Is retired from exporting'),
        ),
    ]
