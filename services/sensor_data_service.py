import json
import requests
import os

from models.sensor_data import TceSensorData
from utils.logging_utils import log_service_call


class SensorDataService:
    """Service for retrieving and generating transport emission data."""

    def __init__(self):
        log_service_call("SensorDataService", "__init__")
        self.base_url = os.getenv(
            "SENSOR_SERVICE_API_URL", "http://localhost:8000")

    def call_service_sensordata(self, variables) -> TceSensorData:
        shipment_id = variables.get("shipment_id", "unknown")
        tce_id = variables.get("tceId")
        process_instance_key = variables.get("camundaProcessInstanceKey")
        activity_id = variables.get("camundaActivityId")

        payload = {
            "shipment_id": shipment_id,
            "tceId": tce_id,
            "camundaProcessInstanceKey": process_instance_key,
            "camundaActivityId": activity_id
        }

        log_service_call(
            service_name="SensorDataService",
            method_name="call_service_sensordata",
            message="Sending sensor data request",
            payload=payload
        )

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/sensor-data",
                json=payload,
                timeout=10
            )
            log_service_call(
                service_name="SensorDataService",
                method_name="call_service_sensordata",
                message=f"Received response {response.status_code}",
                payload=response.json() if response.ok else response.text
            )

            response.raise_for_status()
            response_data = response.json()

            print(f"Response data: {response_data}")

            # Parse sensorData if it's a JSON string
            if 'sensorData' in response_data and isinstance(response_data['sensorData'], str):
                response_data['sensorData'] = json.loads(
                    response_data['sensorData'])

            return TceSensorData(**response_data)

        except requests.RequestException as e:
            log_service_call(
                service_name="SensorDataService",
                method_name="call_service_sensordata",
                message=f"HTTP request failed: {str(e)}",
                payload=payload
            )
            raise
