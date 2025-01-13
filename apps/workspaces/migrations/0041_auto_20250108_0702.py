# Generated by Django 3.2.14 on 2025-01-08 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0040_auto_20241223_1050'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='created_by',
            field=models.CharField(blank=True, help_text='Email of the user who created this record', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='configuration',
            name='updated_by',
            field=models.CharField(blank=True, help_text='Email of the user who last updated this record', max_length=255, null=True),
        ),
    ]
