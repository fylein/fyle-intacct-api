import os
import json
import signal

from consumer.event_consumer import EventConsumer
from common.event import BaseEvent
from common import log
from common.qconnector import RabbitMQConnector

from .sync import sync_dimensions


logger = log.get_logger(__name__)


class MaintenanceWorker(EventConsumer):
    def __init__(self, *, qconnector_cls, **kwargs):
        super().__init__(qconnector_cls=qconnector_cls, event_cls=None, **kwargs)

    def process_message(self, _, payload_dict):
        try:
            sync_dimensions(payload_dict['workspace_id'])
        except Exception as e:
            logger.info('Error while syncing dimensions for workspace - %s, error: %s', payload_dict, str(e))

    def start_consuming(self):
        def stream_consumer(routing_key, payload):
            payload_dict = json.loads(payload)

            self.process_message(routing_key, payload_dict)
            self.check_shutdown()

        self.qconnector.consume_stream(
            callback_fn=stream_consumer
        )

    def shutdown(self, signum=None, frame=None):
        """Override shutdown to handle signal arguments"""
        super().shutdown()

def consume():
    rabbitmq_url = os.environ.get('RABBITMQ_URL')
    rabbitmq_exchange = os.environ.get('RABBITMQ_EXCHANGE')

    maintenance_worker = MaintenanceWorker(
        rabbitmq_url=rabbitmq_url,
        rabbitmq_exchange=rabbitmq_exchange,
        queue_name='maintenance_queue',
        binding_keys='maintenance.#',
        qconnector_cls=RabbitMQConnector
    )

    signal.signal(signal.SIGTERM, maintenance_worker.shutdown)
    signal.signal(signal.SIGINT, maintenance_worker.shutdown)

    maintenance_worker.connect()
    maintenance_worker.start_consuming()


if __name__ == "__main__":
    consume()
