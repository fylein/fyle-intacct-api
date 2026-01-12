from fyle_accounting_library.rabbitmq.data_class import Task
from fyle_accounting_mappings.models import ExpenseAttribute

from apps.fyle.queue import handle_webhook_callback
from apps.sage_intacct.queue import __create_chain_and_run
from apps.workspaces.models import FeatureConfig, Workspace
from tests.test_fyle.fixtures import data


def test_create_chain_and_run(db, mocker):
    """
    Test create_chain_and_run
    """
    mocker.patch('apps.workspaces.models.FeatureConfig.get_feature_config', return_value=False)
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


def test_create_chain_and_run_webhook_sync_enabled(db, mocker):
    """
    Test create_chain_and_run when webhook sync is enabled
    """
    mocker.patch('apps.workspaces.models.FeatureConfig.get_feature_config', return_value=True)
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
    mock_check_interval.assert_not_called()
    mock_task_executor_run.assert_called_once_with(chain_tasks, workspace_id)


def test_handle_webhook_callback(db):
    """
    Test handle_webhook_callback
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

    handle_webhook_callback(body, worksapce.id)


# This test is just for cov :D (2)
def test_handle_webhook_callback_2(db):
    """
    Test handle_webhook_callback_2
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

    handle_webhook_callback(body, worksapce.id)


def test_handle_webhook_callback_ejected_from_report(db):
    """
    Test handle_webhook_callback for EJECTED_FROM_REPORT action
    """
    body = {
        'action': 'EJECTED_FROM_REPORT',
        'resource': 'EXPENSE',
        'data': {
            'id': 'txExpense123',
            'org_id': 'or79Cob97KSh'
        }
    }

    workspace = Workspace.objects.get(id=1)

    handle_webhook_callback(body, workspace.id)


def test_handle_webhook_callback_added_to_report(db):
    """
    Test handle_webhook_callback for ADDED_TO_REPORT action
    """
    body = {
        'action': 'ADDED_TO_REPORT',
        'resource': 'EXPENSE',
        'data': {
            'id': 'txExpense456',
            'org_id': 'or79Cob97KSh',
            'report_id': 'rpReport123'
        }
    }
    workspace = Workspace.objects.get(id=1)
    handle_webhook_callback(body, workspace.id)


def test_handle_webhook_callback_attribute_created(db, add_webhook_attribute_data):
    """
    Test handle_webhook_callback for CATEGORY CREATED action
    """
    workspace = Workspace.objects.get(id=1)
    webhook_body = data['webhook_payloads']['queue_category_created']
    initial_count = ExpenseAttribute.objects.filter(workspace_id=workspace.id, attribute_type='CATEGORY').count()
    handle_webhook_callback(webhook_body, workspace.id)
    final_count = ExpenseAttribute.objects.filter(workspace_id=workspace.id, attribute_type='CATEGORY').count()
    assert final_count == initial_count + 1
    new_category = ExpenseAttribute.objects.get(workspace_id=workspace.id, source_id='cat_travel_789')
    assert new_category.value == 'Travel / Flight'
    assert new_category.active is True


def test_handle_webhook_callback_attribute_updated(db, add_webhook_attribute_data):
    """
    Test handle_webhook_callback for PROJECT UPDATED action
    """
    workspace = Workspace.objects.get(id=1)
    webhook_body = data['webhook_payloads']['queue_project_updated']
    handle_webhook_callback(webhook_body, workspace.id)
    updated_project = ExpenseAttribute.objects.filter(
        workspace_id=workspace.id,
        source_id='proj_webhook_marketing_456'
    ).order_by('-updated_at').first()
    assert updated_project is not None
    assert updated_project.value == 'Webhook Marketing Project Updated'
    assert updated_project.active is True


def test_handle_webhook_callback_attribute_deleted(db, add_webhook_attribute_data):
    """
    Test handle_webhook_callback for CATEGORY DELETED action
    """
    workspace = Workspace.objects.get(id=1)
    webhook_body = data['webhook_payloads']['queue_category_deleted']
    category_before = ExpenseAttribute.objects.filter(
        workspace_id=workspace.id,
        source_id='cat_webhook_food_123'
    ).first()
    assert category_before is not None
    assert category_before.active is True
    handle_webhook_callback(webhook_body, workspace.id)
    category_after = ExpenseAttribute.objects.filter(
        workspace_id=workspace.id,
        source_id='cat_webhook_food_123'
    ).first()
    assert category_after is not None
    assert category_after.active is False


def test_handle_webhook_callback_attribute_webhook_sync_disabled(db, mocker):
    """
    Test handle_webhook_callback when webhook sync is disabled
    """
    workspace = Workspace.objects.get(id=1)
    feature_config = FeatureConfig.objects.get(workspace=workspace)
    feature_config.fyle_webhook_sync_enabled = False
    feature_config.save()
    webhook_body = data['webhook_payloads']['queue_category_created']
    mock_processor = mocker.patch('fyle_integrations_imports.modules.webhook_attributes.WebhookAttributeProcessor.process_webhook')
    handle_webhook_callback(webhook_body, workspace.id)
    mock_processor.assert_not_called()


def test_handle_webhook_callback_attribute_exception(db, add_webhook_attribute_data, mocker):
    """
    Test handle_webhook_callback exception handling for attribute webhooks
    """
    workspace = Workspace.objects.get(id=1)
    webhook_body = data['webhook_payloads']['queue_category_created']
    mock_processor = mocker.patch(
        'fyle_integrations_imports.modules.webhook_attributes.WebhookAttributeProcessor.process_webhook',
        side_effect=Exception('Test exception')
    )
    mock_logger = mocker.patch('apps.fyle.queue.logger')
    handle_webhook_callback(webhook_body, workspace.id)
    mock_processor.assert_called_once()
    mock_logger.error.assert_called_once_with(f'Error processing attribute webhook for workspace {workspace.id}: Test exception')


def test_handle_webhook_callback_org_setting_updated(db, mocker):
    """
    Test handle_webhook_callback for ORG_SETTING UPDATED action
    """
    workspace = Workspace.objects.get(id=1)

    mock_publish = mocker.patch('apps.fyle.queue.publish_to_rabbitmq')

    webhook_body = {
        'action': 'UPDATED',
        'resource': 'ORG_SETTING',
        'data': {
            'regional_settings': {
                'locale': {
                    'date_format': 'DD/MM/YYYY',
                    'timezone': 'Asia/Kolkata'
                }
            }
        }
    }

    handle_webhook_callback(webhook_body, workspace.id)

    mock_publish.assert_called_once()
    call_args = mock_publish.call_args
    payload = call_args[1]['payload']

    assert payload['workspace_id'] == workspace.id
    assert payload['action'] == 'UTILITY.ORG_SETTING_UPDATED'
    assert payload['data']['workspace_id'] == workspace.id
    assert payload['data']['org_settings'] == webhook_body['data']
