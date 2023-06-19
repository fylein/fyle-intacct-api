# Generated by Django 3.1.14 on 2023-05-31 09:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0026_auto_20230531_0926'),
        ('fyle', '0019_expense_report_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensegroupsettings',
            name='workspace',
            field=models.OneToOneField(help_text='To which workspace this expense group setting belongs to', on_delete=django.db.models.deletion.PROTECT, related_name='expense_group_settings', to='workspaces.workspace'),
        ),
    ]
