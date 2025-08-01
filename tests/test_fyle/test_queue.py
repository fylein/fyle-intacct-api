from datetime import datetime, timedelta, timezone

from fyle_accounting_library.rabbitmq.data_class import Task

from apps.fyle.models import ExpenseGroup
from apps.fyle.queue import async_import_and_export_expenses
from apps.sage_intacct.queue import __create_chain_and_run, validate_failing_export
from apps.tasks.models import TaskLog
from apps.workspaces.models import Workspace


def test_create_chain_and_run(db, mocker):
    """
    Test create_chain_and_run
    """
    mock_check_interval = mocker.patch('apps.sage_intacct.queue.check_interval_and_sync_dimension')

    mock_task_executor_run = mocker.patch('fyle_accounting_library.rabbitmq.helpers.TaskChainRunner.run')

    workspace_id = 1
    chain_tasks = [
        Task(
            target='apps.sage_intacct.tasks.create_bill',
            args=[1, 1, True, True]
        )
    ]

    __create_chain_and_run(workspace_id, chain_tasks, True)

    mock_check_interval.assert_called_once_with(workspace_id)
    mock_task_executor_run.assert_called_once_with(chain_tasks, workspace_id)


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


# This test is just for cov :D (2)
def test_async_import_and_export_expenses_2(db):
    """
    Test async_import_and_export_expenses_2
    """
    body = {
        'action': 'STATE_CHANGE_PAYMENT_PROCESSING',
        'data': {
            'id': 'rp1s1L3QtMpF',
            'org_id': 'or79Cob97KSh',
            'state': 'APPROVED'
        }
    }

    worksapce, _ = Workspace.objects.update_or_create(
        fyle_org_id = 'or79Cob97KSh'
    )

    async_import_and_export_expenses(body, worksapce.id)
