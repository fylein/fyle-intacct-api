# Generated by Django 3.1.14 on 2023-05-31 12:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0026_auto_20230531_0926'),
        ('mappings', '0013_auto_20230531_1040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalmapping',
            name='workspace',
            field=models.OneToOneField(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, related_name='general_mappings', to='workspaces.workspace'),
        ),
    ]
