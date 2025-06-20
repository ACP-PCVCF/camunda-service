from services.verifier_service import ReceiptVerifierService
import unittest


class TestReceiptVerifierService(unittest.IsolatedAsyncioTestCase):
    """Test cases for ReceiptVerifierService."""
    service: ReceiptVerifierService = None

    def setUp(self):
        """Set up test case resources."""
        self.service = ReceiptVerifierService()
        print("Setting up test case resources.")

    def tearDown(self):
        """Tear down test case resources."""
        print("Tearing down test case resources.")

    async def test_verify_receipt_stream(self):
        """Test the VerifyReceiptStream method."""
        await self.service.VerifyReceiptStream()
        print("Tested VerifyReceiptStream method.")


if __name__ == "__main__":
    unittest.main()
    print("Running ReceiptVerifierService tests.")
