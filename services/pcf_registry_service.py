import grpc
import os
import tempfile
import services.pb.json_streaming_pb2 as json_streaming_pb2
import services.pb.json_streaming_pb2_grpc as json_streaming_pb2_grpc

from typing import Optional
from models.proofing_document import ProofingDocument
from config.settings import PCF_REGISTRY_SERVER_ADDRESS
from utils.logging_utils import log_service_call


class PCFRegistryService:
    """Service for downloading proof response files from a remote PCF registry."""

    CHUNK_SIZE = 4096

    def __init__(self, server_address: str = PCF_REGISTRY_SERVER_ADDRESS):
        self.server_address = server_address

    def download_proof_response(self, object_id: str) -> Optional[str]:
        log_service_call("PCFRegistryService", "download_proof_response")
        print(f"Downloading proof response with ID: {object_id}")

        try:
            with grpc.insecure_channel(self.server_address) as channel:
                stub = json_streaming_pb2_grpc.JsonStreamingServiceStub(
                    channel)
                print(f"Connected to gRPC server: {self.server_address}")

                request = json_streaming_pb2.GetRequest(message=object_id)

                with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
                    temp_path = temp_file.name
                    response_iterator = stub.GetJson(request)

                    for chunk in response_iterator:
                        temp_file.write(chunk.data)

                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                os.unlink(temp_path)

                print(f"Successfully downloaded proof response file: {object_id}")
                return content

        except grpc.RpcError as e:
            print(f"gRPC error occurred during download: {e.code()} - {e.details()}")
            return None
        except Exception as e:
            print(f"Error downloading proof response file: {e}")
            return None

    def _generate_chunks(self, file_content: str, object_name: str):
        try:
            content_bytes = file_content.encode('utf-8')

            # Create chunks
            for i in range(0, len(content_bytes), self.CHUNK_SIZE):
                chunk = content_bytes[i:i + self.CHUNK_SIZE]
                yield json_streaming_pb2.JsonChunk(data=chunk)

            print(f"Finished preparing file '{object_name}' for streaming.")
        except Exception as e:
            print(f"Error generating chunks for '{object_name}': {e}")
            return

    def upload_proof_response(self, object_name: str, file_content: str) -> bool:
        log_service_call("PCFRegistryService", "upload_proof_response")

        if not json_streaming_pb2 or not json_streaming_pb2_grpc:
            print("Warning: gRPC proto files not available, cannot upload")
            return False

        try:
            with grpc.insecure_channel(self.server_address) as channel:
                stub = json_streaming_pb2_grpc.JsonStreamingServiceStub(
                    channel)

                metadata = [('filename', object_name)]
                chunk_generator = self._generate_chunks(
                    file_content, object_name)

                response = stub.UploadJson(chunk_generator, metadata=metadata)

                if response.success:
                    print(f"PCF Registry response: {response.message}")
                    return True
                else:
                    print(f"PCF Registry response: {response.message}")
                    return False

        except grpc.RpcError as e:
            print(f"gRPC error occurred during upload: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            print(f"Error uploading proof response file: {e}")
            return False

    def upload_proof_response_from_file(self, object_name: str, file_path: str) -> bool:
        if not os.path.exists(file_path):
            print(f"File not found at: {file_path}")
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            return self.upload_proof_response(object_name, file_content)

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return False

    def upload_proofing_document(self, object_name: str, proofing_document: ProofingDocument) -> bool:
        try:
            json_content = proofing_document.model_dump_json(indent=2)
            return self.upload_proof_response(object_name, json_content)

        except Exception as e:
            print(f"Error serializing proofing document: {e}")
            return False
