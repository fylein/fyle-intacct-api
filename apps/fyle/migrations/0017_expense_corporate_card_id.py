# Generated by Django 3.1.14 on 2023-04-14 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0016_auto_20221213_0857'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='corporate_card_id',
            field=models.CharField(blank=True, help_text='Corporate Card ID', max_length=255, null=True),
        ),
    ]