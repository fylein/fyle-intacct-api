from apps.tasks.models import TaskLog
from apps.workspaces.tasks import run_sync_schedule, schedule_sync, run_email_notification
from apps.workspaces.models import WorkspaceSchedule, Configuration
from .fixtures import data


def test_schedule_sync(db):
    workspace_id = 1
    
    schedule_sync(
            hours=1,
            schedule_enabled=True,
            email_added=None,
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

    general_settings = Configuration.objects.get(workspace_id=workspace_id)
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses']
    )

    run_sync_schedule(workspace_id)

    task_log = TaskLog.objects.filter(
        workspace_id=workspace_id
    ).first()
    
    assert task_log.status == 'COMPLETE'

    general_settings.reimbursable_expenses_object = 'PURCHASE BILL'
    general_settings.corporate_credit_card_expenses_object = 'BANK TRANSACTION'
    general_settings.save()

    run_sync_schedule(workspace_id)
    
    task_log = TaskLog.objects.filter(
        workspace_id=workspace_id
    ).first()
    
    assert task_log.status == 'COMPLETE'


def test_email_notification(db):
    workspace_id = 1

    schedule_sync(
            hours=1,
            schedule_enabled=True,
            email_added=None,
            emails_selected=[
                'ashwin.t@fyle.in'
            ],
            workspace_id=workspace_id
        )

    ws_schedule = WorkspaceSchedule.objects.filter( 
        workspace_id=workspace_id 
    ).first()

    ws_schedule.enabled = True
    ws_schedule.emails_selected = ['ashwin.t@fyle.in']
    ws_schedule.save()

    run_email_notification(workspace_id=workspace_id)
