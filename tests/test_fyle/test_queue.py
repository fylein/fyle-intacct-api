from datetime import datetime, timezone, timedelta

from apps.tasks.models import Error
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
    error = Error(
        repetition_count=900,
        updated_at=datetime.now().replace(tzinfo=timezone.utc)
    )
    skip_export = validate_failing_export(is_auto_export=False, interval_hours=2, error=error)

    assert skip_export is False

    # Should return false if repetition count is less than 100
    error = Error(
        repetition_count=90,
        updated_at=datetime.now().replace(tzinfo=timezone.utc)
    )
    skip_export = validate_failing_export(is_auto_export=True, interval_hours=2, error=error)

    assert skip_export is False

    # Hourly schedule - erroed for 4 days straight - 101 repetitions
    error = Error(
        repetition_count=101,
        workspace_id=1,
        type='INTACCT_ERROR',
        error_title='Dummy title',
        error_detail='Dummy detail',
        updated_at=datetime.now()
    )
    error.save()

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=error)

    assert skip_export is True

    # Manually setting last error'd time to 25 hours ago
    Error.objects.filter(id=error.id).update(updated_at=datetime.now() - timedelta(hours=25))

    latest_error = Error.objects.get(id=error.id)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=latest_error)

    # Export should run once in a day
    assert skip_export is False

    # it should skip in next run after 1h, manually setting last error'd time to now
    Error.objects.filter(id=error.id).update(updated_at=datetime.now())
    latest_error = Error.objects.get(id=error.id)
    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=latest_error)

    assert skip_export is True
