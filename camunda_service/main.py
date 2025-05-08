import asyncio
import datetime
import random
import uuid
import json

from typing import Dict, List, Any, Optional, Union
from pyzeebe import ZeebeWorker, Job, JobController, create_insecure_channel, ZeebeClient
from cryptography.hazmat.primitives import (
    hashes,
    serialization,
)
from cryptography.hazmat.primitives.asymmetric import (
    rsa,
    padding,
)
from cryptography.hazmat.backends import default_backend  #

CITIES = [
    "Berlin",
    "Hamburg",
    "München",
    "Köln",
    "Frankfurt",
    "Stuttgart",
    "Düsseldorf",
    "Dortmund",
    "Essen",
    "Leipzig",
    "Bremen",
    "Dresden",
    "Hannover",
    "Nürnberg",
    "Duisburg",
    "Bochum",
    "Wuppertal",
    "Bielefeld",
    "Bonn",
    "Münster",
    "Karlsruhe",
    "Mannheim",
    "Augsburg",
    "Wiesbaden",
]

PACKAGING_TYPES = [
    "Pallet",
    "Container-TEU",
    "Bulk",
    "Box",
    "Crate",
    None,
]

INCOTERMS_LIST = [
    "EXW",
    "FCA",
    "CPT",
    "CIP",
    "DAP",
    "DPU",
    "DDP",
    "FAS",
    "FOB",
    "CFR",
    "CIF",
    None,
]

TEMP_CONTROL_OPTIONS = ["ambient", "refrigerated", None]


def generate_iso_timestamp(base_time=None, add_hours=0):
    """Generiert einen ISO 8601 Timestamp in UTC."""
    if base_time is None:
        base_time = datetime.datetime.now(datetime.timezone.utc)
    time_to_format = base_time + datetime.timedelta(hours=add_hours)
    return time_to_format.isoformat(timespec="seconds").replace("+00:00", "Z")


def convert_sets_to_lists(obj):
    """Recursively convert sets to lists in nested data structures."""
    if isinstance(obj, dict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_sets_to_lists(elem) for elem in obj]
    elif isinstance(obj, set):
        return [convert_sets_to_lists(elem) for elem in obj]
    return obj


def create_crypto_keys():
    """Generate RSA key pair for signing data."""
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_key, public_key_pem


def sign_data(private_key, data_str: str) -> str:
    """Sign data with private key and return hex signature."""
    message_bytes = data_str.encode("utf-8")
    signature_bytes = private_key.sign(
        message_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    return signature_bytes.hex()


def generate_location_data(city_name: str) -> Dict:
    """Generate location data for a given city."""
    return {
        "type": "PhysicalLocation",
        "locationName": city_name,
        "countryCode": "DE",
        "postalCode": f"{random.randint(10000, 99999)}",
        "city": city_name,
    }


def generate_package_data() -> Dict:
    """Generate package type and amount data."""
    result = {}
    package_type = random.choice(PACKAGING_TYPES)

    if package_type:
        result["packagingOrTrEqType"] = package_type

        if package_type == "Container-TEU":
            result["packagingOrTrEqAmount"] = (
                "2.00" if random.random() < 0.7 else "2.25"
            )
        elif package_type == "Pallet":
            result["packagingOrTrEqAmount"] = f"{random.randint(1, 26)}.00"
        else:
            result["packagingOrTrEqAmount"] = f"{random.uniform(1, 10):.2f}"

    return result


def calculate_emissions(transport_activity_val: float) -> Dict:
    """Calculate various emission values based on transport activity."""
    emissions = {}

    # Base CO2 calculations
    co2_factor_ttw_per_tkm = random.uniform(0.06, 0.12)
    co2e_ttw_val = transport_activity_val * co2_factor_ttw_per_tkm
    wtw_multiplier = random.uniform(1.15, 1.25)
    co2e_wtw_val = co2e_ttw_val * wtw_multiplier

    emissions["co2_factor_ttw_per_tkm"] = f"{co2_factor_ttw_per_tkm:.3f}"
    emissions["co2eTTW"] = f"{co2e_ttw_val:.3f}"
    emissions["wtw_multiplier"] = f"{wtw_multiplier:.3f}"
    emissions["co2eWTW"] = f"{co2e_wtw_val:.3f}"

    # Optional emissions with probability factors
    if random.random() < 0.8:
        emissions["noxTTW"] = (
            f"{(transport_activity_val * random.uniform(0.0005, 0.003)):.4f}"
        )
    if random.random() < 0.3:
        emissions["soxTTW"] = (
            f"{(transport_activity_val * random.uniform(0.00001, 0.00005)):.5f}"
        )
    if random.random() < 0.5:
        emissions["ch4TTW"] = (
            f"{(transport_activity_val * random.uniform(0.00002, 0.0001)):.5f}"
        )
    if random.random() < 0.7:
        emissions["pmTTW"] = (
            f"{(transport_activity_val * random.uniform(0.00003, 0.00015)):.5f}"
        )

    return emissions


async def main():
    channel = create_insecure_channel(grpc_address="localhost:26500")
    client = ZeebeClient(channel)
    worker = ZeebeWorker(channel)

    @worker.task(task_type="produce_data", exception_handler=on_error)
    def produce_data(
            shipment_id: str = f"SHIP_{uuid.uuid4()}",
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

        # Initialize base TCE data
        tce_data = {
            "tceId": f"TCE_{uuid.uuid4()}",
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
        duration_hours = (distance_km / avg_speed_kmh) * random.uniform(1, 1.2)
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

        # Store and return result
        shipment_key = f"SHIP_{uuid.uuid4()}"

        return {shipment_key: result_dict}

    @worker.task(task_type="send_to_proofing_service", exception_handler=on_error)
    def send_to_proofing_service(**variables) -> None:
        """
        This function simulates sending the data to a proofing service.
        """
        # Simulate sending data to a proofing service
        print("Sending data to proofing service...")
        shipment_data = {
            key: value for key, value in variables.items()
            if key.startswith("SHIP_")
        }
        # Here you would implement the actual logic to send the data
        # For example, using an HTTP request

        with open("activities.json", "w", encoding="utf-8") as f:
            json.dump(shipment_data, f, indent=4, ensure_ascii=False)

        return {
            "message": "Data sent to proofing service successfully.",
        }

    @worker.task(task_type="notify_next_node", exception_handler=on_error)
    async def notify_next_node(message_name: str, shipment_id: str = None) -> None:
        print(f"message_name: {message_name}")
        shipment_id = shipment_id if shipment_id else f"SHIP_ALL_{uuid.uuid4()}"
        # Publish the message to start Process B (message name = 'start-process-b')
        await client.publish_message(
            name=message_name,
            correlation_key=f"case-1-{shipment_id}",
            variables={"shipment_id": shipment_id}
        )
        print(f"Published message {message_name} with shipment ID: {shipment_id}")

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
