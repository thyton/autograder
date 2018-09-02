import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('mq'))
channel = connection.channel()

channel.queue_declare(queue='hello')

channel.basic_publish(exchange='', routing_key='hello', body='Hello')
print('sent hello')
connection.close()
