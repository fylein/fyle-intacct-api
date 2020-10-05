from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('workspaces', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='WorkspaceGeneralSettings',
            name='corporate_credit_card_expenses_object',
            field=models.CharField(help_text='Mapping Settings ( BILL / CHARGE_CARD_TRANSACTION )', \
                max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='workspacegeneralsettings',
            name='reimbursable_expenses_object',
            field=models.CharField(help_text='Mapping Settings ( BILL / EXPENSE_REPORT )', max_length=50),
        ),
    ]
