# Generated by Django 3.1.14 on 2023-06-15 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sage_intacct', '0021_auto_20230608_1310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='costtype',
            name='record_number',
            field=models.IntegerField(help_text='Sage Intacct Record No'),
        ),
    ]
