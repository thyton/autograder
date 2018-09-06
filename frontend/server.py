import tornado.ioloop
import tornado.web
from threading import Thread
import socketio
import asyncio
import logging

from mq import MQConsumer
from websocket import SocketHandler

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

LOGGER = logging.getLogger(__name__)

clients = []


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('templates/index.html')


mq_client = MQConsumer('mq', clients)

sio = socketio.AsyncServer(async_mode='tornado')
sio.register_namespace(SocketHandler(mq_client, clients))

application = tornado.web.Application([
    (r'/socket.io/', socketio.get_tornado_handler(sio)),
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
    mq_thread = Thread(target=mq_client.run)
    mq_thread.start()

    print('starting tornado')
    tornado_thread = Thread(target=start_tornado)
    tornado_thread.start()

    input('server running, press enter to exit')

    stop_tornado()
    #mq_disconnect()
    mq_client.stop()

