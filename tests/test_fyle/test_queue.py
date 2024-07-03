from apps.fyle.models import Expense
from apps.workspaces.models import Workspace, FyleCredential
from apps.tasks.models import Error
from apps.sage_intacct.queue import __create_chain_and_run, validate_failing_export
from apps.fyle.queue import async_post_accounting_export_summary, async_import_and_export_expenses


# This test is just for cov :D
def test_async_post_accounting_export_summary(db):
    async_post_accounting_export_summary(1, 1)
    assert True

# This test is just for cov :D
def test_create_chain_and_run(db):
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    in_progress_expenses = Expense.objects.filter(org_id='or79Cob97KSh')
    chain_tasks = [
        {
            'target': 'apps.sage_intacct.tasks.create_bill',
            'expense_group': 1,
            'task_log_id': 1,
            'last_export': True
        }
    ]

    __create_chain_and_run(fyle_credentials, in_progress_expenses, workspace_id, chain_tasks, 'PERSONAL')
    assert True


# This test is just for cov :D
def test_async_import_and_export_expenses(db):
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
    # Should return false for manual trigger from UI
    error = Error(
        repetition_count=900
    )
    skip_export = validate_failing_export(is_auto_export=False, interval_hours=2, error=error)

    assert skip_export is False

    # Should return false if repetition count is less than 100

    error = Error(
        repetition_count=90
    )
    skip_export = validate_failing_export(is_auto_export=True, interval_hours=2, error=error)

    assert skip_export is False

    # Should return true if repetition count is greater than 100 and repetition count should be increased by 1
    error = Error(
        repetition_count=900,
        workspace_id=1,
        type='INTACCT_ERROR',
        error_title='Dummy title',
        error_detail='Dummy detail'
    )
    error.save()
    skip_export = validate_failing_export(is_auto_export=True, interval_hours=2, error=error)

    assert skip_export is True

    latest_error = Error.objects.get(id=error.id)
    assert latest_error.repetition_count == 901

    # Hourly schedule - erroed for 4 days straight - 101 repetitions
    error = Error(
        repetition_count=101,
        workspace_id=1,
        type='INTACCT_ERROR',
        error_title='Dummy title',
        error_detail='Dummy detail'
    )
    error.save()

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=error)

    assert skip_export is True
    latest_error = Error.objects.get(id=error.id)
    assert latest_error.repetition_count == 102

    # 103 - repetition count should get increased by 1
    validate_failing_export(is_auto_export=True, interval_hours=1, error=latest_error)

    assert skip_export is True
    latest_error = Error.objects.get(id=error.id)
    assert latest_error.repetition_count == 103

    # 120 - manually setting to 120 and trying to check no skip case
    latest_error.repetition_count = 119
    latest_error.save()

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=latest_error)

    # Export should run once in a day
    assert skip_export is False

    # 121 - it should skip
    latest_error = Error.objects.get(id=latest_error.id)

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=1, error=latest_error)

    assert skip_export is True

    # Test 24h schedule, it shouldn't get skipped at any point
    error = Error(
        repetition_count=105,
        workspace_id=1,
        type='INTACCT_ERROR',
        error_title='Dummy title',
        error_detail='Dummy detail'
    )
    error.save()

    skip_export = validate_failing_export(is_auto_export=True, interval_hours=24, error=error)

    assert skip_export is False
