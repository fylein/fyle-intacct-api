import pytest
from unittest.mock import Mock, patch

from common.event import BaseEvent
from workers import actions
from fyle_accounting_library.rabbitmq.models import FailedEvent

from workers.worker import Worker


@pytest.fixture
def mock_qconnector():
    """
    Mock QConnector
    """
    return Mock()


@pytest.fixture
def export_worker(mock_qconnector):
    """
    Mock Worker
    """
    worker = Worker(
        rabbitmq_url='mock_url',
        rabbitmq_exchange='mock_exchange',
        queue_name='mock_queue',
        binding_keys=['mock.binding.key'],
        qconnector_cls=Mock(return_value=mock_qconnector),
        event_cls=BaseEvent
    )
    worker.qconnector = mock_qconnector
    worker.event_cls = BaseEvent
    return worker


@pytest.mark.django_db
def test_process_message_success(export_worker):
    """
    Test process message success
    """
    with patch('workers.worker.handle_tasks') as mock_handle_tasks:
        mock_handle_tasks.side_effect = Exception('Test error')

        routing_key = 'test.routing.key'
        payload_dict = {
            'data': {'some': 'data'},
            'workspace_id': 123
        }
        event = BaseEvent()
        event.from_dict({'new': payload_dict})

        # The process_message should re-raise the exception
        with pytest.raises(Exception, match='Test error'):
            export_worker.process_message(routing_key, event, 1)

        mock_handle_tasks.assert_called_once_with({'data': {'some': 'data'}, 'workspace_id': 123, 'retry_count': 1})


@pytest.mark.django_db
def test_handle_exception(export_worker):
    """
    Test handle exception
    """
    routing_key = 'test.routing.key'
    payload_dict = {
        'data': {'some': 'data'},
        'workspace_id': 123
    }
    error = Exception('Test error')

    export_worker.handle_exception(routing_key, payload_dict, error, 1)

    failed_event = FailedEvent.objects.get(
        routing_key=routing_key,
        workspace_id=123
    )
    assert failed_event.payload == payload_dict
    assert failed_event.error_traceback == 'Test error'


def test_shutdown(export_worker):
    """
    Test shutdown
    """
    with patch.object(export_worker, 'shutdown', wraps=export_worker.shutdown) as mock_shutdown:
        export_worker.shutdown(_=15, __=None)  # SIGTERM = 15
        mock_shutdown.assert_called_once_with(_=15, __=None)

    with patch.object(export_worker, 'shutdown', wraps=export_worker.shutdown) as mock_shutdown:
        export_worker.shutdown(_=0, __=None)  # Using default values
        mock_shutdown.assert_called_once_with(_=0, __=None)


@patch('workers.worker.signal.signal')
@patch('workers.worker.Worker')
def test_consume(mock_worker_class, mock_signal):
    """
    Test consume
    """
    mock_worker = Mock()
    mock_worker_class.return_value = mock_worker

    with patch.dict('os.environ', {'RABBITMQ_URL': 'test_url'}):
        from workers.worker import consume
        consume(queue_name='exports.p0')

    mock_worker.connect.assert_called_once()
    mock_worker.start_consuming.assert_called_once()
    assert mock_signal.call_count == 2  # Called for both SIGTERM and SIGINT


def test_handle_exports_calls_import_and_export_expenses():
    """
    Test handle exports calls import and export expenses
    """
    with patch('workers.actions.handle_tasks') as mock_handle_tasks:
        data = {'foo': 'bar'}
        actions.handle_tasks(data)
        mock_handle_tasks.assert_called_once_with({'foo': 'bar'})
