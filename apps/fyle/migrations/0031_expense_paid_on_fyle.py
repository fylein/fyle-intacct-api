# Generated by Django 3.2.14 on 2024-06-05 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0030_dependentfieldsetting_last_synced_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='paid_on_fyle',
            field=models.BooleanField(default=False, help_text='Expense Payment status on Fyle'),
        ),
    ]