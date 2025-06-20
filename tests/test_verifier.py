import asyncio
import os
import unittest
from pathlib import Path
import grpc
from grpc import aio
import receipt_verifier_pb2_grpc
import receipt_verifier_pb2

CHUNK_SIZE_BYTES = 3 * 1024 * 1024  # 3MB Chunks


async def read_file_chunks(file_path):
    """Generator that yields file chunks asynchronously"""
    try:
        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                print(f"Sende Chunk mit {len(chunk)} Bytes")
                yield receipt_verifier_pb2.BytesChunk(data=chunk)
    except Exception as e:
        print(f"Fehler beim Lesen der Datei: {e}")


async def main():
    # Server configuration
    server_addr = "localhost:50051"
    file_path = "./data/proof_verify_example/receipt_output.json"

    # Check if file exists
    if not Path(file_path).exists():
        print(f"Datei {file_path} nicht gefunden!")
        return

    # Get file size
    file_size = os.path.getsize(file_path)
    print(f"Lese Datei: {file_path} (Größe: {file_size} bytes)")

    # Create gRPC channel and client
    try:
        async with aio.insecure_channel(server_addr) as channel:
            client = receipt_verifier_pb2_grpc.ReceiptVerifierServiceStub(
                channel)
            print(f"Verbunden mit gRPC Server auf {server_addr}")

            # Create the stream of chunks
            chunk_stream = read_file_chunks(file_path)

            print("Starte Stream zum Server...")

            # Call the streaming RPC
            try:
                response = await client.VerifyReceiptStream(chunk_stream)

                print("gRPC Antwort erhalten:")
                print(f"  Valid: {response.valid}")
                print(f"  Message: {response.message}")

                if response.HasField('journal_value'):
                    print(f"  Journal Value: {response.journal_value}")

            except grpc.RpcError as e:
                print(f"gRPC Fehler: {e.code()}: {e.details()}")

    except Exception as e:
        print(f"Verbindungsfehler: {e}")


class TestReceiptVerifier(unittest.IsolatedAsyncioTestCase):

    async def test_main(self):
        """Test the main function"""
        await main()


if __name__ == "__main__":
    unittest.main()
