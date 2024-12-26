import os
import json

from common.qconnector import QConnector
from common.qconnector import RabbitMQConnector


class RabbitMQ(RabbitMQConnector):
    def __init__(self):
        rabbitmq_url = os.environ.get('RABBITMQ_URL')
        rabbitmq_exchange = os.environ.get('RABBITMQ_EXCHANGE')

        self.qconnector: QConnector = RabbitMQConnector(rabbitmq_url, rabbitmq_exchange)
        self.qconnector.connect()

    def publish(self, routing_key, body):
        self.qconnector.publish(routing_key, json.dumps(body))
