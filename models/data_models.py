from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


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


class Distance(BaseModel):
    actual: Optional[float] = None
    gcd: Optional[float] = None
    sfd: Optional[float] = None


class TCE(BaseModel):
    tceId: str
    prevTceIds: List[str] = []
    hocId: Optional[str] = None
    tocId: Optional[str] = None
    shipmentId: str
    mass: float
    co2eWTW: Optional[float] = None
    co2eTTW: Optional[float] = None
    transportActivity: Optional[float] = None
    distance: Optional[Distance] = None


class ExtensionData(BaseModel):
    mass: float
    shipmentId: str
    tces: List[TCE] = Field(default_factory=list)


class Extension(BaseModel):
    specVersion: str = "2.0.0"
    dataSchema: str
    data: ExtensionData


class ProductFootprint(BaseModel):
    id: str
    specVersion: str = "2.0.0"
    version: int = 0
    created: str
    status: str = "Active"
    companyName: str
    companyIds: List[str]
    productDescription: str
    productIds: List[str]
    productCategoryCpc: int
    productNameCompany: str
    pcf: Optional[float] = None
    comment: str = ""
    extensions: List[Extension] = Field(default_factory=list)
