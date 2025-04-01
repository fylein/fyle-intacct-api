# Generated by Django 4.2.18 on 2025-02-26 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0036_auto_20250108_0702'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dependentfieldsetting',
            name='cost_type_field_id',
            field=models.IntegerField(help_text='Fyle Cost Type Field ID', null=True),
        ),
        migrations.AlterField(
            model_name='dependentfieldsetting',
            name='cost_type_field_name',
            field=models.CharField(help_text='Fyle Cost Type Field Name', max_length=255, null=True),
        ),
    ]
