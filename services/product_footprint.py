import uuid
import datetime
import random
from typing import Dict, Any, Optional
from models.product_footprint import ProductFootprint, Extension, ExtensionData
from utils.logging_utils import log_service_call


class ProductFootprintService:
    """Service for creating and managing product footprint templates."""

    def __init__(self,
                 default_spec_version: str = "2.0.0",
                 default_data_schema: str = "https://api.ileap.sine.dev/shipment-footprint.json"):

        self.default_spec_version = default_spec_version
        self.default_data_schema = default_data_schema

    def create_product_footprint_template(self,
                                          company_name: str,
                                          shipment_information: Dict[str, Any]) -> Dict[str, Any]:
        log_service_call("ProductFootprintService",
                         "create_product_footprint_template")

        shipment_id = shipment_information.get(
            'shipment_id', f"SHIP_{uuid.uuid4()}")
        shipment_weight = shipment_information.get(
            'shipment_weight', random.uniform(1000, 20000))

        product_footprint = ProductFootprint(
            id=str(uuid.uuid4()),
            created=datetime.datetime.now().isoformat(),
            specVersion=self.default_spec_version,
            version=0,
            status="Active",
            companyName=company_name,
            companyIds=[f"urn:epcidsgln:{uuid.uuid4()}"],
            productDescription=f"Logistics emissions related to shipment with ID {shipment_id}",
            productIds=[
                f"urn:pathfinder:product:customcode:vendor-assigned:{uuid.uuid4()}"],
            productCategoryCpc=random.randint(1000, 9999),
            productNameCompany=f"Shipment with ID {shipment_id}",
            extensions=[
                Extension(
                    dataSchema=self.default_data_schema,
                    data=ExtensionData(
                        mass=shipment_weight,
                        shipmentId=shipment_id
                    )
                )
            ]
        )

        return {
            "product_footprint": product_footprint.model_dump()
        }

    def create_basic_template(self,
                              company_name: str,
                              shipment_id: Optional[str] = None,
                              shipment_weight: Optional[float] = None) -> ProductFootprint:
        log_service_call("ProductFootprintService", "create_basic_template")

        if shipment_id is None:
            shipment_id = f"SHIP_{uuid.uuid4()}"

        if shipment_weight is None:
            shipment_weight = random.uniform(1000, 20000)

        return ProductFootprint(
            id=str(uuid.uuid4()),
            created=datetime.datetime.now().isoformat(),
            specVersion=self.default_spec_version,
            version=0,
            status="Active",
            companyName=company_name,
            companyIds=[f"urn:epcidsgln:{uuid.uuid4()}"],
            productDescription=f"Logistics emissions related to shipment with ID {shipment_id}",
            productIds=[
                f"urn:pathfinder:product:customcode:vendor-assigned:{uuid.uuid4()}"],
            productCategoryCpc=random.randint(1000, 9999),
            productNameCompany=f"Shipment with ID {shipment_id}",
            extensions=[
                Extension(
                    dataSchema=self.default_data_schema,
                    data=ExtensionData(
                        mass=shipment_weight,
                        shipmentId=shipment_id
                    )
                )
            ]
        )

    def validate_shipment_information(self, shipment_information: Dict[str, Any]) -> bool:
        if not isinstance(shipment_information, dict):
            return False

        if 'shipment_weight' in shipment_information:
            weight = shipment_information['shipment_weight']
            if not isinstance(weight, (int, float)) or weight <= 0:
                return False

        if 'shipment_id' in shipment_information:
            shipment_id = shipment_information['shipment_id']
            if not isinstance(shipment_id, str) or not shipment_id.strip():
                return False

        return True
