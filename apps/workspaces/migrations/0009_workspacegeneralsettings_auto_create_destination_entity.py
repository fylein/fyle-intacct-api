# Generated by Django 3.0.3 on 2021-03-03 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0008_workspacegeneralsettings_import_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='workspacegeneralsettings',
            name='auto_create_destination_entity',
            field=models.BooleanField(default=False, help_text='Auto create vendor / employee'),
        ),
    ]
