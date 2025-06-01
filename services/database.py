from models.database import HocTocDatabase
from models.proofing_document import ProofingDocument
from models.product_footprint import ProductFootprint
from typing import Optional, Dict, Any
from utils.data_utils import get_mock_data


class HocTocService:
    def __init__(self):
        self.db = HocTocDatabase()
        # One-time setup: populate database if empty
        self._populate_database_if_needed()

    def _populate_database_if_needed(self):
        """Populate database from mock data if it's empty."""
        # Check if database has data
        test_data = self.db.get_hoc_data("100")
        if test_data is None:
            self.db.populate_from_mock_data(get_mock_data)

    def get_transport_data(self, id: str) -> Optional[Dict[str, Any]]:
        """Get data from database (replaces get_mock_data)."""

        data = self.db.get_hoc_data(id)
        if data:
            return data

        data = self.db.get_toc_data(id)
        if data:
            return data

        return None

    def collect_hoc_toc_data(self, product_footprint: dict):
        """Your existing method, updated to use database."""
        product_footprint_verified = ProductFootprint.model_validate(
            product_footprint)
        proofingDocument = ProofingDocument(
            productFootprint=product_footprint_verified,
            tocData=[],
            hocData=[]
        )

        for ids in product_footprint_verified.extensions[0].data.tces:
            if ids.tocId is not None:
                data = self.get_transport_data(ids.tocId)
                if data:
                    proofingDocument.tocData.append(data)
            if ids.hocId is not None:
                data = self.get_transport_data(ids.hocId)
                if data:
                    proofingDocument.hocData.append(data)

        result = {
            "proofing_document": proofingDocument.model_dump()
        }
        return result
