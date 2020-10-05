from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ExpenseGroup',
            name='fund_source',
            field=models.CharField(default='PERSONAL', help_text='Expense fund source', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='expensegroup',
            name='fyle_group_id',
            field=models.CharField(help_text='fyle expense group id report id, etc', max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='expensegroup',
            unique_together={('fyle_group_id', 'workspace')},
        ),
    ]
