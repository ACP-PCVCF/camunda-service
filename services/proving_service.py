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
        """
        Send a proofing document to the proofing service and receive the response.

        Args:
            proofing_document: Dictionary containing the proofing document data

        Returns:
            Dictionary containing the proof response

        Raises:
            ValidationError: If the proofing document is invalid
            Exception: If there's an error in Kafka communication
        """
        log_service_call("ProofingService", "send_proofing_document")

        # Validate the proofing document using Pydantic model
        proofing_document_verified = ProofingDocument.model_validate(
            proofing_document)

        # Convert to JSON and send to Kafka
        message_to_send = proofing_document_verified.model_dump_json()
        send_message_to_kafka(self.topic_out, message_to_send)

        # Consume response from Kafka
        response_message = consume_messages_from_kafka(self.topic_in)

        # Validate and parse the response
        proof_response = ProofResponse.model_validate_json(response_message)

        return proof_response.model_dump()

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
