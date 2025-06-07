import unittest

from models.proofing_document import ProofingDocument, ProofResponse
from utils.kafka import send_message_to_kafka, consume_messages_from_kafka


class kafka_communication_test(unittest.TestCase):
    def test_from_json_file(self):
        filename = "data/proof_documents_examples/shipment_3.json"
        content = None
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
        except FileNotFoundError:
            print("Fehler: Die Datei 'meine_datei.txt' wurde nicht gefunden.")
        except IOError as e:
            print(f"Ein Fehler beim Lesen der Datei ist aufgetreten: {e}")

        proofing_document = ProofingDocument.model_validate_json(content)

        topic_out = "shipments"
        topic_in = "pcf-results"

        message_to_send = proofing_document.model_dump_json()
        send_message_to_kafka(topic_out, message_to_send)
        msg = consume_messages_from_kafka(topic_in)

        print(msg)

        proof_response = ProofResponse.model_validate_json(msg)

        self.assertEqual(proof_response.proofReference, "123")
