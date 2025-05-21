import uuid
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
    distance: dict[str, str]
    transportActivity: str
    co2_factor_ttw_per_tkm: str
    co2eTTW: str
    wtw_multiplier: str
    co2eWTW: str
    origin: dict
    destination: dict
    departureAt: str
    arrivalAt: str

    # Optional fields with default values
    tocId: str | None = None
    hocId: str | None = None
    prevTceIds: list[str] | None = None
    consignmentId: str | None = None
    packagingOrTrEqType: str | None = None
    packagingOrTrEqAmount: str | None = None
    flightNo: str | None = None
    voyageNo: str | None = None
    incoterms: str | None = None
    temperatureControl: str | None = None
    noxTTW: str | None = None
    soxTTW: str | None = None
    ch4TTW: str | None = None
    pmTTW: str | None = None


class SignedTCEData(BaseModel):
    """Model for signed TCE data with cryptographic information."""
    activityDataJson: str
    activitySignature: str
    activityPublicKeyPem: str


class InstanceSCF(BaseModel):
    """Model for SCF data."""
    proof: str
    pcf: float | int


class ProofingResult(BaseModel):
    """Model für das Ergebnis des Proofing-Services."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    instance_scf: InstanceSCF
    timestamp: str | None = None
    status: str | int = 200


