import pytest
from unittest import mock
from apps.sage_intacct.queue import trigger_sync_payments
from workers.helpers import WorkerActionEnum


@pytest.mark.django_db
@mock.patch('apps.sage_intacct.queue.publish_to_rabbitmq')
@mock.patch('apps.workspaces.models.Configuration.objects.get')
@mock.patch('apps.mappings.models.GeneralMapping.objects.filter')
def test_trigger_sync_payments(
    mock_general_mapping_filter,
    mock_configuration_get,
    mock_publish_to_rabbitmq
):
    workspace_id = 1
    # Mock configuration and general_mappings
    mock_config = mock.Mock()
    mock_config.sync_fyle_to_sage_intacct_payments = True
    mock_config.sync_sage_intacct_to_fyle_payments = True
    mock_config.reimbursable_expenses_object = 'BILL'
    mock_configuration_get.return_value = mock_config

    mock_general_mapping = mock.Mock()
    mock_general_mapping.payment_account_id = 123
    mock_general_mapping_filter.return_value.first.return_value = mock_general_mapping

    # Call function
    trigger_sync_payments(workspace_id)

    # Should publish CREATE_AP_PAYMENT and CHECK_SAGE_INTACCT_OBJECT_STATUS and PROCESS_FYLE_REIMBURSEMENTS
    assert mock_publish_to_rabbitmq.call_count == 3
    payloads = [call[1]['payload'] if 'payload' in call[1] else None for call in mock_publish_to_rabbitmq.call_args_list]
    actions = [p['action'] for p in payloads if p]
    assert WorkerActionEnum.CREATE_AP_PAYMENT.value in actions
    assert WorkerActionEnum.CHECK_SAGE_INTACCT_OBJECT_STATUS.value in actions
    assert WorkerActionEnum.PROCESS_FYLE_REIMBURSEMENTS.value in actions

    # Test with reimbursable_expenses_object = 'EXPENSE_REPORT'
    mock_config.reimbursable_expenses_object = 'EXPENSE_REPORT'
    trigger_sync_payments(workspace_id)
    payloads = [call[1]['payload'] if 'payload' in call[1] else None for call in mock_publish_to_rabbitmq.call_args_list]
    actions = [p['action'] for p in payloads if p]
    assert WorkerActionEnum.CREATE_SAGE_INTACCT_REIMBURSEMENT.value in actions
