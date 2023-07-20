# Generated by Django 3.1.14 on 2023-07-20 10:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0030_lastexportdetail'),
        ('fyle', '0025_auto_20230720_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dependentfieldsetting',
            name='workspace',
            field=models.OneToOneField(help_text='Reference to Workspace', on_delete=django.db.models.deletion.PROTECT, related_name='dependent_fields', to='workspaces.workspace'),
        ),
    ]
