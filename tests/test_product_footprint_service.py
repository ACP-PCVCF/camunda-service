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
