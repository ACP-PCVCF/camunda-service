import asyncio
import datetime
import random
import uuid
import json

from typing import Dict, List, Optional, Union
from pyzeebe import ZeebeWorker, Job, JobController, create_insecure_channel, ZeebeClient

from camunda_service.utils import CITIES, INCOTERMS_LIST, TEMP_CONTROL_OPTIONS, generate_iso_timestamp, \
    convert_sets_to_lists, create_crypto_keys, sign_data, generate_location_data, generate_package_data, \
    calculate_emissions


async def main():
    channel = create_insecure_channel(grpc_address="localhost:26500")
    client = ZeebeClient(channel)
    worker = ZeebeWorker(channel)

    @worker.task(task_type="determine_job_sequence", exception_handler=on_error)
    def determine_job_sequence():
        subprocesses = [
            "case_1_with_tsp",
            "case_2_with_tsp",
            "case_3_with_tsp",
        ]
        return {"subprocess_identifiers": subprocesses}

    @worker.task(task_type="produce_data", exception_handler=on_error)
    def produce_data(
            shipment_id: str,
            mass_kg: float = random.uniform(1000, 20000),
            distance_km: float = random.uniform(10, 1000),
            prev_tce_id: Optional[Union[str, List[str]]] = None,
            start_time: Optional[datetime.datetime] = None,
    ) -> Dict:
        """
        Generate transport carbon emission (TCE) data for a shipment.

        Args:
            shipment_id: Unique identifier for the shipment
            mass_kg: Mass of shipment in kilograms
            distance_km: Distance of transport in kilometers
            prev_tce_id: Previous TCE ID for linking records
            start_time: Starting time for the transport

        Returns:
            Dictionary containing the TCE data and cryptographic signatures
        """
        # Generate cryptographic keys
        activity_private_key, activity_public_key_pem = create_crypto_keys()
        tce_id = f"TCE_{uuid.uuid4()}"
        # Initialize base TCE data
        tce_data = {
            "tceId": tce_id,
            "shipmentId": shipment_id,
            "mass": f"{mass_kg:.2f}",
            "distance": {
                "value": f"{distance_km:.2f}",
                "unit": "km",
                "dataSource": "Simulated",
            },
        }

        # Calculate transport activity and emissions
        transport_activity_val = (distance_km * mass_kg) / 1000.0
        tce_data["transportActivity"] = f"{transport_activity_val:.3f}"

        # Add emission data
        tce_data.update(calculate_emissions(transport_activity_val))

        # Add TOC or HOC ID (Transport Operator Code or Handling Operator Code)
        if random.choice([True, False]):
            tce_data["tocId"] = f"TOC_{uuid.uuid4()}"
            tce_data["hocId"] = None
        else:
            tce_data["hocId"] = f"HOC_{uuid.uuid4()}"
            tce_data["tocId"] = None

        # Ensure at least one operator ID exists
        if tce_data.get("tocId") is None and tce_data.get("hocId") is None:
            tce_data["tocId"] = f"TOC_fallback_{uuid.uuid4()}"

        # Add previous TCE IDs if provided
        if prev_tce_id:
            tce_data["prevTceIds"] = (
                [prev_tce_id] if not isinstance(prev_tce_id, list) else prev_tce_id
            )

        # Add consignment ID with 70% probability
        if random.random() < 0.7:
            tce_data["consignmentId"] = f"CON_{uuid.uuid4()}"

        # Add packaging data
        tce_data.update(generate_package_data())

        # Generate origin and destination
        origin_city = random.choice(CITIES)
        destination_city_options = [c for c in CITIES if c != origin_city]
        if not destination_city_options:
            destination_city_options = CITIES
        destination_city = random.choice(destination_city_options)

        tce_data["origin"] = generate_location_data(origin_city)
        tce_data["destination"] = generate_location_data(destination_city)

        # Calculate departure and arrival times
        avg_speed_kmh = random.uniform(60, 80)
        duration_hours = int((distance_km / avg_speed_kmh) * random.uniform(1, 1.2))
        departure_time_iso = generate_iso_timestamp(start_time)
        tce_data["departureAt"] = departure_time_iso
        dt_departure = datetime.datetime.fromisoformat(
            departure_time_iso.replace("Z", "+00:00")
        )
        tce_data["arrivalAt"] = generate_iso_timestamp(
            dt_departure, add_hours=duration_hours
        )

        # Set flight and voyage numbers to None
        tce_data["flightNo"] = None
        tce_data["voyageNo"] = None

        # Add incoterms randomly
        incoterm = random.choice(INCOTERMS_LIST)
        if incoterm:
            tce_data["incoterms"] = incoterm

        # Add temperature control with random selection
        temp_control = random.choice(TEMP_CONTROL_OPTIONS)
        if temp_control:
            tce_data["temperatureControl"] = temp_control

        # Clean up data structure
        tce_data_no_sets = convert_sets_to_lists(tce_data)
        cleaned_tce_data = {k: v for k, v in tce_data_no_sets.items() if v is not None}

        # Serialize, sign, and prepare result
        message_json_str = json.dumps(
            cleaned_tce_data, sort_keys=True, separators=(",", ":")
        )
        signature_hex = sign_data(activity_private_key, message_json_str)

        result_dict = {
            "activityDataJson": message_json_str,
            "activitySignature": signature_hex,
            "activityPublicKeyPem": activity_public_key_pem,
        }

        return {tce_id: result_dict}

    @worker.task(task_type="send_to_proofing_service", exception_handler=on_error)
    def send_to_proofing_service(**variables) -> dict[str, str | dict]:
        """
        This function simulates sending the data to a proofing service.
        """
        # Simulate sending data to a proofing service
        print("Sending data to proofing service...")
        shipment_data = {
            key: value for key, value in variables.items()
            if key.startswith("TCE_")
        }
        # Here you would implement the actual logic to send the data
        # For example, using an HTTP request

        with open("activities.json", "w", encoding="utf-8") as f:
            json.dump(shipment_data, f, indent=4, ensure_ascii=False)

        return {
            "instance_scf": {
                "proof": "proof",
                "pcf": random.uniform(0, 1000),
            },
        }

    @worker.task(task_type="notify_next_node", exception_handler=on_error)
    async def notify_next_node(message_name: str, shipment_id: str = None) -> None:
        shipment_id = shipment_id if shipment_id else f"SHIP_{uuid.uuid4()}"
        # Publish the message to start Process B (message name = 'start-process-b')
        await client.publish_message(
            name=message_name,
            correlation_key=f"{message_name}-{shipment_id}",
            variables={"shipment_id": shipment_id}
        )
        print(f"Published message {message_name} with shipment ID: {shipment_id}")

    @worker.task(
        task_type="send_data_to_origin")
    async def send_data_to_origin(
            shipment_id: str,
            message_name: str,
            tce_data: dict,
    ):
        await client.publish_message(
            name=message_name,
            correlation_key=shipment_id,
            variables={
                "shipment_id": shipment_id,
                "tce_data": tce_data
            }
        )
        print(f"Published message {message_name} with shipment ID: {shipment_id}")

    @worker.task(
        task_type="set_shipment_id", exception_handler=on_error
    )
    def set_shipment_id():
        shipment_id = f"SHIP_{uuid.uuid4()}"
        return {"shipment_id": shipment_id}

    # Start the worker
    await worker.work()


async def on_error(exception: Exception, job: Job, job_controller: JobController):
    """
    on_error will be called when the task fails
    """
    print(exception)
    await job_controller.set_error_status(
        job, f"Failed to handle job {job}. Error: {str(exception)}"
    )


if __name__ == "__main__":
    asyncio.run(main())
