import unittest
from unittest.mock import patch, MagicMock
from tasks.worker_tasks import CamundaWorkerTasks
from models.proofing_document import ProofingDocument, ProofResponse
from models.product_footprint import ProductFootprint


class TestWorkerTasks(unittest.TestCase):

    def setUp(self):
        self.mock_worker = MagicMock()
        self.mock_client = MagicMock()
        
        self.patches = [
            patch('tasks.worker_tasks.HocTocService'),
            patch('tasks.worker_tasks.SensorDataService'),
            patch('tasks.worker_tasks.ReceiptVerifierService'),
            patch('tasks.worker_tasks.ProofingService'),
            patch('tasks.worker_tasks.ProductFootprintService'),
            patch('tasks.worker_tasks.LogisticsOperationService'),
            patch('tasks.worker_tasks.PCFRegistryService'),
        ]
        
        self.mock_services = {}
        for patch_obj in self.patches:
            mock_service = patch_obj.start()
            service_name = patch_obj.attribute.split('.')[-1]
            self.mock_services[service_name] = mock_service
        
        self.worker_tasks = CamundaWorkerTasks(self.mock_worker, self.mock_client)

    def tearDown(self):
        for patch_obj in self.patches:
            patch_obj.stop()

    def _create_test_proofing_document(self):
        product_footprint = ProductFootprint(
            id="test-id",
            created="2023-01-01T00:00:00Z",
            companyName="Test Company",
            companyIds=["company-id-1"],
            productDescription="Test Product",
            productIds=["product-id-1"],
            productCategoryCpc=123,
            productNameCompany="Test Product Name"
        )

        proof_response = ProofResponse(
            productFootprintId="test-id",
            proofReceipt="test-receipt-data",
            proofReference="test-reference",
            pcf=10.5,
            imageId="test-image-id"
        )

        return ProofingDocument(
            productFootprint=product_footprint,
            proof=[proof_response],
            tocData=[],
            hocData=[]
        )

    def test_upload_proof_to_pcf_registry(self):
        """Test the upload_proof_to_pcf_registry task."""
        proofing_document = self._create_test_proofing_document()
        proofing_document_dict = proofing_document.model_dump()

        result = self.worker_tasks.upload_proof_to_pcf_registry(proofing_document_dict)

        self.worker_tasks.pcf_registry_service.upload_proofing_document.assert_called_once_with(
            "test-id", proofing_document.proof[-1]
        )

        expected_result = {
            "proof_upload_status": "upload_successful",
            "proofing_document_id": "test-id"
        }
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
