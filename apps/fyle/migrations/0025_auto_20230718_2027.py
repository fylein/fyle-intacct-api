# Generated by Django 3.1.14 on 2023-07-18 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0024_auto_20230705_1057'),
    ]

    operations = [
        migrations.AddField(
            model_name='dependentfieldsetting',
            name='cost_code_placeholder',
            field=models.TextField(blank=True, help_text='Placeholder for Cost code', null=True),
        ),
        migrations.AddField(
            model_name='dependentfieldsetting',
            name='cost_type_placeholder',
            field=models.TextField(blank=True, help_text='Placeholder for Cost Type', null=True),
        ),
    ]
