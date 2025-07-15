import uuid
from typing import Dict, Any, Optional, List
from pyzeebe import Job
from models.product_footprint import ProductFootprint, TceData, Distance
from services.sensor_data_service import SensorDataService
from utils.logging_utils import log_service_call


class LogisticsOperationService:
    """Service for handling logistics operations including transport and hub procedures."""

    def __init__(self, sensor_data_service: Optional[SensorDataService] = None):
        self.sensor_data_service = sensor_data_service or SensorDataService()

    def execute_transport_procedure(self,
                                    toc_id: int,
                                    product_footprint: Dict[str, Any],
                                    job: Job,
                                    sensor_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        log_service_call("LogisticsOperationService",
                         "execute_transport_procedure")
        new_tce_id = str(uuid.uuid4())
        process_id = job.process_instance_key
        element_id = job.element_id
        product_footprint_verified = ProductFootprint.model_validate(
            product_footprint)
        new_sensor_data = self.sensor_data_service.call_service_sensordata({
            "shipment_id": product_footprint_verified.extensions[0].data.shipmentId,
            "tceId": new_tce_id,
            "camundaProcessInstanceKey": str(process_id),
            "camundaActivityId": element_id
        })

        if sensor_data is not None:
            sensor_data.append(new_sensor_data.model_dump())
        else:
            sensor_data = [new_sensor_data.model_dump()]

        distance_from_sensor = new_sensor_data.sensorData.distance.actual

        prev_tce_ids = self._build_prev_tce_ids_chain(
            product_footprint_verified)

        new_tce = TceData(
            tceId=new_tce_id,
            shipmentId=product_footprint_verified.extensions[0].data.shipmentId,
            mass=product_footprint_verified.extensions[0].data.mass,
            distance=Distance(actual=distance_from_sensor),
            tocId=str(toc_id),  # Convert to string for consistency
            prevTceIds=prev_tce_ids
        )

        product_footprint_verified.extensions[0].data.tces.append(new_tce)

        return {
            "product_footprint": product_footprint_verified.model_dump(),
            "sensor_data": sensor_data
        }

    def execute_hub_procedure(self,
                              hoc_id: str,
                              product_footprint: Dict[str, Any]) -> Dict[str, Any]:
        log_service_call("LogisticsOperationService", "execute_hub_procedure")
        product_footprint_verified = ProductFootprint.model_validate(
            product_footprint)
        prev_tce_ids = self._build_prev_tce_ids_chain(
            product_footprint_verified)

        new_tce = TceData(
            tceId=str(uuid.uuid4()),
            shipmentId=product_footprint_verified.extensions[0].data.shipmentId,
            mass=product_footprint_verified.extensions[0].data.mass,
            hocId=hoc_id,
            prevTceIds=prev_tce_ids
        )

        # Add TCE to product footprint
        product_footprint_verified.extensions[0].data.tces.append(new_tce)

        return {
            "product_footprint": product_footprint_verified.model_dump()
        }

    def _build_prev_tce_ids_chain(self, product_footprint: ProductFootprint) -> List[str]:
        prev_tce_ids = []

        if len(product_footprint.extensions[0].data.tces) > 0:
            # Get the previous TCE IDs from the last TCE
            prev_tce_ids = product_footprint.extensions[0].data.tces[-1].prevTceIds.copy(
            )

            # Add the last TCE ID to the chain
            last_tce_id = product_footprint.extensions[0].data.tces[-1].tceId
            prev_tce_ids.append(last_tce_id)

        return prev_tce_ids
