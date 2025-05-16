from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Location(BaseModel):
    """Model for location information."""
    type: str = "PhysicalLocation"
    locationName: str = ""
    countryCode: str = Field(default="DE", min_length=2, max_length=2)
    postalCode: str = ""
    city: str = ""

class TCEData(BaseModel):
    """Model for Transport Carbon Emission (TCE) data."""
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

class SignedTCEData(BaseModel):
    """Model for signed TCE data with cryptographic information."""
    activityDataJson: str
    activitySignature: str
    activityPublicKeyPem: str