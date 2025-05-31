import random
import uuid
import datetime
from typing import Dict
from pyzeebe import ZeebeWorker, ZeebeClient
from services.service_implementations.service_proofing import ProofingService
from services.service_implementations.service_sensordata import SensorDataService
from utils.error_handling import on_error
from utils.logging_utils import log_task_start, log_task_completion
from utils.data_utils import get_mock_data
from models.data_models import ProductFootprint, TCE, Distance, Extension, ExtensionData, ProofingDocument


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
        self.worker.task(task_type="determine_job_sequence",
                         exception_handler=on_error)(self.determine_job_sequence)
        self.worker.task(task_type="call_service_sensordata",
                         exception_handler=on_error)(self.call_service_sensordata)
        self.worker.task(task_type="send_to_proofing_service",
                         exception_handler=on_error)(self.send_to_proofing_service)
        self.worker.task(task_type="notify_next_node",
                         exception_handler=on_error)(self.notify_next_node)
        self.worker.task(task_type="send_data_to_origin",
                         exception_handler=on_error)(self.send_data_to_origin)
        self.worker.task(task_type="define_product_footprint_template",
                         exception_handler=on_error)(self.define_product_footprint_template)
        self.worker.task(task_type="hub_procedure",
                         exception_handler=on_error)(self.hub_procedure)
        self.worker.task(task_type="transport_procedure",
                         exception_handler=on_error)(self.transport_procedure)
        self.worker.task(task_type="set_shipment_information",
                         exception_handler=on_error)(self.set_shipment_information)
        self.worker.task(task_type="collect_hoc_toc_data",
                         exception_handler=on_error)(self.collect_hoc_toc_data)

    def collect_hoc_toc_data(self, product_footprint: dict):

        product_footprint_verified = ProductFootprint.model_validate(
            product_footprint)

        proofingDocument = ProofingDocument(
            productFootprint=product_footprint_verified, tocData=[], hocData=[])
        for ids in product_footprint_verified.extensions[0].data.tces:
            if ids.tocId is not None:
                proofingDocument.tocData.append(get_mock_data(ids.tocId))
            if ids.hocId is not None:
                proofingDocument.hocData.append(get_mock_data(ids.hocId))

        result = {
            "proofing_document": proofingDocument.model_dump()
        }

        return result

    def transport_procedure(self, tocId: int, product_footprint: dict) -> dict:

        log_task_start("transport_procedure", tocId=tocId,
                       product_footprint=product_footprint)

        # call greta
        distance_from_sensor = random.uniform(10, 1000)

        product_footprint_verified = ProductFootprint.model_validate(
            product_footprint)

        prev_tce_ids = []

        if len(product_footprint_verified.extensions[0].data.tces) > 0:
            prev_tce_ids = product_footprint_verified.extensions[0].data.tces[-1].prevTceIds.copy(
            )
            last_tceid = product_footprint_verified.extensions[0].data.tces[-1].tceId

            prev_tce_ids.append(last_tceid)

        new_TCE = TCE(
            tceId=str(uuid.uuid4()),
            shipmentId=product_footprint_verified.extensions[0].data.shipmentId,
            mass=product_footprint_verified.extensions[0].data.mass,
            distance=Distance(
                actual=distance_from_sensor
            ),
            tocId=tocId,
            prevTceIds=prev_tce_ids
        )

        product_footprint_verified.extensions[0].data.tces.append(
            new_TCE
        )

        result = {
            "product_footprint": product_footprint_verified.model_dump()
        }

        log_task_completion("transport_procedure", **result)

        return result

    def hub_procedure(self, hocId: str, product_footprint: dict) -> dict:
        """
        Handle the hub procedure for a given HOC ID and product footprint.

        Args:
            hocId: Unique identifier for the hub operation category (HOC)
            product_footprint: Product footprint data

        Returns:
            product_footprint with HocId Information
        """

        log_task_start("hub_procedure", hocId=hocId,
                       product_footprint=product_footprint)

        product_footprint_verified = ProductFootprint.model_validate(
            product_footprint)

        prev_tce_ids = []
        if len(product_footprint_verified.extensions[0].data.tces) > 0:
            prev_tce_ids = product_footprint_verified.extensions[0].data.tces[-1].prevTceIds.copy(
            )
            last_tceid = product_footprint_verified.extensions[0].data.tces[-1].tceId

            prev_tce_ids.append(last_tceid)

        new_TCE = TCE(
            tceId=str(uuid.uuid4()),
            shipmentId=product_footprint_verified.extensions[0].data.shipmentId,
            mass=product_footprint_verified.extensions[0].data.mass,
            hocId=hocId,
            prevTceIds=prev_tce_ids
        )
        print("New TCE:")
        print(new_TCE.prevTceIds)
        product_footprint_verified.extensions[0].data.tces.append(
            new_TCE
        )
        result = {
            "product_footprint": product_footprint_verified.model_dump()
        }

        log_task_completion("hub_procedure", **result)

        return result

    def define_product_footprint_template(self, company_name: str, shipment_information: dict) -> dict:
        """
        Define a product footprint template.

        Returns:
            Dictionary containing the product footprint template
        """
        log_task_start("define_product_footprint_template")

        product_footprint = ProductFootprint(
            id=str(uuid.uuid4()),
            created=datetime.datetime.now().isoformat(),
            specVersion="2.0.0",
            version=0,
            status="Active",
            companyName=company_name,
            companyIds=[f"urn:epcidsgln:{uuid.uuid4()}"],
            productDescription=f"Logistics emissions related to shipment with ID {shipment_information.get('shipment_id', 'unknown')}",
            productIds=[
                f"urn:pathfinder:product:customcode:vendor-assigned:{uuid.uuid4()}"],
            productCategoryCpc=random.randint(1000, 9999),
            productNameCompany=f"Shipment with ID {shipment_information.get('shipment_id', 'unknown')}",
            extensions=[
                Extension(
                    dataSchema="https://api.ileap.sine.dev/shipment-footprint.json",
                    data=ExtensionData(
                        mass=shipment_information.get(
                            "shipment_weight", random.uniform(1000, 20000)),
                        shipmentId=shipment_information.get(
                            "shipment_id", f"SHIP_{uuid.uuid4()}")
                    )
                )
            ]
        )
        result = {
            "product_footprint": product_footprint.model_dump()
        }

        log_task_completion("define_product_footprint_template", **result)
        return result

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
            # Random sensor ID for demonstration
            sensor_id: int = random.randint(1, 1000)
    ) -> Dict:
        """
        Generate transport carbon emission (TCE) data for a shipment.

        Args:
            shipment_id: Unique identifier for the shipment
            sensor_id: Unique identifier for the sensor

        Returns:
            Dictionary containing the TCE data
        """
        # log_task_start("call_service_sensordata", shipment_id=shipment_id, sensor_id=sensor_id)
        # Instead of the inline implementation, call the service
        # In the future, this would call the real sensor data service
        result = self.sensor_data_service.get_mock_sensor_data(
            shipment_id=shipment_id,
            mass_kg=None or random.uniform(1000, 20000),
            distance_km=None or random.uniform(10, 1000),
            prev_tce_id=None,
            start_time=None
        )

        # log_task_completion("call_service_sensordata", **result)

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

        log_task_completion("send_to_proofing_service", **result)
        return result

    async def notify_next_node(self, message_name: str, shipment_information: dict = None) -> None:
        """
        Publish a message to notify the next node in the process.

        Args:
            message_name: Name of the message to publish
            shipment_id: Unique identifier for the shipment
        """
        log_task_start("notify_next_node",
                       message_name=message_name, shipment_information=shipment_information)

        # Publish the message
        await self.client.publish_message(
            name=message_name,
            correlation_key=f"{message_name}-{shipment_information.get('shipment_id', 'unknown')}",
            variables={"shipment_information": shipment_information}
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
        log_task_start("send_data_to_origin",
                       shipment_id=shipment_id, message_name=message_name)

        await self.client.publish_message(
            name=message_name,
            correlation_key=shipment_id,
            variables={
                "shipment_id": shipment_id,
                "tce_data": tce_data
            }
        )

        log_task_completion("send_data_to_origin")

    def set_shipment_information(self):
        """
        Generate a new shipment ID.
        And weight for the shipment.

        Returns:
            Dictionary containing the new shipment ID and weight
        """
        log_task_start("set_shipment_information")

        shipment_id = f"SHIP_{uuid.uuid4()}"
        weight = random.uniform(1000, 20000)
        result = {"shipment_information": {
            "shipment_id": shipment_id, "shipment_weight": weight}}

        log_task_completion("set_shipment_information", **result)
        return result
