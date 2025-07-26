import json
import os

from .pcf_registry_service import PCFRegistryService
from models.proofing_document import ProofingDocument, ProofResponse
from utils.kafka import send_message_to_kafka, consume_messages_from_kafka
from utils.logging_utils import log_service_call
from typing import Dict, Any


class ProofingService:
    """Service for handling proofing document operations via Kafka messaging."""

    def __init__(self, topic_out: str = "shipments", topic_in: str = "pcf-results"):
        self.topic_out = topic_out
        self.topic_in = topic_in
        self.pcf_registry_service = PCFRegistryService()

    def send_proofing_document(self, proofing_document: Dict[str, Any], proof_response_obj: ProofResponse) -> Dict[str, Any]:
        log_service_call("ProofingService", "send_proofing_document")

        proofing_document_verified = ProofingDocument.model_validate(
            proofing_document)

        if proof_response_obj is not None:
            proofing_document_verified.proof.append(proof_response_obj)
            print(f"Added inner proof with id: {proofing_document_verified.proof[0].productFootprintId} for current Proofing Document ID: {proofing_document_verified.productFootprint.id}")

        print("Sending proofing document to Kafka...")

        message_to_send = proofing_document_verified.model_dump_json()
        send_message_to_kafka(self.topic_out, message_to_send)

        print("Message sent to Kafka topic.")

    def receive_proof_response(self) -> ProofResponse:
        response_message = consume_messages_from_kafka(self.topic_in)
        proof_response = ProofResponse.model_validate_json(response_message)
        self.pcf_registry_service.upload_proofing_document(
            proof_response.productFootprintId, proof_response)

        return proof_response
