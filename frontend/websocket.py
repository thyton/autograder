import socketio
import logging
LOGGER = logging.getLogger(__name__)

class SocketHandler(socketio.AsyncNamespace):
    def __init__(self, mq_client, clients):
        socketio.AsyncNamespace.__init__(self)
        self._mq_client = mq_client
        self._clients = clients

    def on_connect(self, sid, environ):
        LOGGER.info('websocket opened')
        self._clients.append(self)

    def on_disconnect(self, sid):
        LOGGER.info('websocket closed')
        self._clients.remove(self)

    async def on_message(self, sid, message):
        #XXX socket message received from client
        LOGGER.info('received %s', message)
        self._mq_client.publish(message)

