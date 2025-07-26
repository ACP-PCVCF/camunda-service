import grpc
import json

import services.pb.receipt_verifier_pb2 as receipt_verifier_pb2
import services.pb.receipt_verifier_pb2_grpc as receipt_verifier_pb2_grpc

from grpc import aio
from config.settings import VERIFIER_SERVICE_API_URL as server_addr
from services.pcf_registry_service import PCFRegistryService
CHUNK_SIZE_BYTES = 3 * 1024 * 1024


class ReceiptVerifierService():
    """Service to verify proof receipts using gRPC streaming."""

    def __init__(self):
        self.pcf_registry_service = PCFRegistryService()

    def __read_data_chunks(self, data, chunk_size=1024):
        """Generator to read data in chunks."""
        try:
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data

            for i in range(0, len(data_bytes), chunk_size):
                chunk = data_bytes[i:i + chunk_size]
                yield receipt_verifier_pb2.BytesChunk(data=chunk)
        except Exception as e:
            print(f"Error reading data: {e}")

    async def VerifyReceiptStream(self, proof_response=None):
        """Process a stream of BytesChunk and return a GrpcVerifyResponse."""

        print("Uploading proof response to verifier service...")
        async with aio.insecure_channel(server_addr) as channel:
            client = receipt_verifier_pb2_grpc.ReceiptVerifierServiceStub(
                channel)
            print(f"Connected to gRPC server: {server_addr}")

            proof_response_data = proof_response.model_dump()

            if proof_response_data:
                verifier_data = {}
                verifier_data['receipt'] = proof_response_data['proofReceipt']
                verifier_data['image_id'] = proof_response_data['imageId']

                chunk_stream = self.__read_data_chunks(
                    json.dumps(verifier_data))

                print(f"Finished preparing file '{proof_response_data['productFootprintId']}' for streaming.")

                try:
                    response = await client.VerifyReceiptStream(chunk_stream)
                    print(f"Verifier service:  {{ Valid: {response.valid}, Message: {response.message} }}")
                    message = response.message

                    return message

                except grpc.RpcError as e:
                    print(f"Error gRPC: {e.code()}: {e.details()}")
                    return f"gRPC Error: {e.details()}"

            return "No proof response file found or invalid file path."
