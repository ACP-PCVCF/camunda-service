import random
import uuid
from typing import Dict

from pyzeebe import ZeebeWorker, ZeebeClient

from services.service_implementations.service_proofing import ProofingService
from services.service_implementations.service_sensordata import SensorDataService
from utils.error_handling import on_error
from utils.logging_utils import log_task_start, log_task_completion


class CamundaWorkerTasks:
    """Zeebe worker task handlers."""
    
    def __init__(self, worker: ZeebeWorker, client: ZeebeClient):
        self.worker = worker
        self.client = client
        self.sensor_data_service = SensorDataService()
        self.proofing_service = ProofingService()
        
        # Register all tasks
        self._register_tasks()
    
    def _register_tasks(self):
        """Register all task handlers with the Zeebe worker."""
        self.worker.task(task_type="determine_job_sequence", exception_handler=on_error)(self.determine_job_sequence)
        self.worker.task(task_type="call_service_sensordata", exception_handler=on_error)(self.call_service_sensordata)
        self.worker.task(task_type="send_to_proofing_service", exception_handler=on_error)(self.send_to_proofing_service)
        self.worker.task(task_type="notify_next_node", exception_handler=on_error)(self.notify_next_node)
        self.worker.task(task_type="send_data_to_origin", exception_handler=on_error)(self.send_data_to_origin)
        self.worker.task(task_type="set_shipment_id", exception_handler=on_error)(self.set_shipment_id)
    
    def determine_job_sequence(self):
        """
        Determine which subprocesses should be executed.
        
        Returns:
            Dictionary containing the list of subprocess identifiers
        """
        log_task_start("determine_job_sequence")
        
        subprocesses = [
            "case_1_with_tsp",
            "case_2_with_tsp",
            "case_3_with_tsp",
        ]
        result = {"subprocess_identifiers": subprocesses}
        
        log_task_completion("determine_job_sequence", **result)
        return result
    
    def call_service_sensordata(
            self,
            shipment_id: str,
            sensor_id: int = random.randint(1, 1000)  # Random sensor ID for demonstration
    ) -> Dict:
        """
        Generate transport carbon emission (TCE) data for a shipment.
        
        Args:
            shipment_id: Unique identifier for the shipment
            sensor_id: Unique identifier for the sensor
        
        Returns:
            Dictionary containing the TCE data
        """
        #log_task_start("call_service_sensordata", shipment_id=shipment_id, sensor_id=sensor_id)
        # Instead of the inline implementation, call the service
        # In the future, this would call the real sensor data service
        result = self.sensor_data_service.fetch_sensor_data({"shipment_id": shipment_id})

        #log_task_completion("call_service_sensordata", **result)

        return result
    
    def call_service_sensordata_certificate(self):
        """
        Generate a certificate for the transport carbon emission (TCE) data.
        
        Returns:
            Dictionary containing the certificate data
        """
        log_task_start("call_service_sensordata_certificate")
        
        # In the future, this would call the real sensor data service
        result = {
            "certificate": "Certificate data here"
        }
        
        log_task_completion("call_service_sensordata_certificate", **result)
        return result
    
    def send_to_proofing_service(self, **variables) -> dict[str, str | dict]:
        """
        Send data to a proofing service.
        
        Args:
            variables: Process variables containing TCE data
            
        Returns:
            Dictionary containing proof and PCF information
        """
        log_task_start("send_to_proofing_service")
        
        # Extract TCE data from variables
        shipment_data = {
            key: value for key, value in variables.items()
            if key.startswith("TCE_")
        }
        
        # Call the proofing service
        result = self.proofing_service.send_to_proofing(shipment_data)
        result_data = result.dict()
        
        log_task_completion("send_to_proofing_service", **result_data)
        return result_data
    
    async def notify_next_node(self, message_name: str, shipment_id: str = None) -> None:
        """
        Publish a message to notify the next node in the process.
        
        Args:
            message_name: Name of the message to publish
            shipment_id: Unique identifier for the shipment
        """
        log_task_start("notify_next_node", message_name=message_name, shipment_id=shipment_id)
        
        shipment_id = shipment_id if shipment_id else f"SHIP_{uuid.uuid4()}"
        
        # Publish the message
        await self.client.publish_message(
            name=message_name,
            correlation_key=f"{message_name}-{shipment_id}",
            variables={"shipment_id": shipment_id}
        )
        
        log_task_completion("notify_next_node")
    
    async def send_data_to_origin(
            self,
            shipment_id: str,
            message_name: str,
            tce_data: dict,
    ):
        """
        Send data back to the origin process.
        
        Args:
            shipment_id: Unique identifier for the shipment
            message_name: Name of the message to publish
            tce_data: TCE data to include in the message
        """
        log_task_start("send_data_to_origin", shipment_id=shipment_id, message_name=message_name)
        
        await self.client.publish_message(
            name=message_name,
            correlation_key=shipment_id,
            variables={
                "shipment_id": shipment_id,
                "tce_data": tce_data
            }
        )
        
        log_task_completion("send_data_to_origin")
    
    def set_shipment_id(self):
        """
        Generate a new shipment ID.
        
        Returns:
            Dictionary containing the new shipment ID
        """
        log_task_start("set_shipment_id")
        
        shipment_id = f"SHIP_{uuid.uuid4()}"
        result = {"shipment_id": shipment_id}
        
        log_task_completion("set_shipment_id", **result)
        return result