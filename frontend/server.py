import tornado.ioloop
import tornado.web
import tornado.websocket
import pika
from threading import Thread
import asyncio
import logging

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

LOGGER = logging.getLogger(__name__)

clients = []


class MQConsumer(object):
    #EXCHANGE = 'message'
    #EXCHANGE_TYPE = 'topic'
    #QUEUE = 'text'
    #ROUTING_KEY = 'example.text'

    def __init__(self, host):
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._host = host

    def on_message(self, unused_channel, basic_deliver, properties, body):
        LOGGER.info('Received message # %s from %s: %s',
                    basic_deliver.delivery_tag, properties.app_id, body)
        #XXX message received from queue
        for client in clients:
            client.write_message(body)

        self.acknowledge_message(basic_deliver.delivery_tag)

    def publish(self, message):
        print('sending', message)
        self._channel.basic_publish(
            exchange=self._exchange,
            routing_key='grader',
            properties=pika.BasicProperties(reply_to=self._callback_queue),
            body=message)


    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())

        self._connection = self.connect()

        #self._connection = self.connect()
        self._connection.ioloop.start()

    def connect(self):
        LOGGER.info('Connecting to %s', self._host)
        return pika.adapters.TornadoConnection(
                pika.ConnectionParameters(host=self._host),
                self.on_connection_open)

    def on_connection_open(self, unused_connection):
        LOGGER.info('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        LOGGER.info('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s',
                           reply_code, reply_text)
            self._connection.add_timeout(5, self.reconnect)

    def open_channel(self):
        LOGGER.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        LOGGER.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange('grader')

    def add_on_channel_close_callback(self):
        LOGGER.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        LOGGER.warning('Channel %i was closed: (%s) %s',
                       channel, reply_code, reply_text)
        self._connection.close()

    def setup_exchange(self, exchange_name):
        LOGGER.info('Declaring exchange %s', exchange_name)
        self._exchange = exchange_name
        self._channel.exchange_declare(self.on_exchange_declareok,
                                       exchange_name,
                                       'topic')

    def on_exchange_declareok(self, unused_frame):
        LOGGER.info('Exchange declared')
        self.setup_queue()

    def setup_queue(self, queue_name=''):
        LOGGER.info('Declaring queue %s', queue_name)
        self._channel.queue_declare(self.on_queue_declareok, queue_name, exclusive=True)
        #queue_declare_result = self._channel.queue_declare(exclusive=True)
        #self._callback_queue = queue_declare_result.method.queue


    def on_queue_declareok(self, method_frame):
        #LOGGER.info('Binding %s to %s with %s',
                    #self.EXCHANGE, self.QUEUE, self.ROUTING_KEY)
        #self._channel.queue_bind(self.on_bindok, self.QUEUE,
                                 #self.EXCHANGE, self.ROUTING_KEY)
        print(method_frame)
        self._callback_queue = method_frame.method.queue
        LOGGER.info('Binding to %s', self._callback_queue)
        self._channel.queue_bind(self.on_bindok, queue=self._callback_queue, exchange=self._exchange)

    def on_bindok(self, unused_frame):
        LOGGER.info('Queue bound')
        self.start_consuming()

    def start_consuming(self):
        LOGGER.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(
                self.on_message,
                self._callback_queue,
                no_ack=True)

    def stop(self):
        LOGGER.info('Stopping')
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.stop()
        LOGGER.info('Stopped')

    def stop_consuming(self):
        if self._channel:
            LOGGER.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self, unused_frame):
        LOGGER.info('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel()

    def close_channel(self):
        LOGGER.info('Closing the channel')
        self._channel.close()

    def reconnect(self):
        """Will be invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.

        """
        if not self._closing:

            # Create a new connection
            self._connection = self.connect()

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        LOGGER.info('Closing connection')
        self._connection.close()

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        LOGGER.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        LOGGER.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        if self._channel:
            self._channel.close()

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        LOGGER.info('Acknowledging message %s', delivery_tag)
        self._channel.basic_ack(delivery_tag)


'''
connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='mq'))
channel = connection.channel()
queue_declare_result = channel.queue_declare(exclusive=True)
callback_queue = queue_declare_result.method.queue

print('callback queue:', callback_queue)
'''

def response(ch, method, props, body):
    print('response')
    for client in clients:
        client.write_message(body)

def mq_connect():
    asyncio.set_event_loop(asyncio.new_event_loop())
    print('mq listening')
    channel.basic_consume(response, no_ack=True, queue=callback_queue)
    channel.start_consuming()

def mq_disconnect():
    channel.stop_consuming()
    connection.close()
    print('mq disconnected')

class SocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print('websocket opened')
        clients.append(self)

    def on_close(self):
        print('websocket closed')
        clients.remove(self)

    def on_message(self, message):
        #XXX socket message received from client
        print('received', message)
        mq_client.publish(message)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('templates/index.html')


application = tornado.web.Application([
    (r'/ws', SocketHandler),
    (r'/', MainHandler),
])

def start_tornado():
    asyncio.set_event_loop(asyncio.new_event_loop())
    application.listen(5000)
    tornado.ioloop.IOLoop.instance().start()

def stop_tornado():
    tornado.ioloop.IOLoop.instance().stop()


if __name__ == '__main__':
    print('starting mq')
    mq_client = MQConsumer('mq')
    mq_thread = Thread(target=mq_client.run)
    mq_thread.start()

    print('starting tornado')
    tornado_thread = Thread(target=start_tornado)
    tornado_thread.start()

    input('server running, press enter to exit')

    stop_tornado()
    #mq_disconnect()
    mq_client.stop()

