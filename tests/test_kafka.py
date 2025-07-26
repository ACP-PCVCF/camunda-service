from utils.kafka import send_message_to_kafka, consume_messages_from_kafka, delivery_report
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKafka(unittest.TestCase):

    @patch('utils.kafka.Producer')
    def test_send_message_to_kafka(self, mock_producer_class):
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        send_message_to_kafka("test-topic", "test-message",
                              "test-bootstrap-server")

        mock_producer_class.assert_called_once_with({
            'bootstrap.servers': 'test-bootstrap-server',
            'message.max.bytes': 52428800,
            'receive.message.max.bytes': 52428800,
            'compression.type': 'snappy',
            'batch.size': 65536,
            'linger.ms': 100
        })

        mock_producer.produce.assert_called_once()
        args, kwargs = mock_producer.produce.call_args
        self.assertEqual(args[0], "test-topic")
        self.assertEqual(kwargs["key"], "my_key")
        self.assertEqual(kwargs["value"], b"test-message")
        self.assertEqual(kwargs["callback"], delivery_report)

        mock_producer.flush.assert_called_once()

    @patch('utils.kafka.Producer')
    def test_send_message_to_kafka_exception(self, mock_producer_class):
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        mock_producer.produce.side_effect = Exception("Test exception")

        send_message_to_kafka("test-topic", "test-message")

        mock_producer.produce.assert_called_once()
        mock_producer.flush.assert_not_called()

    @patch('utils.kafka.Consumer')
    def test_consume_messages_from_kafka(self, mock_consumer_class):
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = b'test-message'
        mock_message.topic.return_value = 'test-topic'
        mock_message.partition.return_value = 0
        mock_message.offset.return_value = 42

        mock_consumer.poll.return_value = mock_message

        result = consume_messages_from_kafka(
            "test-topic", "test-bootstrap-server", "test-group")

        mock_consumer_class.assert_called_once_with({
            'bootstrap.servers': 'test-bootstrap-server',
            'group.id': 'test-group',
            'auto.offset.reset': 'latest',
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 5000,
            'max.partition.fetch.bytes': 52428800,
            'fetch.max.bytes': 52428800
        })

        mock_consumer.subscribe.assert_called_once_with(["test-topic"])
        mock_consumer.poll.assert_called_once_with(timeout=1.0)
        mock_message.error.assert_called_once()
        mock_consumer.commit.assert_called_once_with(asynchronous=False)
        mock_consumer.close.assert_called_once()

        self.assertEqual(result, "test-message")

    @patch('utils.kafka.Consumer')
    def test_consume_messages_from_kafka_partition_eof(self, mock_consumer_class):
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        from confluent_kafka import KafkaError
        mock_error = MagicMock()
        mock_error.code.return_value = KafkaError._PARTITION_EOF

        mock_message = MagicMock()
        mock_message.error.return_value = mock_error
        mock_message.topic.return_value = 'test-topic'
        mock_message.partition.return_value = 0
        mock_message.offset.return_value = 42

        mock_message2 = MagicMock()
        mock_message2.error.return_value = None
        mock_message2.value.return_value = b'test-message'
        mock_message2.topic.return_value = 'test-topic'
        mock_message2.partition.return_value = 0
        mock_message2.offset.return_value = 43

        mock_consumer.poll.side_effect = [mock_message, mock_message2]

        result = consume_messages_from_kafka("test-topic")

        mock_consumer.poll.assert_has_calls(
            [call(timeout=1.0), call(timeout=1.0)])
        self.assertTrue(mock_message.error.called)
        self.assertTrue(mock_message2.error.called)
        mock_consumer.commit.assert_called_once_with(asynchronous=False)
        mock_consumer.close.assert_called_once()

        self.assertEqual(result, "test-message")

    @patch('utils.kafka.Consumer')
    def test_consume_messages_from_kafka_error(self, mock_consumer_class):
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        from confluent_kafka import KafkaError, KafkaException
        mock_error = MagicMock()
        mock_error.code.return_value = KafkaError.UNKNOWN_TOPIC_OR_PART

        mock_message = MagicMock()
        mock_message.error.return_value = mock_error
        mock_message.topic.return_value = 'test-topic'
        mock_message.partition.return_value = 0

        mock_consumer.poll.return_value = mock_message

        with self.assertRaises(KafkaException):
            consume_messages_from_kafka("test-topic")

        mock_consumer.poll.assert_called_once_with(timeout=1.0)
        self.assertTrue(mock_message.error.called)
        mock_consumer.close.assert_called_once()

    def test_delivery_report_success(self):
        mock_message = MagicMock()
        mock_message.topic.return_value = 'test-topic'
        mock_message.partition.return_value = 0

        with patch('builtins.print') as mock_print:
            delivery_report(None, mock_message)

            mock_print.assert_called_once()
            self.assertIn("delivered successfully", mock_print.call_args[0][0])

    def test_delivery_report_error(self):
        mock_message = MagicMock()

        with patch('builtins.print') as mock_print:
            delivery_report("Test error", mock_message)

            mock_print.assert_called_once()
            self.assertIn("delivery failed", mock_print.call_args[0][0])
            self.assertIn("Test error", mock_print.call_args[0][0])


if __name__ == '__main__':
    unittest.main()
