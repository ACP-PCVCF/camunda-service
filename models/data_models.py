from typing import Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class Location:
    """Data class for location information."""
    type: str = "PhysicalLocation"
    locationName: str = ""
    countryCode: str = "DE"
    postalCode: str = ""
    city: str = ""

@dataclass
class TCEData:
    """Data class for Transport Carbon Emission (TCE) data."""
    tceId: str
    shipmentId: str
    mass: str
    distance: Dict[str, str]
    transportActivity: str
    co2_factor_ttw_per_tkm: str
    co2eTTW: str
    wtw_multiplier: str
    co2eWTW: str
    origin: Dict
    destination: Dict
    departureAt: str
    arrivalAt: str
    
    # Optional fields with default values
    tocId: Optional[str] = None
    hocId: Optional[str] = None
    prevTceIds: Optional[List[str]] = None
    consignmentId: Optional[str] = None
    packagingOrTrEqType: Optional[str] = None
    packagingOrTrEqAmount: Optional[str] = None
    flightNo: Optional[str] = None
    voyageNo: Optional[str] = None
    incoterms: Optional[str] = None
    temperatureControl: Optional[str] = None
    noxTTW: Optional[str] = None
    soxTTW: Optional[str] = None
    ch4TTW: Optional[str] = None
    pmTTW: Optional[str] = None

@dataclass
class SignedTCEData:
    """Data class for signed TCE data with cryptographic information."""
    activityDataJson: str
    activitySignature: str
    activityPublicKeyPem: str