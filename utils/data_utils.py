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
                    # Dimensionless (fraction)
                    "distributionEfficiency": "0.98",
                    "energyDensity": "1 kWh/unit",    # As per documentation example for electricity
                    "unit": "kWh"
                }
            ],
            "co2eIntensityWTW": "25 gCO2e/MJ",    # Example: Grid mix electricity
            "co2eIntensityTTW": "0 gCO2e/MJ",     # For electric vehicles at point of use
            "hubActivityUnit": "kWh delivered"
        },
        "101": {
            "hocId": "101",
            "passhubType": "Refuelling Hub",
            "energyCarriers": [
                {
                    "energyCarrier": "Hydrogen",
                    "distributionEfficiency": "0.90",
                    "energyDensity": "33.3 kWh/kg",   # Approx. 120 MJ/kg
                    "unit": "kg"
                },
                {
                    "energyCarrier": "Diesel",
                    "distributionEfficiency": "0.99",
                    "energyDensity": "10.7 kWh/L",   # Approx. 38.6 MJ/L
                    "unit": "L"
                }
            ],
            # Assuming these intensities are primarily for Hydrogen at this hub
            # Example: Steam Methane Reforming (SMR) H2
            "co2eIntensityWTW": "70 gCO2e/MJ",
            # For Fuel Cell Electric Vehicles (FCEV)
            "co2eIntensityTTW": "0 gCO2e/MJ",
            "hubActivityUnit": "kg dispensed"     # e.g., kg of Hydrogen
        },
        "102": {
            "hocId": "102",
            "passhubType": "Logistics Hub",
            "energyCarriers": [
                {
                    "energyCarrier": "Electricity",
                    "distributionEfficiency": "0.97",
                    "energyDensity": "1 kWh/unit",
                    "unit": "kWh"
                },
                {
                    "energyCarrier": "Diesel",
                    "distributionEfficiency": "0.99",
                    "energyDensity": "10.7 kWh/L",
                    "unit": "L"
                }
            ],
            # Assuming these intensities are predominantly related to Diesel for trucks
            "co2eIntensityWTW": "95 gCO2e/MJ",    # WTW for fossil Diesel
            "co2eIntensityTTW": "73 gCO2e/MJ",    # TTW for Diesel combustion
            "hubActivityUnit": "number of vehicles serviced"
        },
        "103": {
            "hocId": "103",
            "passhubType": "Multi-modal Energy Hub",
            "energyCarriers": [
                {
                    "energyCarrier": "Electricity",
                    "distributionEfficiency": "0.96",
                    "energyDensity": "1 kWh/unit",
                    "unit": "kWh"
                },
                {
                    "energyCarrier": "HVO100",  # Hydrotreated Vegetable Oil
                    "distributionEfficiency": "0.98",
                    "energyDensity": "9.2 kWh/L",  # Approx. energy density
                    "unit": "L"
                },
                {
                    "energyCarrier": "CNG",     # Compressed Natural Gas
                    "distributionEfficiency": "0.92",
                    "energyDensity": "13.9 kWh/kg",  # Approx. 50 MJ/kg by mass
                    "unit": "kg"               # Typically sold by mass
                }
            ],
            # Example: blended/average values for a hub focusing on lower carbon options
            "co2eIntensityWTW": "30 gCO2e/MJ",
            # Reflects some combustion but lower than pure fossil
            "co2eIntensityTTW": "20 gCO2e/MJ",
            "hubActivityUnit": "energy delivered (MJ)"
        },
        "200": {
            "tocId": "200",
            "certifications": ["ISO_14001", "ECO_TRANSIT_CERT"],
            "description": "Standard Diesel Truck - Long Haul",
            "mode": "Road",  # Assuming TransportMode is a string, could be an Enum
            "loadFactor": "0.80",  # Dimensionless (fraction)
            "emptyDistanceFactor": "0.10",  # Dimensionless (fraction)
            "temperatureControl": "Ambient",
            "truckLoadingSequence": "LIFO",  # Last-In, First-Out
            "airShippingOption": None,
            "flightLength": None,
            "energyCarriers": [
                {
                    "energyCarrier": "Diesel",
                    "distributionEfficiency": "0.99",  # Assumed high for direct fueling
                    "energyDensity": "10.7 kWh/L",   # Approx. 38.6 MJ/L
                    "unit": "L"
                }
            ],
            "co2eIntensityWTW": "85 gCO2e/tkm",  # Well-to-Wheel, per tonne-kilometer
            "co2eIntensityTTW": "75 gCO2e/tkm",  # Tank-to-Wheel, per tonne-kilometer
            "transportActivityUnit": "tkm"
        },
        "201": {
            "tocId": "201",
            "certifications": ["GREEN_LOGISTICS_PARTNER"],
            "description": "Electric Van - Urban Delivery",
            "mode": "Road",
            "loadFactor": "0.65",
            "emptyDistanceFactor": "0.05",
            "temperatureControl": "None",
            "truckLoadingSequence": "Optimized Route",
            "airShippingOption": None,
            "flightLength": None,
            "energyCarriers": [
                {
                    "energyCarrier": "Electricity",
                    "distributionEfficiency": "0.95",  # Grid to vehicle charging efficiency
                    "energyDensity": "1 kWh/unit",    # Standard for electricity
                    "unit": "kWh"
                }
            ],
            # Lower due to electric, depends on grid mix
            "co2eIntensityWTW": "30 gCO2e/tkm",
            "co2eIntensityTTW": "0 gCO2e/tkm",     # Zero at point of use for EV
            "transportActivityUnit": "vkm"  # Vehicle-kilometer, common for urban delivery
        },
        "202": {
            "tocId": "202",
            "certifications": ["IATA_CEIV_PHARMA"],
            "description": "Air Freight - International Cargo",
            "mode": "Air",
            "loadFactor": "0.70",
            "emptyDistanceFactor": "0.02",  # Less applicable in same way as road
            "temperatureControl": "Refrigerated +2C to +8C",
            "truckLoadingSequence": None,  # Not applicable
            "airShippingOption": "Dedicated Cargo Aircraft",
            "flightLength": "Long Haul (>4000km)",
            "energyCarriers": [
                {
                    "energyCarrier": "Jet Fuel (Kerosene)",
                    "distributionEfficiency": "0.99",
                    "energyDensity": "12.0 kWh/kg",  # Approx. 43.1 MJ/kg
                    "unit": "kg"  # Often measured in kg or tonnes for aviation
                }
            ],
            "co2eIntensityWTW": "700 gCO2e/tkm",  # Significantly higher for air freight
            "co2eIntensityTTW": "650 gCO2e/tkm",
            "transportActivityUnit": "tkm"
        },
        "203": {
            "tocId": "203",
            "certifications": ["RAIL_SUSTAINABILITY_CHARTER"],
            "description": "Electric Rail Freight - National",
            "mode": "Rail",
            "loadFactor": "0.90",  # Typically high for rail
            "emptyDistanceFactor": "0.03",
            "temperatureControl": "Ambient",
            "truckLoadingSequence": None,  # Not applicable
            "airShippingOption": None,
            "flightLength": None,
            "energyCarriers": [
                {
                    "energyCarrier": "Electricity",
                    "distributionEfficiency": "0.92",  # From grid to locomotive
                    "energyDensity": "1 kWh/unit",
                    "unit": "kWh"
                }
            ],
            "co2eIntensityWTW": "15 gCO2e/tkm",  # Very low for electric rail
            "co2eIntensityTTW": "0 gCO2e/tkm",  # If fully electric
            "transportActivityUnit": "tkm"
        },
        "204": {
            "tocId": "204",
            "certifications": ["MARITIME_ECO_SHIP"],
            "description": "Container Ship - Transoceanic",
            "mode": "Sea",
            "loadFactor": "0.85",
            "emptyDistanceFactor": "0.08",  # For empty container repositioning
            "temperatureControl": "Controlled Atmosphere (Fruits)",
            "truckLoadingSequence": None,  # Not applicable
            "airShippingOption": None,
            "flightLength": None,
            "energyCarriers": [
                {
                    "energyCarrier": "Heavy Fuel Oil (HFO)",
                    "distributionEfficiency": "0.98",
                    "energyDensity": "11.5 kWh/kg",  # Approx. 41.3 MJ/kg
                    "unit": "tonne"  # Marine fuels often in tonnes
                },
                {
                    "energyCarrier": "Marine Gas Oil (MGO)",  # For ECA zones
                    "distributionEfficiency": "0.98",
                    "energyDensity": "11.9 kWh/kg",  # Approx. 42.7 MJ/kg
                    "unit": "tonne"
                }
            ],
            # Very low per tkm due to scale, but high absolute
            "co2eIntensityWTW": "10 gCO2e/tkm",
            "co2eIntensityTTW": "9 gCO2e/tkm",  # HFO is carbon intensive
            "transportActivityUnit": "tkm"
        }
    }

    return mock_hoc_data.get(id, None)
