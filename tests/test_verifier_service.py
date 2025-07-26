from models.proofing_document import ProofResponse
from services.verifier_service import ReceiptVerifierService
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import json
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestReceiptVerifierService(unittest.TestCase):

    def setUp(self):
        self.pcf_registry_patcher = patch(
            'services.verifier_service.PCFRegistryService')
        self.mock_pcf_registry = self.pcf_registry_patcher.start()
        self.verifier_service = ReceiptVerifierService()

        self.verifier_service.pcf_registry_service = self.mock_pcf_registry.return_value

    def tearDown(self):
        self.pcf_registry_patcher.stop()

    @patch('services.verifier_service.aio.insecure_channel')
    @patch('services.verifier_service.receipt_verifier_pb2_grpc.ReceiptVerifierServiceStub')
    def test_verify_receipt_stream_success(self, mock_stub_class, mock_channel):
        mock_channel_instance = AsyncMock()
        mock_channel.return_value.__aenter__.return_value = mock_channel_instance

        mock_stub = MagicMock()
        mock_stub_class.return_value = mock_stub

        mock_response = MagicMock()
        mock_response.valid = True
        mock_response.message = "Verification successful"

        mock_stub.VerifyReceiptStream = AsyncMock(return_value=mock_response)

        proof_response = ProofResponse(
            productFootprintId="test-id-123",
            proofReceipt="test-receipt-data",
            proofReference="test-reference",
            pcf=10.5,
            imageId="test-image-id"
        )

        # Call the method under test
        result = asyncio.run(
            self.verifier_service.VerifyReceiptStream(proof_response))

        # Assertions
        self.assertEqual(result, "Verification successful")
        mock_stub.VerifyReceiptStream.assert_called_once()

        call_args = mock_stub.VerifyReceiptStream.call_args[0][0]
        chunks = list(call_args)

        data_bytes = b''.join(chunk.data for chunk in chunks)
        data = json.loads(data_bytes.decode('utf-8'))

        self.assertEqual(data['receipt'], "test-receipt-data")
        self.assertEqual(data['image_id'], "test-image-id")

    def test_verify_receipt_stream_grpc_error(self):

        proof_response = ProofResponse(
            productFootprintId="test-id-123",
            proofReceipt="test-receipt-data",
            proofReference="test-reference",
            pcf=10.5,
            imageId="test-image-id"
        )

        original_method = self.verifier_service.VerifyReceiptStream

        async def mock_verify_receipt_stream(proof_response):
            return "gRPC Error: Service unavailable"

        self.verifier_service.VerifyReceiptStream = mock_verify_receipt_stream

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.verifier_service.VerifyReceiptStream(proof_response))
            loop.close()

            self.assertEqual(result, "gRPC Error: Service unavailable")
        finally:
            self.verifier_service.VerifyReceiptStream = original_method

    def test_verify_receipt_stream_no_data(self):
        original_method = self.verifier_service.VerifyReceiptStream

        async def mock_verify_receipt_stream(proof_response):
            return "No proof response file found or invalid file path."

        self.verifier_service.VerifyReceiptStream = mock_verify_receipt_stream

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.verifier_service.VerifyReceiptStream(None))
            loop.close()

            self.assertEqual(
                result, "No proof response file found or invalid file path.")
        finally:
            self.verifier_service.VerifyReceiptStream = original_method


if __name__ == '__main__':
    unittest.main()
