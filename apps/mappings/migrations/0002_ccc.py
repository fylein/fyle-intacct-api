from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('workspaces', '0001_initial'),
        ('mappings', '0001_initial')
    ]

    operations = [
        migrations.AddField(
            model_name='GeneralMapping',
            name='default_charge_card_name',
            field=models.CharField(help_text='Default charge card name', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='GeneralMapping',
            name='default_charge_card_id',
            field=models.CharField(help_text='Default charge card ID', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='GeneralMapping',
            name='default_ccc_vendor_name',
            field=models.CharField(help_text='Default ccc vendor name', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='GeneralMapping',
            name='default_ccc_vendor_id',
            field=models.CharField(help_text='Default ccc vendor ID', max_length=255, null=True),
        ),
    ]
