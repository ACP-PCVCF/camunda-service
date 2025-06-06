from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding


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


def get_mock_data(id: str):
    """Generate mock data for testing purposes."""

    mock_hoc_data = {
        "100": {
            "hocId": "100",
            "passhubType": "Charging Hub",
            "energyCarriers": [
                {
                    "energyCarrier": "Electricity",
                    "relativeShare": "1.0",  # 100% electricity
                    "emissionFactorWTW": "25",  # Grid mix electricity
                    "emissionFactorTTW": "0"    # Zero at point of use for electric
                }
            ],
            "co2eIntensityWTW": "25",
            "co2eIntensityTTW": "0",
            "hubActivityUnit": "kWh delivered"
        },
        "101": {
            "hocId": "101",
            "passhubType": "Refuelling Hub",
            "energyCarriers": [
                {
                    "energyCarrier": "Hydrogen",
                    "relativeShare": "0.8",  # 80% hydrogen
                    # Steam Methane Reforming (SMR) H2
                    "emissionFactorWTW": "70",
                    "emissionFactorTTW": "0"    # Zero for FCEV
                },
                {
                    "energyCarrier": "Diesel",
                    "relativeShare": "0.2",  # 20% diesel
                    "emissionFactorWTW": "95",
                    "emissionFactorTTW": "73"
                }
            ],
            "co2eIntensityWTW": "70",
            "co2eIntensityTTW": "0",
            "hubActivityUnit": "kg dispensed"
        },
        "102": {
            "hocId": "102",
            "passhubType": "Logistics Hub",
            "energyCarriers": [
                {
                    "energyCarrier": "Electricity",
                    "relativeShare": "0.3",  # 30% electricity
                    "emissionFactorWTW": "25",
                    "emissionFactorTTW": "0"
                },
                {
                    "energyCarrier": "Diesel",
                    "relativeShare": "0.7",  # 70% diesel
                    "emissionFactorWTW": "95",
                    "emissionFactorTTW": "73"
                }
            ],
            "co2eIntensityWTW": "95",
            "co2eIntensityTTW": "73",
            "hubActivityUnit": "number of vehicles serviced"
        },
        "103": {
            "hocId": "103",
            "passhubType": "Multi-modal Energy Hub",
            "energyCarriers": [
                {
                    "energyCarrier": "Electricity",
                    "relativeShare": "0.4",  # 40% electricity
                    "emissionFactorWTW": "25",
                    "emissionFactorTTW": "0"
                },
                {
                    "energyCarrier": "HVO100",
                    "relativeShare": "0.35",  # 35% HVO100
                    "emissionFactorWTW": "20",  # Lower carbon biofuel
                    "emissionFactorTTW": "15"
                },
                {
                    "energyCarrier": "CNG",
                    "relativeShare": "0.25",  # 25% CNG
                    "emissionFactorWTW": "55",
                    "emissionFactorTTW": "50"
                }
            ],
            "co2eIntensityWTW": "30",
            "co2eIntensityTTW": "20",
            "hubActivityUnit": "energy delivered (MJ)"
        },
        "200": {
            "tocId": "200",
            "certifications": ["ISO14083:2023", "GLECv3"],
            "description": "Standard Diesel Truck - Long Haul",
            "mode": "road",
            "loadFactor": "0.80",
            "emptyDistanceFactor": "0.10",
            "temperatureControl": "Ambient",
            "truckLoadingSequence": "LIFO",
            "airShippingOption": None,
            "flightLength": None,
            "energyCarriers": [
                {
                    "energyCarrier": "Diesel",
                    "relativeShare": "1.0",  # 100% diesel
                    "emissionFactorWTW": "85",
                    "emissionFactorTTW": "75"
                }
            ],
            "co2eIntensityWTW": "85",
            "co2eIntensityTTW": "75",
            "transportActivityUnit": "tkm"
        },
        "201": {
            "tocId": "201",
            "certifications": ["GLECv3.1"],
            "description": "Electric Van - Urban Delivery",
            "mode": "road",
            "loadFactor": "0.65",
            "emptyDistanceFactor": "0.05",
            "temperatureControl": "None",
            "truckLoadingSequence": "Optimized Route",
            "airShippingOption": None,
            "flightLength": None,
            "energyCarriers": [
                {
                    "energyCarrier": "Electricity",
                    "relativeShare": "1.0",  # 100% electricity
                    "emissionFactorWTW": "30",
                    "emissionFactorTTW": "0"
                }
            ],
            "co2eIntensityWTW": "30",
            "co2eIntensityTTW": "0",
            "transportActivityUnit": "vkm"
        },
        "202": {
            "tocId": "202",
            "certifications": ["ISO14083:2023", "GLECv2"],
            "description": "Air Freight - International Cargo",
            "mode": "air",
            "loadFactor": "0.70",
            "emptyDistanceFactor": "0.02",
            "temperatureControl": "Refrigerated +2C to +8C",
            "truckLoadingSequence": "None",
            "airShippingOption": "Dedicated Cargo Aircraft",
            "flightLength": "Long Haul (>4000km)",
            "energyCarriers": [
                {
                    "energyCarrier": "Jet Fuel (Kerosene)",
                    "relativeShare": "1.0",  # 100% jet fuel
                    "emissionFactorWTW": "700",
                    "emissionFactorTTW": "650"
                }
            ],
            "co2eIntensityWTW": "700",
            "co2eIntensityTTW": "650",
            "transportActivityUnit": "tkm"
        },
        "203": {
            "tocId": "203",
            "certifications": ["GLECv3", "ISO14083:2023"],
            "description": "Electric Rail Freight - National",
            "mode": "rail",
            "loadFactor": "0.90",
            "emptyDistanceFactor": "0.03",
            "temperatureControl": "Ambient",
            "truckLoadingSequence": "None",
            "airShippingOption": None,
            "flightLength": None,
            "energyCarriers": [
                {
                    "energyCarrier": "Electricity",
                    "relativeShare": "1.0",  # 100% electricity
                    "emissionFactorWTW": "15",
                    "emissionFactorTTW": "0"
                }
            ],
            "co2eIntensityWTW": "15",
            "co2eIntensityTTW": "0",
            "transportActivityUnit": "tkm"
        },
        "204": {
            "tocId": "204",
            "certifications": ["GLECv3.1"],
            "description": "Container Ship - Transoceanic",
            "mode": "sea",
            "loadFactor": "0.85",
            "emptyDistanceFactor": "0.08",
            "temperatureControl": "Controlled Atmosphere (Fruits)",
            "truckLoadingSequence": "None",
            "airShippingOption": None,
            "flightLength": None,
            "energyCarriers": [
                {
                    "energyCarrier": "Heavy Fuel Oil (HFO)",
                    "relativeShare": "0.8",  # 80% HFO
                    "emissionFactorWTW": "12",
                    "emissionFactorTTW": "11"
                },
                {
                    "energyCarrier": "Marine Gas Oil (MGO)",
                    "relativeShare": "0.2",  # 20% MGO for ECA zones
                    "emissionFactorWTW": "8",
                    "emissionFactorTTW": "7"
                }
            ],
            "co2eIntensityWTW": "10",
            "co2eIntensityTTW": "9",
            "transportActivityUnit": "tkm"
        }
    }

    return mock_hoc_data.get(id, None)
