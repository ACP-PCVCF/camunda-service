import services.pb.receipt_verifier_pb2 as receipt_verifier_pb2
import services.pb.receipt_verifier_pb2_grpc as receipt_verifier_pb2_grpc
from pathlib import Path
import grpc
from grpc import aio
import os
import json
from config.settings import VERIFIER_SERVICE_API_URL as server_addr
CHUNK_SIZE_BYTES = 3 * 1024 * 1024  # 3MB Chunks


class ReceiptVerifierService():
    """Service to verify proof receipts using gRPC streaming."""

    def __read_data_chunks(self, data, chunk_size=1024):
        """Generator to read data in chunks."""
        try:
            # Convert string data to bytes if needed
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data

            # Split data into chunks
            for i in range(0, len(data_bytes), chunk_size):
                chunk = data_bytes[i:i + chunk_size]
                yield receipt_verifier_pb2.BytesChunk(data=chunk)
        except Exception as e:
            print(f"Error reading data: {e}")

    async def VerifyReceiptStream(self):
        """Process a stream of BytesChunk and return a GrpcVerifyResponse."""

        async with aio.insecure_channel(server_addr) as channel:
            client = receipt_verifier_pb2_grpc.ReceiptVerifierServiceStub(
                channel)
            print(f"Verbunden mit gRPC Server auf {server_addr}")

            # Create the stream of chunks
            # Until Felix database is available, we use a static file
            if os.path.exists("data/proof_documents_examples/proof_response.json"):
                with open("data/proof_documents_examples/proof_response.json", "r") as f:
                    proof_response = json.load(f)

                    verifier_data = {}
                    verifier_data['receipt'] = proof_response['proofReceipt']
                    verifier_data['image_id'] = proof_response['imageId']

                    chunk_stream = self.__read_data_chunks(
                        json.dumps(verifier_data))

                    print("Starte Stream zum Server...")

                    # Call the streaming RPC
                    try:
                        response = await client.VerifyReceiptStream(chunk_stream)

                        print("gRPC Antwort erhalten:")
                        print(f"  Valid: {response.valid}")
                        print(f"  Message: {response.message}")

                        message = response.message

                        if response.HasField('journal_value'):
                            print(f"  Journal Value: {response.journal_value}")

                    except grpc.RpcError as e:
                        print(f"gRPC Fehler: {e.code()}: {e.details()}")

                    return message

            return "No proof response file found or invalid file path."
