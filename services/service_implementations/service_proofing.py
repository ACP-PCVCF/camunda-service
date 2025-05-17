import json
import os
import random
from typing import Dict, Any

import requests
from requests import RequestException

from models.data_models import ProofingResult
from utils.logging_utils import log_service_call


class ProofingService:
    """Service for sending data to proofing service and retrieving proofs."""

    def __init__(self, output_file_path="activities.json"):
        self.output_file_path = output_file_path
        log_service_call("ProofingService", "__init__")
        self.api_url = os.environ.get("PROOFING_SERVICE_API_URL", "http://localhost:8000/api/proofing")

    def send_to_proofing(
            self, shipment_data: Dict[str, Dict], shipment_id: str = None) -> ProofingResult:
        """
        Send shipment data to the proofing service.
        
        Args:
            shipment_data: Dictionary containing TCE data
            shipment_id: Optional shipment ID
            
        Returns:
            Dictionary containing the proof and PCF information
        """
        log_service_call("ProofingService", "send_to_proofing",
                         shipment_data_keys=list(shipment_data.keys()),
                         shipment_id=shipment_id)

        return self.send_to_mock_proofing(shipment_data)

    def send_to_mock_proofing(self, shipment_data: Dict[str, Dict]) -> ProofingResult:
        """
        Send shipment data to the proofing service.
        
        Args:
            shipment_data: Dictionary containing TCE data
            
        Returns:
            Dictionary containing the proof and PCF information
        """
        log_service_call("ProofingService", "send_to_mock_proofing",
                         shipment_data_keys=list(shipment_data.keys()))

        # In production, this would make an API call to the proofing service
        try:
            response = requests.get(f"{self.api_url}/proof", params=shipment_data)
            response.raise_for_status()
            response_data = ProofingResult(**response.json())
            return response_data

        except RequestException as e:
            log_service_call("ProofingService", "_simulate_get_request", error=str(e))
            raise
        # For now, we just simulate this by writing to a file and returning mock data

        # try:
        #     with open(self.output_file_path, "w", encoding="utf-8") as f:
        #         json.dump(shipment_data, f, indent=4, ensure_ascii=False)
        #
        #     # Generate random PCF (Product Carbon Footprint) value
        #     result = {
        #         "instance_scf": {
        #             "proof": self._generate_mock_proof(),
        #             "pcf": random.uniform(0, 1000),
        #         }
        #     }
        #
        #     log_service_call("ProofingService", "send_to_proofing",
        #                      result="success",
        #                      pcf=result["instance_scf"]["pcf"])
        #
        #     return result
        #
        # except Exception as e:
        #     log_service_call("ProofingService", "send_to_proofing",
        #                      error=str(e))
        #     # In production code, proper error handling would go here
        #     raise

    def _generate_mock_proof(self) -> str:
        """Generate a mock proof string (in production this would be a real proof)."""
        proof_chars = "ABCDEFabcdef0123456789"
        return "".join(random.choice(proof_chars) for _ in range(64))
