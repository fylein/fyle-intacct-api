from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Workspace',
            fields=[
                ('id', models.AutoField(help_text='Unique Id to identify a workspace', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Name of the workspace', max_length=255)),
                ('fyle_org_id', models.CharField(help_text='org id', max_length=255, unique=True)),
                ('last_synced_at', models.DateTimeField(help_text='Datetime when expenses were pulled last', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('user', models.ManyToManyField(help_text='Reference to users table', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SageIntacctCredential',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('si_user_id', models.TextField(help_text='Stores Sage Intacct user id')),
                ('si_company_id', models.TextField(help_text='Stores Sage Intacct company id')),
                ('si_company_name', models.TextField(help_text='Stores Sage Intacct company name')),
                ('si_user_password', models.TextField(help_text='Stores Sage Intacct user password')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('workspace', models.OneToOneField(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.Workspace')),
            ],
        ),
        migrations.CreateModel(
            name='FyleCredential',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('refresh_token', models.TextField(help_text='Stores Fyle refresh token')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('workspace', models.OneToOneField(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.Workspace')),
            ],
        ),
        migrations.CreateModel(
            name='WorkspaceGeneralSettings',
            fields=[
                ('id', models.AutoField(help_text='Unique Id to identify a workspace', primary_key=True, serialize=False)),
                ('reimbursable_expenses_object', models.CharField(help_text='Mapping Settings ( BILLS / EXPENSE_REPORT )', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at')),
                ('workspace', models.OneToOneField(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.Workspace')),
            ],
        ),
        migrations.AlterModelTable(
            name='FyleCredential',
            table='fyle_credentials',
        ),
        migrations.AlterModelTable(
            name='SageIntacctCredential',
            table='sage_intacct_credentials',
        ),
        migrations.AlterModelTable(
            name='Workspace',
            table='workspaces',
        ),
        migrations.AlterModelTable(
            name='WorkspaceGeneralSettings',
            table='general_settings',
        ),
    ]
