from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import pika
from threading import Thread

app = Flask(__name__)
socketio = SocketIO(app)

connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='mq',
            heartbeat=300
            ))
channel = connection.channel()
queue_declare_result = channel.queue_declare(exclusive=True)
callback_queue = queue_declare_result.method.queue

print('callback queue:', callback_queue)

def response(ch, method, props, body):
    print('response')
    with app.app_context():
        emit('response', body)

channel.basic_consume(response, no_ack=True, queue=callback_queue)
t = Thread(target=channel.start_consuming)
t.start()

@socketio.on('message')
def handle_message(message):
    channel.basic_publish(
            exchange='',
            routing_key='grader',
            properties=pika.BasicProperties(reply_to=callback_queue),
            body=message)

@app.route("/")
def hello():
    return render_template('index.html')

