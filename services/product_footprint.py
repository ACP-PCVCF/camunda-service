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
        """
        Initialize the ProductFootprintService.

        Args:
            default_spec_version: Default specification version for product footprints
            default_data_schema: Default data schema URL for extensions
        """
        self.default_spec_version = default_spec_version
        self.default_data_schema = default_data_schema

    def create_product_footprint_template(self,
                                          company_name: str,
                                          shipment_information: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a product footprint template for logistics emissions tracking.

        Args:
            company_name: Name of the company creating the footprint
            shipment_information: Dictionary containing shipment details
                                 Expected keys: 'shipment_id', 'shipment_weight'

        Returns:
            Dictionary containing the created product footprint
        """
        log_service_call("ProductFootprintService",
                         "create_product_footprint_template")

        # Extract shipment information with defaults
        shipment_id = shipment_information.get(
            'shipment_id', f"SHIP_{uuid.uuid4()}")
        shipment_weight = shipment_information.get(
            'shipment_weight', random.uniform(1000, 20000))

        # Create the product footprint
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
        """
        Create a basic product footprint template with minimal required information.

        Args:
            company_name: Name of the company
            shipment_id: Optional shipment ID (generated if not provided)
            shipment_weight: Optional shipment weight (random if not provided)

        Returns:
            ProductFootprint instance
        """
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
        """
        Validate shipment information dictionary.

        Args:
            shipment_information: Dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(shipment_information, dict):
            return False

        # Check if shipment_weight is valid if provided
        if 'shipment_weight' in shipment_information:
            weight = shipment_information['shipment_weight']
            if not isinstance(weight, (int, float)) or weight <= 0:
                return False

        # Check if shipment_id is valid if provided
        if 'shipment_id' in shipment_information:
            shipment_id = shipment_information['shipment_id']
            if not isinstance(shipment_id, str) or not shipment_id.strip():
                return False

        return True

    def update_template_with_custom_data(self,
                                         template: ProductFootprint,
                                         custom_data: Dict[str, Any]) -> ProductFootprint:
        """
        Update an existing template with custom data.

        Args:
            template: Existing ProductFootprint template
            custom_data: Dictionary containing custom data to update

        Returns:
            Updated ProductFootprint instance
        """
        log_service_call("ProductFootprintService",
                         "update_template_with_custom_data")

        # Create a copy of the template
        updated_template = template.model_copy(deep=True)

        # Update fields if provided in custom_data
        if 'company_name' in custom_data:
            updated_template.companyName = custom_data['company_name']

        if 'product_description' in custom_data:
            updated_template.productDescription = custom_data['product_description']

        if 'product_category_cpc' in custom_data:
            updated_template.productCategoryCpc = custom_data['product_category_cpc']

        # Update extension data if provided
        if 'mass' in custom_data and updated_template.extensions:
            updated_template.extensions[0].data.mass = custom_data['mass']

        if 'shipment_id' in custom_data and updated_template.extensions:
            updated_template.extensions[0].data.shipmentId = custom_data['shipment_id']

        return updated_template
