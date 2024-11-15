# Generated by Django 3.2.14 on 2024-11-12 04:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sage_intacct', '0029_auto_20240902_1511'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='costtype',
            index=models.Index(fields=['project_id'], name='cost_types_project_04e2f5_idx'),
        ),
        migrations.AddIndex(
            model_name='costtype',
            index=models.Index(fields=['task_id'], name='cost_types_task_id_085813_idx'),
        ),
        migrations.AddIndex(
            model_name='costtype',
            index=models.Index(fields=['task_name'], name='cost_types_task_na_17ecec_idx'),
        ),
    ]