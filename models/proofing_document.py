from typing import Optional
from pydantic import BaseModel
from models.product_footprint import ProductFootprint
from models.logistics_operations import TocData, HocData
from models.sensor_data import TceSensorData


class ProofingDocument(BaseModel):
    productFootprint: ProductFootprint
    tocData: list[TocData]
    hocData: list[HocData]
    signedSensorData: Optional[list[TceSensorData]] = None


class ProofResponse(BaseModel):
    productFootprintId: str
    proofReceipt: str
    proofReference: str
    pcf: float
    imageId: str
