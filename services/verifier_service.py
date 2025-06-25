import services.pb.receipt_verifier_pb2 as receipt_verifier_pb2
import services.pb.receipt_verifier_pb2_grpc as receipt_verifier_pb2_grpc
from pathlib import Path
import grpc
from grpc import aio
import os
from config.settings import VERIFIER_SERVICE_API_URL as server_addr
CHUNK_SIZE_BYTES = 3 * 1024 * 1024  # 3MB Chunks


class ReceiptVerifierService():
    """Service to verify proof receipts using gRPC streaming."""

    def __read_file_chunks(self, file_path, chunk_size=1024):
        """Generator to read a file in chunks."""
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield receipt_verifier_pb2.BytesChunk(data=chunk)
        except Exception as e:
            print(f"Error reading file: {e}")

    async def VerifyReceiptStream(self):

        return "Ok"
        """Process a stream of BytesChunk and return a GrpcVerifyResponse."""


"""         async with aio.insecure_channel(server_addr) as channel:
            client = receipt_verifier_pb2_grpc.ReceiptVerifierServiceStub(
                channel)
            print(f"Verbunden mit gRPC Server auf {server_addr}")

            # Create the stream of chunks
            # Until Felix database is available, we use a static file
            file_path = "./data/proof_verify_example/receipt_output.json"
            chunk_stream = self.__read_file_chunks(file_path)

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

            return message """
