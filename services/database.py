from models.database import HocTocDatabase
from models.proofing_document import ProofingDocument
from models.product_footprint import ProductFootprint
from typing import Optional, Dict, Any
import sqlite3
import json

from models.sensor_data import TceSensorData
from utils.data_utils import get_mock_data
from models.logistics_operations import HocData, TocData


class HocTocService:
    def __init__(self):
        self.db = HocTocDatabase()
        # One-time setup: populate database if empty
        self._populate_database_if_needed()

    def _populate_database_if_needed(self):
        """Populate database from mock data if it's empty."""
        # Check if database has data
        test_data = self.get_hoc_data("100")
        if test_data is None:
            self.db.populate_from_mock_data(get_mock_data)

    def get_hoc_data(self, hoc_id: str) -> Optional[Dict[str, Any]]:
        """Get HOC data by ID."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM hoc_data WHERE hoc_id = ?', (hoc_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "hocId": row[0],
                "passhubType": row[1],
                "energyCarriers": json.loads(row[2]),
                "co2eIntensityWTW": row[3],
                "co2eIntensityTTW": row[4],
                "hubActivityUnit": row[5]
            }
        return None

    def get_toc_data(self, toc_id: str) -> Optional[Dict[str, Any]]:
        """Get TOC data by ID."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM toc_data WHERE toc_id = ?', (toc_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "tocId": row[0],
                "certifications": json.loads(row[1]),
                "description": row[2],
                "mode": row[3],
                "loadFactor": row[4],
                "emptyDistanceFactor": row[5],
                "temperatureControl": row[6],
                "truckLoadingSequence": row[7],
                "airShippingOption": row[8],
                "flightLength": row[9],
                "energyCarriers": json.loads(row[10]),
                "co2eIntensityWTW": row[11],
                "co2eIntensityTTW": row[12],
                "transportActivityUnit": row[13]
            }
        return None

    def get_transport_data(self, id: str) -> Optional[Dict[str, Any]]:
        """Get data from database by ID, checking HOC and TOC tables."""

        data = self.get_hoc_data(id)
        if data:
            return data

        data = self.get_toc_data(id)
        if data:
            return data

        return None

    def collect_hoc_toc_data(self, product_footprint: dict, sensor_data: Optional[list[dict]] = None) -> dict:
        """Collect HOC and TOC data based on product footprint and return a proofing document."""
        product_footprint_verified = ProductFootprint.model_validate(
            product_footprint)
        proofingDocument = ProofingDocument(
            productFootprint=product_footprint_verified,
            tocData=[],
            hocData=[],
            signedSensorData=[] if sensor_data is None else [
                TceSensorData.model_validate(sd) for sd in sensor_data
            ]
        )

        for ids in product_footprint_verified.extensions[0].data.tces:
            if ids.tocId is not None:
                raw_data = self.get_transport_data(ids.tocId)
                if raw_data:
                    # Validate through Pydantic model first
                    validated_toc_data = TocData.model_validate(raw_data)
                    proofingDocument.tocData.append(validated_toc_data)
            if ids.hocId is not None:
                raw_data = self.get_transport_data(ids.hocId)
                if raw_data:
                    # Validate through Pydantic model first
                    validated_hoc_data = HocData.model_validate(raw_data)
                    proofingDocument.hocData.append(validated_hoc_data)

        result = {
            "proofing_document": proofingDocument.model_dump()
        }
        return result
