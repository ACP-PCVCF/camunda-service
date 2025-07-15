from confluent_kafka import Producer
from confluent_kafka import Consumer, KafkaException, KafkaError
from config.settings import KAFKA_BOOTSTRAP_SERVERS

import sys


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def send_message_to_kafka(topic_name, message, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS):
    conf = {
        'bootstrap.servers': bootstrap_servers,
        'message.max.bytes': 52428800,
        'receive.message.max.bytes': 52428800,
        'compression.type': 'snappy',
        'batch.size': 65536,
        'linger.ms': 100
    }
    producer = Producer(conf)

    try:
        producer.produce(topic_name, key="my_key", value=message.encode(
            'utf-8'), callback=delivery_report)
        producer.flush()  # Wait for all messages in the producer queue to be delivered
    except Exception as e:
        print(f"Error producing message: {e}")


def consume_messages_from_kafka(topic_name, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id='my_python_consumer_group') -> str:
    conf = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'latest',
        'enable.auto.commit': True,
        'auto.commit.interval.ms': 5000,
        'max.partition.fetch.bytes': 52428800,
        'fetch.max.bytes': 52428800
    }

    consumer = Consumer(conf)

    try:
        consumer.subscribe([topic_name])
        while True:
            # Poll for messages, with a 1-second timeout
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event - not an error
                    sys.stderr.write(
                        f'%% {msg.topic()} [{msg.partition()}] reached end offset {msg.offset()}\n')
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                # Message successfully received
                print(
                    f"Received message from Kafka: Topic={msg.topic()}, Partition={msg.partition()}, Offset={msg.offset()}")
                print(
                    f"Key: {msg.key().decode('utf-8') if msg.key() else 'N/A'}")
                consumer.commit(asynchronous=False)
                return msg.value().decode('utf-8')

    except KeyboardInterrupt:
        sys.stderr.write('%% Aborted by user\n')
    finally:
        consumer.close()
