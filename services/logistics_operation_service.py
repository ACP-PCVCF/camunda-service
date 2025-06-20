import uuid
from typing import Dict, Any, Optional, List
from pyzeebe import Job
from models.product_footprint import ProductFootprint, TceData, Distance
from services.sensor_data_service import SensorDataService
from utils.logging_utils import log_service_call


class LogisticsOperationService:
    """Service for handling logistics operations including transport and hub procedures."""

    def __init__(self, sensor_data_service: Optional[SensorDataService] = None):
        """
        Initialize the LogisticsOperationService.

        Args:
            sensor_data_service: Optional SensorDataService instance. If not provided, a new one will be created.
        """
        self.sensor_data_service = sensor_data_service or SensorDataService()

    def execute_transport_procedure(self,
                                    toc_id: int,
                                    product_footprint: Dict[str, Any],
                                    job: Job,
                                    sensor_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute transport procedure for a given transport operation category (TOC).

        Args:
            toc_id: Unique identifier for the transport operation category
            product_footprint: Product footprint data dictionary
            job: Zeebe Job instance containing process instance and element ID
            sensor_data: Optional list of previous sensor data dictionaries to append to

        Returns:
            Dictionary containing updated product footprint and sensor data
        """
        log_service_call("LogisticsOperationService",
                         "execute_transport_procedure")

        # Generate new TCE ID
        new_tce_id = str(uuid.uuid4())

        # Extract job information
        process_id = job.process_instance_key
        element_id = job.element_id

        # Validate and parse product footprint
        product_footprint_verified = ProductFootprint.model_validate(
            product_footprint)

        # Get sensor data from external service
        new_sensor_data = self.sensor_data_service.call_service_sensordata({
            "shipment_id": product_footprint_verified.extensions[0].data.shipmentId,
            "tceId": new_tce_id,
            "camundaProcessInstanceKey": str(process_id),
            "camundaActivityId": element_id
        })

        # Update sensor data list
        if sensor_data is not None:
            sensor_data.append(new_sensor_data.model_dump())
        else:
            sensor_data = [new_sensor_data.model_dump()]

        # Extract distance from sensor data
        distance_from_sensor = new_sensor_data.sensorData.distance.actual

        # Build previous TCE IDs chain
        prev_tce_ids = self._build_prev_tce_ids_chain(
            product_footprint_verified)

        # Create new TCE data for transport
        new_tce = TceData(
            tceId=new_tce_id,
            shipmentId=product_footprint_verified.extensions[0].data.shipmentId,
            mass=product_footprint_verified.extensions[0].data.mass,
            distance=Distance(actual=distance_from_sensor),
            tocId=str(toc_id),  # Convert to string for consistency
            prevTceIds=prev_tce_ids
        )

        # Add TCE to product footprint
        product_footprint_verified.extensions[0].data.tces.append(new_tce)

        return {
            "product_footprint": product_footprint_verified.model_dump(),
            "sensor_data": sensor_data
        }

    def execute_hub_procedure(self,
                              hoc_id: str,
                              product_footprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute hub procedure for a given hub operation category (HOC).

        Args:
            hoc_id: Unique identifier for the hub operation category
            product_footprint: Product footprint data dictionary

        Returns:
            Dictionary containing updated product footprint
        """
        log_service_call("LogisticsOperationService", "execute_hub_procedure")

        # Validate and parse product footprint
        product_footprint_verified = ProductFootprint.model_validate(
            product_footprint)

        # Build previous TCE IDs chain
        prev_tce_ids = self._build_prev_tce_ids_chain(
            product_footprint_verified)

        # Create new TCE data for hub
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
        """
        Build the chain of previous TCE IDs from the product footprint.

        Args:
            product_footprint: Validated ProductFootprint instance

        Returns:
            List of previous TCE IDs
        """
        prev_tce_ids = []

        if len(product_footprint.extensions[0].data.tces) > 0:
            # Get the previous TCE IDs from the last TCE
            prev_tce_ids = product_footprint.extensions[0].data.tces[-1].prevTceIds.copy(
            )

            # Add the last TCE ID to the chain
            last_tce_id = product_footprint.extensions[0].data.tces[-1].tceId
            prev_tce_ids.append(last_tce_id)

        return prev_tce_ids

    def get_tce_chain_summary(self, product_footprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of the TCE chain in the product footprint.

        Args:
            product_footprint: Product footprint data dictionary

        Returns:
            Dictionary containing TCE chain summary
        """
        log_service_call("LogisticsOperationService", "get_tce_chain_summary")

        product_footprint_verified = ProductFootprint.model_validate(
            product_footprint)
        tces = product_footprint_verified.extensions[0].data.tces

        summary = {
            "total_tces": len(tces),
            "transport_operations": len([tce for tce in tces if tce.tocId is not None]),
            "hub_operations": len([tce for tce in tces if tce.hocId is not None]),
            "tce_ids": [tce.tceId for tce in tces],
            "shipment_id": product_footprint_verified.extensions[0].data.shipmentId,
            "total_mass": product_footprint_verified.extensions[0].data.mass
        }

        # Calculate total distance if available
        total_distance = 0.0
        for tce in tces:
            if tce.distance and tce.distance.actual:
                total_distance += tce.distance.actual

        summary["total_distance"] = total_distance

        return summary

    def validate_product_footprint_structure(self, product_footprint: Dict[str, Any]) -> bool:
        """
        Validate that the product footprint has the required structure for operations.

        Args:
            product_footprint: Product footprint data dictionary

        Returns:
            True if valid structure, False otherwise
        """
        try:
            ProductFootprint.model_validate(product_footprint)
            return True
        except Exception:
            return False

    def create_standalone_tce(self,
                              shipment_id: str,
                              mass: float,
                              toc_id: Optional[str] = None,
                              hoc_id: Optional[str] = None,
                              distance: Optional[float] = None,
                              prev_tce_ids: Optional[List[str]] = None) -> TceData:
        """
        Create a standalone TCE data object.

        Args:
            shipment_id: Shipment identifier
            mass: Shipment mass
            toc_id: Optional transport operation category ID
            hoc_id: Optional hub operation category ID
            distance: Optional distance value
            prev_tce_ids: Optional list of previous TCE IDs

        Returns:
            TceData instance
        """
        log_service_call("LogisticsOperationService", "create_standalone_tce")

        if toc_id is None and hoc_id is None:
            raise ValueError("Either toc_id or hoc_id must be provided")

        if toc_id is not None and hoc_id is not None:
            raise ValueError("Only one of toc_id or hoc_id should be provided")

        distance_obj = Distance(
            actual=distance) if distance is not None else None

        return TceData(
            tceId=str(uuid.uuid4()),
            shipmentId=shipment_id,
            mass=mass,
            tocId=toc_id,
            hocId=hoc_id,
            distance=distance_obj,
            prevTceIds=prev_tce_ids or []
        )
