import datetime
import random
from typing import Dict

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

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
