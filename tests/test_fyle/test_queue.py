from datetime import datetime, timezone, timedelta

from apps.fyle.models import ExpenseGroup
from apps.tasks.models import Error, TaskLog
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

    error = Error(
        repetition_count=900,
        updated_at=datetime.now(tz=timezone.utc),
        expense_group=expense_group,
        workspace_id=1
    )
    skip_export = validate_failing_export(is_auto_export=False, interval_hours=2, error=error, expense_group=expense_group)

    assert skip_export is False
    assert task_log.is_retired is False

    # Should return false if repetition count is less than 100
    task_log.created_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    task_log.save()

    error = Error(
        repetition_count=90,
        updated_at=datetime.now(tz=timezone.utc),
        workspace_id=1
    )
    skip_export = validate_failing_export(is_auto_export=True, interval_hours=2, error=error, expense_group=expense_group)

    assert skip_export is False
    assert task_log.is_retired is False

    # Hourly schedule - errored for 4 days straight - 101 repetitions
    error = Error.objects.create(
        repetition_count=101,
        workspace_id=1,
        type='INTACCT_ERROR',
        error_title='Dummy title',
        error_detail='Dummy detail',
        updated_at=datetime.now(tz=timezone.utc)
    )

    task_log.created_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    task_log.save()

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=error, expense_group=expense_group)

    assert skip_export is True
    assert task_log.is_retired is False

    # Manually setting last error'd time to 25 hours ago
    task_log.created_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    task_log.refresh_from_db()
    task_log.save()

    Error.objects.filter(id=error.id).update(updated_at=datetime.now(tz=timezone.utc) - timedelta(hours=25))
    latest_error = Error.objects.get(id=error.id)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=latest_error, expense_group=expense_group)

    assert skip_export is False
    task_log.refresh_from_db()
    assert task_log.is_retired is False

    # It should skip in next run after 1h, manually setting last error'd time to now
    Error.objects.filter(id=error.id).update(updated_at=datetime.now(tz=timezone.utc))
    latest_error = Error.objects.get(id=error.id)
    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=latest_error, expense_group=expense_group)

    assert skip_export is True

    # Task Log created 2 months ago and error repetition count is 101
    task_log.created_at = datetime.now(tz=timezone.utc) - timedelta(days=61)
    task_log.save()

    error = Error.objects.create(
        repetition_count=101,
        workspace_id=1,
        type='INTACCT_ERROR',
        error_title='Dummy title',
        error_detail='Dummy detail',
        updated_at=datetime.now(tz=timezone.utc)
    )

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=error, expense_group=expense_group)

    assert skip_export is True
    task_log.refresh_from_db()
    assert task_log.is_retired is True

    # Task Log created 1 month ago and error repetition count is 101
    task_log.created_at = datetime.now(tz=timezone.utc) - timedelta(days=30)
    task_log.is_retired = False
    task_log.save()

    error = Error.objects.create(
        repetition_count=101,
        workspace_id=1,
        type='INTACCT_ERROR',
        error_title='Dummy title',
        error_detail='Dummy detail',
        updated_at=datetime.now(tz=timezone.utc)
    )

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=error, expense_group=expense_group)

    assert skip_export is True
    task_log.refresh_from_db()
    assert task_log.is_retired is False

    # Error last updated > 1 week ago
    Error.objects.filter(id=error.id).update(updated_at=datetime.now(tz=timezone.utc) - timedelta(days=8))
    latest_error = Error.objects.get(id=error.id)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=latest_error, expense_group=expense_group)

    assert skip_export is False
    assert task_log.is_retired is False

    # Error last updated > 24 hrs ago
    Error.objects.filter(id=error.id).update(updated_at=datetime.now(tz=timezone.utc) - timedelta(days=2))
    latest_error = Error.objects.get(id=error.id)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=latest_error, expense_group=expense_group)

    assert skip_export is True
    task_log.refresh_from_db()
    assert task_log.is_retired is False

    # Error last updated < 24 hrs ago
    task_log.created_at = datetime.now(tz=timezone.utc) - timedelta(days=14)
    task_log.is_retired = False
    task_log.save()

    Error.objects.filter(id=error.id).update(updated_at=datetime.now(tz=timezone.utc), repetition_count=10)
    latest_error = Error.objects.get(id=error.id)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=latest_error, expense_group=expense_group)

    assert skip_export is False
    task_log.refresh_from_db()
    assert task_log.is_retired is False
