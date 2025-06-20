import unittest
from unittest.mock import patch
from services.product_footprint import ProductFootprintService
from models.product_footprint import ProductFootprint


class TestProductFootprintService(unittest.TestCase):
    """Test cases for the ProductFootprintService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = ProductFootprintService()

        self.sample_shipment_info = {
            "shipment_id": "SHIP_12345",
            "shipment_weight": 1500.0
        }

        self.company_name = "Test Logistics Company"

    @patch('services.product_footprint_service.log_service_call')
    def test_create_product_footprint_template(self, mock_log):
        """Test creating a product footprint template."""
        result = self.service.create_product_footprint_template(
            self.company_name, self.sample_shipment_info)

        # Verify the result structure
        self.assertIn("product_footprint", result)
        footprint = result["product_footprint"]

        # Verify required fields
        self.assertEqual(footprint["companyName"], self.company_name)
        self.assertEqual(footprint["specVersion"], "2.0.0")
        self.assertEqual(footprint["status"], "Active")
        self.assertIn("id", footprint)
        self.assertIn("created", footprint)

        # Verify extensions
        self.assertTrue(len(footprint["extensions"]) > 0)
        extension_data = footprint["extensions"][0]["data"]
        self.assertEqual(extension_data["shipmentId"], "SHIP_12345")
        self.assertEqual(extension_data["mass"], 1500.0)

        # Verify logging was called
        mock_log.assert_called_once_with(
            "ProductFootprintService.create_product_footprint_template")

    def test_create_basic_template(self):
        """Test creating a basic template."""
        template = self.service.create_basic_template(self.company_name)

        self.assertIsInstance(template, ProductFootprint)
        self.assertEqual(template.companyName, self.company_name)
        self.assertEqual(template.specVersion, "2.0.0")
        self.assertEqual(template.status, "Active")
        self.assertTrue(len(template.extensions) > 0)

    def test_create_basic_template_with_custom_values(self):
        """Test creating a basic template with custom values."""
        custom_shipment_id = "CUSTOM_SHIP_123"
        custom_weight = 2500.0

        template = self.service.create_basic_template(
            self.company_name,
            shipment_id=custom_shipment_id,
            shipment_weight=custom_weight
        )

        self.assertEqual(
            template.extensions[0].data.shipmentId, custom_shipment_id)
        self.assertEqual(template.extensions[0].data.mass, custom_weight)

    def test_validate_shipment_information_valid(self):
        """Test validation with valid shipment information."""
        valid_info = {
            "shipment_id": "SHIP_123",
            "shipment_weight": 1000.0
        }

        self.assertTrue(self.service.validate_shipment_information(valid_info))

    def test_validate_shipment_information_invalid(self):
        """Test validation with invalid shipment information."""
        # Test invalid weight
        invalid_weight = {
            "shipment_id": "SHIP_123",
            "shipment_weight": -100.0
        }
        self.assertFalse(
            self.service.validate_shipment_information(invalid_weight))

        # Test invalid shipment_id
        invalid_id = {
            "shipment_id": "",
            "shipment_weight": 1000.0
        }
        self.assertFalse(
            self.service.validate_shipment_information(invalid_id))

        # Test non-dict input
        self.assertFalse(
            self.service.validate_shipment_information("not_a_dict"))

    def test_update_template_with_custom_data(self):
        """Test updating template with custom data."""
        template = self.service.create_basic_template(self.company_name)

        custom_data = {
            "company_name": "Updated Company",
            "product_description": "Updated description",
            "mass": 3000.0,
            "shipment_id": "UPDATED_SHIP_456"
        }

        updated_template = self.service.update_template_with_custom_data(
            template, custom_data)

        self.assertEqual(updated_template.companyName, "Updated Company")
        self.assertEqual(updated_template.productDescription,
                         "Updated description")
        self.assertEqual(updated_template.extensions[0].data.mass, 3000.0)
        self.assertEqual(
            updated_template.extensions[0].data.shipmentId, "UPDATED_SHIP_456")

        # Verify original template is unchanged
        self.assertEqual(template.companyName, self.company_name)

    def test_custom_configuration(self):
        """Test service with custom configuration."""
        custom_service = ProductFootprintService(
            default_spec_version="3.0.0",
            default_data_schema="https://custom.schema.com/schema.json"
        )

        template = custom_service.create_basic_template(self.company_name)

        self.assertEqual(template.specVersion, "3.0.0")
        self.assertEqual(
            template.extensions[0].dataSchema, "https://custom.schema.com/schema.json")

    def test_create_with_missing_shipment_info(self):
        """Test creating template with missing shipment information."""
        empty_info = {}

        result = self.service.create_product_footprint_template(
            self.company_name, empty_info)

        # Should still work with defaults
        self.assertIn("product_footprint", result)
        footprint = result["product_footprint"]

        # Should have generated defaults
        self.assertIn(
            "SHIP_", footprint["extensions"][0]["data"]["shipmentId"])
        self.assertIsInstance(
            footprint["extensions"][0]["data"]["mass"], float)


if __name__ == '__main__':
    unittest.main()
