import json
import os
from .pcf_registry_service import PCFRegistryService
from typing import Dict, Any
from models.proofing_document import ProofingDocument, ProofResponse
from utils.kafka import send_message_to_kafka, consume_messages_from_kafka
from utils.logging_utils import log_service_call


class ProofingService:
    """Service for handling proofing document operations via Kafka messaging."""

    def __init__(self, topic_out: str = "shipments", topic_in: str = "pcf-results"):
        self.topic_out = topic_out
        self.topic_in = topic_in
        self.pcf_registry_service = PCFRegistryService()

    def send_proofing_document(self, proofing_document: Dict[str, Any]) -> Dict[str, Any]:
        log_service_call("ProofingService", "send_proofing_document")
        print("Sending proofing document to Kafka...")

        proofing_document_verified = ProofingDocument.model_validate(
            proofing_document)

        if os.path.exists("data/proof_documents_examples/proof_response.json"):
            with open("data/proof_documents_examples/proof_response.json", "r") as f:
                data = json.load(f)
                data = ProofResponse.model_validate(data)
                proofing_document_verified.proof.append(data)
                print(proofing_document_verified.proof[0].productFootprintId)

        print("Proofing document verified and ready to send.")

        message_to_send = proofing_document_verified.model_dump_json()

        send_message_to_kafka(self.topic_out, message_to_send)

        print("Message sent to Kafka topic.")

    def receive_proof_response(self) -> Dict[str, str]:
        response_message = consume_messages_from_kafka(self.topic_in)
        proof_response = ProofResponse.model_validate_json(response_message)
        self.pcf_registry_service.upload_proofing_document(
            proof_response.productFootprintId, proof_response)

        return {"proof_response_id": proof_response.productFootprintId}
