from models.proofing_document import ProofingDocument
from services.pcf_registry_service import PCFRegistryService
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPCFRegistryService(unittest.TestCase):

    def setUp(self):
        self.service = PCFRegistryService(server_address="test-server:50051")

    @patch('services.pcf_registry_service.grpc.insecure_channel')
    def test_download_proof_response_success(self, mock_channel):
        mock_channel_instance = MagicMock()
        mock_channel.return_value.__enter__.return_value = mock_channel_instance

        mock_stub = MagicMock()
        mock_stub_class = MagicMock()
        mock_stub_class.return_value = mock_stub

        with patch('services.pcf_registry_service.json_streaming_pb2_grpc.JsonStreamingServiceStub',
                   return_value=mock_stub):

            mock_chunk1 = MagicMock()
            mock_chunk1.data = b'{"key1":'
            mock_chunk2 = MagicMock()
            mock_chunk2.data = b'"value1"}'
            mock_stub.GetJson.return_value = [mock_chunk1, mock_chunk2]

            mock_temp_file = MagicMock()
            mock_temp_file.__enter__.return_value = mock_temp_file
            mock_temp_file.name = "/tmp/mock_temp_file"

            with patch('tempfile.NamedTemporaryFile', return_value=mock_temp_file):
                with patch('builtins.open', mock_open(read_data='{"key1":"value1"}')):
                    with patch('os.unlink') as mock_unlink:
                        result = self.service.download_proof_response(
                            "test-object-id")

                        self.assertEqual(result, '{"key1":"value1"}')
                        mock_stub.GetJson.assert_called_once()
                        mock_unlink.assert_called_once_with(
                            "/tmp/mock_temp_file")

    @patch('services.pcf_registry_service.grpc.insecure_channel')
    def test_download_proof_response_grpc_error(self, mock_channel):
        mock_channel_instance = MagicMock()
        mock_channel.return_value.__enter__.return_value = mock_channel_instance

        mock_stub = MagicMock()

        with patch('services.pcf_registry_service.json_streaming_pb2_grpc.JsonStreamingServiceStub',
                   return_value=mock_stub):

            from grpc import RpcError
            mock_error = MagicMock(spec=RpcError)
            mock_error.code = MagicMock(return_value="UNAVAILABLE")
            mock_error.details = MagicMock(return_value="Service unavailable")
            mock_stub.GetJson.side_effect = mock_error

            result = self.service.download_proof_response("test-object-id")

            self.assertIsNone(result)
            mock_stub.GetJson.assert_called_once()

    @patch('services.pcf_registry_service.grpc.insecure_channel')
    def test_upload_proof_response_success(self, mock_channel):
        mock_channel_instance = MagicMock()
        mock_channel.return_value.__enter__.return_value = mock_channel_instance

        mock_stub = MagicMock()

        with patch('services.pcf_registry_service.json_streaming_pb2_grpc.JsonStreamingServiceStub',
                   return_value=mock_stub):

            mock_response = MagicMock()
            mock_response.success = True
            mock_response.message = "Upload successful"
            mock_stub.UploadJson.return_value = mock_response

            result = self.service.upload_proof_response(
                "test-object-name", '{"key1":"value1"}')

            self.assertTrue(result)
            mock_stub.UploadJson.assert_called_once()

    @patch('services.pcf_registry_service.grpc.insecure_channel')
    def test_upload_proof_response_failure(self, mock_channel):
        mock_channel_instance = MagicMock()
        mock_channel.return_value.__enter__.return_value = mock_channel_instance
        mock_stub = MagicMock()

        with patch('services.pcf_registry_service.json_streaming_pb2_grpc.JsonStreamingServiceStub',
                   return_value=mock_stub):

            mock_response = MagicMock()
            mock_response.success = False
            mock_response.message = "Upload failed"
            mock_stub.UploadJson.return_value = mock_response

            result = self.service.upload_proof_response(
                "test-object-name", '{"key1":"value1"}')

            self.assertFalse(result)
            mock_stub.UploadJson.assert_called_once()

    @patch('services.pcf_registry_service.grpc.insecure_channel')
    def test_upload_proof_response_grpc_error(self, mock_channel):
        mock_channel_instance = MagicMock()
        mock_channel.return_value.__enter__.return_value = mock_channel_instance
        mock_stub = MagicMock()

        with patch('services.pcf_registry_service.json_streaming_pb2_grpc.JsonStreamingServiceStub',
                   return_value=mock_stub):

            from grpc import RpcError
            mock_error = MagicMock(spec=RpcError)
            mock_error.code = MagicMock(return_value="UNAVAILABLE")
            mock_error.details = MagicMock(return_value="Service unavailable")
            mock_stub.UploadJson.side_effect = mock_error

            result = self.service.upload_proof_response(
                "test-object-name", '{"key1":"value1"}')

            self.assertFalse(result)
            mock_stub.UploadJson.assert_called_once()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"key1":"value1"}')
    def test_upload_proof_response_from_file_success(self, mock_file, mock_exists):
        mock_exists.return_value = True

        with patch.object(self.service, 'upload_proof_response', return_value=True) as mock_upload:
            result = self.service.upload_proof_response_from_file(
                "test-object-name", "/path/to/file.json")

            self.assertTrue(result)
            mock_upload.assert_called_once_with(
                "test-object-name", '{"key1":"value1"}')

    @patch('os.path.exists')
    def test_upload_proof_response_from_file_not_found(self, mock_exists):
        mock_exists.return_value = False

        result = self.service.upload_proof_response_from_file(
            "test-object-name", "/path/to/nonexistent.json")

        self.assertFalse(result)

    def test_upload_proofing_document(self):
        from models.product_footprint import ProductFootprint

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

        proofing_document = ProofingDocument(
            productFootprint=product_footprint,
            tocData=[],
            hocData=[]
        )

        with patch.object(self.service, 'upload_proof_response', return_value=True) as mock_upload:
            result = self.service.upload_proofing_document(
                "test-object-name", proofing_document)

            self.assertTrue(result)
            mock_upload.assert_called_once()
            args = mock_upload.call_args[0]
            self.assertEqual(args[0], "test-object-name")
            self.assertIn("test-id", args[1])


if __name__ == '__main__':
    unittest.main()
