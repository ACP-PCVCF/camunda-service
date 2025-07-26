from models.product_footprint import ProductFootprint
from models.proofing_document import ProofingDocument, ProofResponse
from services.proving_service import ProofingService
import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProofingService(unittest.TestCase):

    def setUp(self):
        self.pcf_registry_patcher = patch(
            'services.proving_service.PCFRegistryService')
        self.mock_pcf_registry = self.pcf_registry_patcher.start()

        self.service = ProofingService(
            topic_out="test-topic-out", topic_in="test-topic-in")

        self.service.pcf_registry_service = self.mock_pcf_registry.return_value

    def tearDown(self):
        self.pcf_registry_patcher.stop()

    def _create_test_proofing_document(self):
        product_footprint = ProductFootprint(
            id="test-id",
            created="2023-01-01T00:00:00Z",
            companyName="Test Company",
            companyIds=["company-id-1"],
            productDescription="Test Product",
            productIds=["product-id-1"],
            productCategoryCpc=123,
            productNameCompany="Test Product Name"
        )

        return {
            "productFootprint": product_footprint.model_dump(),
            "tocData": [],
            "hocData": []
        }

    def _create_test_proof_response(self):
        return ProofResponse(
            productFootprintId="test-id",
            proofReceipt="test-receipt-data",
            proofReference="test-reference",
            pcf=10.5,
            imageId="test-image-id"
        )

    @patch('services.proving_service.send_message_to_kafka')
    def test_send_proofing_document_without_proof(self, mock_send_kafka):
        proofing_document = self._create_test_proofing_document()

        self.service.send_proofing_document(proofing_document, None)

        mock_send_kafka.assert_called_once()
        self.assertEqual(mock_send_kafka.call_args[0][0], "test-topic-out")
        message = mock_send_kafka.call_args[0][1]
        parsed_message = json.loads(message)
        self.assertEqual(parsed_message["productFootprint"]["id"], "test-id")
        self.assertEqual(len(parsed_message["proof"]), 0)

    @patch('services.proving_service.send_message_to_kafka')
    def test_send_proofing_document_with_proof(self, mock_send_kafka):
        proofing_document = self._create_test_proofing_document()
        proof_response = self._create_test_proof_response()

        self.service.send_proofing_document(proofing_document, proof_response)

        mock_send_kafka.assert_called_once()
        self.assertEqual(mock_send_kafka.call_args[0][0], "test-topic-out")
        message = mock_send_kafka.call_args[0][1]
        parsed_message = json.loads(message)
        self.assertEqual(parsed_message["productFootprint"]["id"], "test-id")
        self.assertEqual(len(parsed_message["proof"]), 1)
        self.assertEqual(parsed_message["proof"]
                         [0]["productFootprintId"], "test-id")
        self.assertEqual(parsed_message["proof"]
                         [0]["proofReceipt"], "test-receipt-data")

    @patch('services.proving_service.consume_messages_from_kafka')
    def test_receive_proof_response(self, mock_consume_kafka):
        proof_response = self._create_test_proof_response()

        mock_consume_kafka.return_value = proof_response.model_dump_json()

        result = self.service.receive_proof_response()

        mock_consume_kafka.assert_called_once_with("test-topic-in")
        self.mock_pcf_registry.return_value.upload_proofing_document.assert_called_once()

        self.assertEqual(result.productFootprintId, "test-id")
        self.assertEqual(result.proofReceipt, "test-receipt-data")
        self.assertEqual(result.proofReference, "test-reference")
        self.assertEqual(result.pcf, 10.5)
        self.assertEqual(result.imageId, "test-image-id")


if __name__ == '__main__':
    unittest.main()
