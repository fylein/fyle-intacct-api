from datetime import datetime, timezone, timedelta

from apps.fyle.models import ExpenseGroup
from apps.tasks.models import TaskLog
from apps.workspaces.models import Workspace
from apps.sage_intacct.queue import __create_chain_and_run, validate_failing_export
from apps.fyle.queue import async_import_and_export_expenses


def test_create_chain_and_run(db):
    """
    Test create_chain_and_run
    """
    workspace_id = 1
    chain_tasks = [
        {
            'target': 'apps.sage_intacct.tasks.create_bill',
            'expense_group': 1,
            'task_log_id': 1,
            'last_export': True
        }
    ]

    __create_chain_and_run(workspace_id, chain_tasks, False)
    assert True


def test_async_import_and_export_expenses(db):
    """
    Test async_import_and_export_expenses
    """
    body = {
        'action': 'ACCOUNTING_EXPORT_INITIATED',
        'data': {
            'id': 'rp1s1L3QtMpF',
            'org_id': 'or79Cob97KSh'
        }
    }

    worksapce, _ = Workspace.objects.update_or_create(
        fyle_org_id='or79Cob97KSh'
    )

    async_import_and_export_expenses(body, worksapce.id)


def test_validate_failing_export(db):
    """
    Test validate_failing_export
    """
    # Should return false for manual trigger from UI
    expense_group = ExpenseGroup.objects.filter(workspace_id=1).first()
    task_log = TaskLog.objects.filter(workspace_id=1).first()

    skip_export = validate_failing_export(is_auto_export=False, interval_hours=2, expense_group=expense_group)

    assert skip_export is False
    task_log.refresh_from_db()
    assert task_log.is_retired is False

    # Task Log created 25 hour ago and tried 25 hours ago
    time = datetime.now(tz=timezone.utc) - timedelta(hours=25)
    TaskLog.objects.filter(workspace_id=1).update(updated_at=time, created_at=time)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=2, expense_group=expense_group)

    assert skip_export is False
    task_log.refresh_from_db()
    assert task_log.is_retired is False

    # Hourly schedule - Task Log created 1 hour ago but tried to export 1 hour ago
    time = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    TaskLog.objects.filter(workspace_id=1).update(updated_at=time, created_at=time)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, expense_group=expense_group)

    assert skip_export is True
    task_log.refresh_from_db()
    assert task_log.is_retired is False

    # Task Log created 29 days and tried 7 days ago
    update_time = datetime.now(tz=timezone.utc) - timedelta(days=7)
    create_time = datetime.now(tz=timezone.utc) - timedelta(days=29)

    TaskLog.objects.filter(workspace_id=1).update(updated_at=update_time, created_at=create_time)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=2, expense_group=expense_group)

    assert skip_export is False
    task_log.refresh_from_db()
    assert task_log.is_retired is False

    # Task Log created 31 days and tried 19 days ago
    update_time = datetime.now(tz=timezone.utc) - timedelta(days=19)
    create_time = datetime.now(tz=timezone.utc) - timedelta(days=31)

    TaskLog.objects.filter(workspace_id=1).update(updated_at=update_time, created_at=create_time)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=2, expense_group=expense_group)

    assert skip_export is False
    task_log.refresh_from_db()
    assert task_log.is_retired is False

    # Task Log created 61 days and tried 6 days ago
    update_time = datetime.now(tz=timezone.utc) - timedelta(days=6)
    create_time = datetime.now(tz=timezone.utc) - timedelta(days=61)

    TaskLog.objects.filter(workspace_id=1).update(updated_at=update_time, created_at=create_time)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=2, expense_group=expense_group)

    assert skip_export is True
    task_log.refresh_from_db()
    assert task_log.is_retired is True

    # is_auto_export is False
    skip_export = validate_failing_export(is_auto_export=False, interval_hours=2, expense_group=expense_group)

    assert skip_export is False
