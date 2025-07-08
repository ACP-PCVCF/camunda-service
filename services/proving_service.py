import json
import os
from typing import Dict, Any
from models.proofing_document import ProofingDocument, ProofResponse
from utils.kafka import send_message_to_kafka, consume_messages_from_kafka
from utils.logging_utils import log_service_call


class ProofingService:
    """Service for handling proofing document operations via Kafka messaging."""

    def __init__(self, topic_out: str = "shipments", topic_in: str = "pcf-results"):
        """
        Initialize the ProofingService.

        Args:
            topic_out: Kafka topic for sending proofing documents
            topic_in: Kafka topic for receiving proof responses
        """
        self.topic_out = topic_out
        self.topic_in = topic_in

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

    def receive_proof_response(self) -> ProofResponse:
        response_message = consume_messages_from_kafka(self.topic_in)

        proof_response = ProofResponse.model_validate_json(response_message)

        response_dict = proof_response.model_dump()

        # Delete proof_response.json file if it exists
        proof_response_path = "data/proof_documents_examples/proof_response.json"
        try:
            if os.path.exists(proof_response_path):
                os.remove(proof_response_path)
                print(f"Deleted {proof_response_path}")
        except OSError as e:
            print(f"Error deleting {proof_response_path}: {e}")

        with open("data/proof_documents_examples/proof_response.json", "w") as f:
            json.dump(response_dict, f, indent=4)

        return response_dict

    def validate_proofing_document(self, proofing_document: Dict[str, Any]) -> ProofingDocument:
        """
        Validate a proofing document without sending it.

        Args:
            proofing_document: Dictionary containing the proofing document data

        Returns:
            Validated ProofingDocument instance

        Raises:
            ValidationError: If the proofing document is invalid
        """
        return ProofingDocument.model_validate(proofing_document)

    def parse_proof_response(self, response_json: str) -> ProofResponse:
        """
        Parse a proof response from JSON.

        Args:
            response_json: JSON string containing the proof response

        Returns:
            Parsed ProofResponse instance

        Raises:
            ValidationError: If the response is invalid
        """
        return ProofResponse.model_validate_json(response_json)
