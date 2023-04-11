# Generated by Django 3.1.14 on 2023-04-11 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0024_auto_20230321_0740'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='map_fyle_cards_intacct_account',
            field=models.BooleanField(default=True, help_text='Map Fyle Cards to Intacct Account'),
        ),
        migrations.AddField(
            model_name='configuration',
            name='skip_cards_mapping',
            field=models.BooleanField(default=False, help_text='Skip cards mapping'),
        ),
    ]
