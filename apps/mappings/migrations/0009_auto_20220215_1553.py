# Generated by Django 3.1.14 on 2022-02-15 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mappings', '0008_auto_20210831_0718'),
    ]

    operations = [
        migrations.AddField(
            model_name='generalmapping',
            name='default_tax_code_id',
            field=models.CharField(help_text='DEfault Tax Code Id', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='generalmapping',
            name='default_tax_code_name',
            field=models.CharField(help_text='DEfault Tax Code Id', max_length=255, null=True),
        ),
    ]
