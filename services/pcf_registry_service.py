import grpc
import json
import os
import tempfile
from typing import Optional
from models.proofing_document import ProofResponse, ProofingDocument
import services.pb.json_streaming_pb2 as json_streaming_pb2
import services.pb.json_streaming_pb2_grpc as json_streaming_pb2_grpc


from config.settings import PCF_REGISTRY_SERVER_ADDRESS
from utils.logging_utils import log_service_call


class PCFRegistryService:
    """Service for downloading proof response files from a remote PCF registry."""

    # Chunk size for file uploads (4KB)
    CHUNK_SIZE = 4096

    def __init__(self, server_address: str = None):
        """
        Initialize the PCF Registry Service.

        Args:
            server_address: gRPC server address for the PCF registry
        """
        self.server_address = server_address or getattr(
            __import__('config.settings', fromlist=[
                       'PCF_REGISTRY_SERVER_ADDRESS']),
            'PCF_REGISTRY_SERVER_ADDRESS',
            'localhost:50052'
        )

    def download_proof_response(self, object_id: str) -> Optional[str]:
        """
        Downloads a proof response file from the server using server-side streaming RPC.

        Args:
            object_id: The ID of the proof response file to download

        Returns:
            The file content as string if successful, None otherwise
        """
        log_service_call("PCFRegistryService", "download_proof_response")

        if not json_streaming_pb2 or not json_streaming_pb2_grpc:
            print("Warning: gRPC proto files not available, using fallback method")
            return self._fallback_download(object_id)

        print(f"Downloading proof response file: {object_id}")
        print(f"Using PCF Registry server address: {self.server_address}")

        try:
            with grpc.insecure_channel(self.server_address) as channel:
                stub = json_streaming_pb2_grpc.JsonStreamingServiceStub(
                    channel)

                # Create request
                request = json_streaming_pb2.GetRequest(message=object_id)

                # Create temporary file to store downloaded content
                with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
                    temp_path = temp_file.name

                    # Download file chunks
                    response_iterator = stub.GetJson(request)

                    for chunk in response_iterator:
                        temp_file.write(chunk.data)

                # Read the downloaded content
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Clean up temporary file
                os.unlink(temp_path)

                print(
                    f"Successfully downloaded proof response file: {object_id}")
                return content

        except grpc.RpcError as e:
            print(
                f"gRPC error occurred during download: {e.code()} - {e.details()}")
            return None
        except Exception as e:
            print(f"Error downloading proof response file: {e}")
            return None

    def get_and_append_proof_response(self, proofing_document: ProofingDocument,
                                      proof_response_id: str) -> ProofingDocument:
        """
        Downloads a proof response file and appends it to the proofing document if available.

        Args:
            proofing_document: The proofing document to append to
            proof_response_id: The ID of the proof response file to download

        Returns:
            The proofing document (potentially modified with appended proof response)
        """
        log_service_call("PCFRegistryService", "get_and_append_proof_response")

        # Skip download if proof_response_id is None or empty
        if not proof_response_id:
            print("No proof response ID provided, skipping proof response download.")
            return proofing_document

        # Try to download the proof response file
        proof_response_content = self.download_proof_response(
            proof_response_id)

        if proof_response_content:
            try:
                # Parse the JSON content
                data = json.loads(proof_response_content)

                # Validate and convert to ProofResponse model
                proof_response = ProofResponse.model_validate(data)

                # Append to the proofing document
                proofing_document.proof.append(proof_response)

                print(
                    f"Successfully appended proof response with ID: {proof_response.productFootprintId}")

            except json.JSONDecodeError as e:
                print(f"Error parsing proof response JSON: {e}")
            except Exception as e:
                print(f"Error processing proof response: {e}")
        else:
            print(
                f"Proof response file '{proof_response_id}' not found or could not be downloaded, ignoring.")

        return proofing_document

    def _generate_chunks(self, file_content: str, object_name: str):
        """
        A generator function that yields chunks of bytes from file content.
        This is used for client-side streaming.

        Args:
            file_content: The content of the file as string
            object_name: The name of the object being uploaded

        Yields:
            JsonChunk objects for streaming
        """
        try:
            # Convert string content to bytes
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
        """
        Uploads a proof response file to the server using client-side streaming RPC.

        Args:
            object_name: The name of the object to upload
            file_content: The content of the file as string

        Returns:
            True if upload was successful, False otherwise
        """
        log_service_call("PCFRegistryService", "upload_proof_response")

        if not json_streaming_pb2 or not json_streaming_pb2_grpc:
            print("Warning: gRPC proto files not available, cannot upload")
            return False

        print(f"Uploading proof response file: {object_name}")
        print(f"Using PCF Registry server address: {self.server_address}")

        try:
            with grpc.insecure_channel(self.server_address) as channel:
                stub = json_streaming_pb2_grpc.JsonStreamingServiceStub(
                    channel)

                # The filename is sent as metadata
                metadata = [('filename', object_name)]

                # Create a generator for streaming file chunks
                chunk_generator = self._generate_chunks(
                    file_content, object_name)

                # Upload the file
                response = stub.UploadJson(chunk_generator, metadata=metadata)

                if response.success:
                    print(
                        f"Successfully uploaded proof response file: {object_name}")
                    print(f"Server message: {response.message}")
                    return True
                else:
                    print(f"Upload failed: {response.message}")
                    return False

        except grpc.RpcError as e:
            print(
                f"gRPC error occurred during upload: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            print(f"Error uploading proof response file: {e}")
            return False

    def upload_proof_response_from_file(self, object_name: str, file_path: str) -> bool:
        """
        Uploads a proof response file from local file system to the server.

        Args:
            object_name: The name of the object to upload
            file_path: The path to the local file to upload

        Returns:
            True if upload was successful, False otherwise
        """
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
        """
        Uploads a proofing document as JSON to the server.

        Args:
            object_name: The name of the object to upload
            proofing_document: The proofing document to upload

        Returns:
            True if upload was successful, False otherwise
        """
        try:
            # Convert proofing document to JSON
            json_content = proofing_document.model_dump_json(indent=2)

            return self.upload_proof_response(object_name, json_content)

        except Exception as e:
            print(f"Error serializing proofing document: {e}")
            return False
