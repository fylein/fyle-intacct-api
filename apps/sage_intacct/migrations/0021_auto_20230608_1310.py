# Generated by Django 3.1.14 on 2023-06-08 13:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0025_auto_20230417_1124'),
        ('sage_intacct', '0020_costtypes'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CostTypes',
            new_name='CostType',
        ),
    ]
