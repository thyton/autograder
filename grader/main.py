import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq'))
channel = connection.channel()

channel.exchange_declare('grader', 'topic')

channel.queue_declare(queue='grader')
channel.queue_bind(queue='grader', exchange='grader')

def callback(ch, method, props, body):
    print('received', body)
    print('repsponding to', props.reply_to)
    #XXX received something for grading, do something and reply
    ch.basic_publish(exchange='grader',
                     routing_key=props.reply_to,
                     body='done')
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue='grader')

print('awaiting messages')
channel.start_consuming()

