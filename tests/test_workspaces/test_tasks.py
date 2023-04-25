from apps.tasks.models import TaskLog
from apps.workspaces.tasks import run_sync_schedule, schedule_sync, run_email_notification, \
    async_update_fyle_credentials,delete_cards_mapping_settings
from apps.workspaces.models import WorkspaceSchedule, Configuration, FyleCredential
from fyle_accounting_mappings.models import ExpenseAttribute, MappingSetting
from .fixtures import data


def test_schedule_sync(db):
    workspace_id = 1
    
    schedule_sync(
            hours=1,
            schedule_enabled=True,
            email_added=[
                'ashwin.t@fyle.in'
            ],
            emails_selected=[
                'ashwin.t@fyle.in'
            ],
            workspace_id=workspace_id
        )

    ws_schedule = WorkspaceSchedule.objects.filter( 
        workspace_id=workspace_id 
    ).first() 
    
    assert ws_schedule.schedule.func == 'apps.workspaces.tasks.run_sync_schedule'

    schedule_sync(
            hours=1,
            schedule_enabled=False,
            email_added=None,
            emails_selected=[
                'ashwin.t@fyle.in'
            ],
            workspace_id=workspace_id
        )

    ws_schedule = WorkspaceSchedule.objects.filter( 
        workspace_id=workspace_id 
    ).first() 

    assert ws_schedule.schedule == None


def test_run_sync_schedule(mocker,db):
    workspace_id = 1

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses']
    )

    run_sync_schedule(workspace_id)
    
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    configuration.save()

    run_sync_schedule(workspace_id)
    
    configuration.corporate_credit_card_expenses_object = 'EXPENSE_REPORT'
    configuration.save()

    run_sync_schedule(workspace_id)

    task_log = TaskLog.objects.filter(
        workspace_id=workspace_id
    ).first()
    
    assert task_log.status == 'ENQUEUED'

def test_run_sync_schedule_je(mocker,db):
    workspace_id = 1

    configuration = Configuration.objects.get(workspace_id=workspace_id)
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses']
    )

    run_sync_schedule(workspace_id)
    
    configuration.reimbursable_expenses_object = 'JOURNAL_ENTRY'
    configuration.corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
    configuration.save()

    run_sync_schedule(workspace_id)
    
    configuration.corporate_credit_card_expenses_object = 'JOURNAL_ENTRY'
    configuration.save()

    run_sync_schedule(workspace_id)

    task_log = TaskLog.objects.filter(
        workspace_id=workspace_id
    ).first()
    
    assert task_log.status == 'ENQUEUED'


def test_email_notification(db):
    workspace_id = 1

    schedule_sync(
            hours=1,
            schedule_enabled=True,
            email_added=None,
            emails_selected=[
                'user5@fyleforgotham.in'
            ],
            workspace_id=workspace_id
        )

    ws_schedule = WorkspaceSchedule.objects.filter( 
        workspace_id=workspace_id 
    ).first()
    run_email_notification(workspace_id=workspace_id)

    updated_ws_schedule = WorkspaceSchedule.objects.filter( 
        workspace_id=workspace_id, id=ws_schedule.id
    ).first()

    assert updated_ws_schedule.error_count == 3

    attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id, value='user5@fyleforgotham.in').first()
    attribute.delete()

    ws_schedule.enabled = True
    ws_schedule.additional_email_options = [{'email': 'user5@fyleforgotham.in', 'name': 'Ashwin'}]
    ws_schedule.save()

    run_email_notification(workspace_id=workspace_id)
    updated_ws_schedule = WorkspaceSchedule.objects.filter( 
        workspace_id=workspace_id, id=ws_schedule.id
    ).first()

    assert updated_ws_schedule.error_count == 3

def test_async_update_fyle_credentials(db):
    workspace_id = 1
    refresh_token = 'hehehuhu'

    async_update_fyle_credentials('or79Cob97KSh', refresh_token)

    fyle_credentials = FyleCredential.objects.filter(workspace_id=workspace_id).first()

    assert fyle_credentials.refresh_token == refresh_token

def test_delete_cards_mapping_settings(db):
    workspace_id = 1
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    configuration.corporate_credit_card_expenses_object == 'BILL'
    configuration.save()

    mapping_setting = MappingSetting.objects.filter(
            workspace_id=configuration.workspace_id,
        ).first()

    mapping_setting.source_field = 'CORPORATE_CARD'
    mapping_setting.destination_field = 'CHARGE_CARD_NUMBER'
    mapping_setting.save()

    assert mapping_setting.source_field == 'CORPORATE_CARD'

    delete_cards_mapping_settings(configuration)

    result_mapping_setting = MappingSetting.objects.filter(
            workspace_id=configuration.workspace_id,
            source_field='CORPORATE_CARD',
            destination_field='CHARGE_CARD_NUMBER'
        ).first()
    assert result_mapping_setting == None
