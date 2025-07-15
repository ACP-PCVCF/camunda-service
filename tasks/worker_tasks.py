import random
import uuid
from typing import Optional
import os

from pyzeebe import ZeebeWorker, ZeebeClient, Job

from utils.error_handling import on_error
from utils.logging_utils import log_task_start, log_task_completion

from services.database import HocTocService
from services.verifier_service import ReceiptVerifierService
from services.sensor_data_service import SensorDataService
from services.proving_service import ProofingService
from services.product_footprint import ProductFootprintService
from services.logistics_operation_service import LogisticsOperationService
from services.pcf_registry_service import PCFRegistryService


class CamundaWorkerTasks:
    """Zeebe worker task handlers."""

    def __init__(self, worker: ZeebeWorker, client: ZeebeClient):
        self.worker = worker
        self.client = client
        self.hoc_toc_service = HocTocService()
        self.sensor_data_service = SensorDataService()
        self.receipt_verifier_service = ReceiptVerifierService()
        self.proofing_service = ProofingService()
        self.product_footprint_service = ProductFootprintService()
        self.logistics_operation_service = LogisticsOperationService(
            self.sensor_data_service)
        self.pcf_registry_service = PCFRegistryService()

        self._register_tasks()

    def _register_tasks(self):
        """Register all task handlers with the Zeebe worker."""
        self.worker.task(task_type="determine_job_sequence",
                         exception_handler=on_error)(self.determine_job_sequence)
        self.worker.task(task_type="send_to_proofing_service",
                         exception_handler=on_error, timeout_ms=600000)(self.send_to_proofing_service)
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
        self.worker.task(task_type="verify_receipt",
                         exception_handler=on_error)(self.verify_receipt)
        self.worker.task(task_type="consume_proof_response",
                         exception_handler=on_error, timeout_ms=600000)(self.consume_proof_response)
        self.worker.task(task_type="get_proof_from_pcf_registry",
                         exception_handler=on_error)(self.get_proof_from_pcf_registry)

    def get_proof_from_pcf_registry(self, previous_product_footprint_id) -> dict:
        log_task_start("get_proof_from_pcf_registry")

        if previous_product_footprint_id is None:
            print("No previous product footprint ID provided")
            log_task_completion("get_proof_from_pcf_registry")
            return {"get_proof_success": "False"}

        proof_response_id = previous_product_footprint_id["proof_response_id"]
        print(f"Downloading proof response with ID: {proof_response_id}")

        proof_response = self.pcf_registry_service.download_proof_response(
            proof_response_id)

        if proof_response:
            proof_response_path = "data/proof_documents_examples/proof_response.json"
            try:
                os.makedirs(os.path.dirname(
                    proof_response_path), exist_ok=True)

                with open(proof_response_path, 'w', encoding='utf-8') as f:
                    f.write(proof_response)
                print(f"Proof response saved to: {proof_response_path}")
                log_task_completion(
                    "get_proof_from_pcf_registry", saved_to=proof_response_path)
                return {"get_proof_success": "True"}

            except Exception as e:
                print(f"Error saving proof response to file: {e}")
                log_task_completion(
                    "get_proof_from_pcf_registry", error=str(e))
                return {"get_proof_success": "False", "error": str(e)}
        else:
            print(
                f"Failed to download proof response with ID: {proof_response_id}")
            log_task_completion("get_proof_from_pcf_registry")
            return {"get_proof_success": "False"}

    def consume_proof_response(self) -> dict:
        log_task_start("consume_proof_response")

        proof_response_id = self.proofing_service.receive_proof_response()

        log_task_completion("consume_proof_response", **proof_response_id)
        return {"proof_response_id": proof_response_id}

    async def verify_receipt(self) -> dict:
        log_task_start("verify_receipt")

        receipt_verifier = self.receipt_verifier_service
        result = await receipt_verifier.VerifyReceiptStream()

        log_task_completion("verify_receipt")
        return {"verification_result": result}

    def collect_hoc_toc_data(self, product_footprint: dict, sensor_data: Optional[list[dict]] = None) -> dict:
        log_task_start("collect_hoc_toc_data")
        result = self.hoc_toc_service.collect_hoc_toc_data(
            product_footprint, sensor_data)
        log_task_completion("collect_hoc_toc_data")

        return result

    def transport_procedure(self, tocId: int, product_footprint: dict, job: Job, sensor_data: Optional[list[dict]] = None) -> dict:
        log_task_start("transport_procedure")

        result = self.logistics_operation_service.execute_transport_procedure(
            tocId, product_footprint, job, sensor_data)

        log_task_completion("transport_procedure")
        return result

    def hub_procedure(self, hocId: str, product_footprint: dict) -> dict:
        result = self.logistics_operation_service.execute_hub_procedure(
            hocId, product_footprint)

        log_task_completion("hub_procedure")
        return result

    def define_product_footprint_template(self, company_name: str, shipment_information: dict) -> dict:
        result = self.product_footprint_service.create_product_footprint_template(
            company_name, shipment_information)

        log_task_completion("define_product_footprint_template")
        return result

    def determine_job_sequence(self):
        log_task_start("determine_job_sequence")

        subprocesses = [
            "case_1_with_tsp",
            "case_2_with_tsp",
            "case_3_with_tsp",
        ]
        result = {"subprocess_identifiers": subprocesses}

        log_task_completion("determine_job_sequence", **result)
        return result

    def send_to_proofing_service(self, proofing_document: dict) -> dict:
        log_task_start("send_to_proofing_service")

        self.proofing_service.send_proofing_document(
            proofing_document)

        log_task_completion("send_to_proofing_service")

        return {"proof_send_status": "send_successful"}

    async def notify_next_node(self, message_name: str, shipment_information: dict) -> None:
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
            shipment_information: dict,
            message_name: str,
            product_footprints: dict,
    ):
        log_task_start("send_data_to_origin",
                       shipment_information=shipment_information, message_name=message_name)

        await self.client.publish_message(
            name=message_name,
            correlation_key=shipment_information.get("shipment_id", "unknown"),
            variables={
                "shipment_id": shipment_information.get("shipment_id", "unknown"),
                "product_footprints": product_footprints
            }
        )

        log_task_completion("send_data_to_origin")

    def set_shipment_information(self):
        log_task_start("set_shipment_information")

        shipment_id = f"SHIP_{uuid.uuid4()}"
        weight = random.uniform(1000, 20000)
        result = {"shipment_information": {
            "shipment_id": shipment_id, "shipment_weight": weight}}

        log_task_completion("set_shipment_information", **result)
        return result
