import sqlite3
import json
from config.database_config import DatabaseConfig


class HocTocDatabase:
    def __init__(self):
        self.db_path = DatabaseConfig.DB_PATH
        self.timeout = DatabaseConfig.TIMEOUT
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create HOC (Hub of Consumption) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hoc_data (
                hoc_id TEXT PRIMARY KEY,
                passhub_type TEXT,
                energy_carriers TEXT,  -- JSON string
                co2e_intensity_wtw TEXT,
                co2e_intensity_ttw TEXT,
                hub_activity_unit TEXT
            )
        ''')

        # Create TOC (Transport Operation Category) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS toc_data (
                toc_id TEXT PRIMARY KEY,
                certifications TEXT,  -- JSON string
                description TEXT,
                mode TEXT,
                load_factor TEXT,
                empty_distance_factor TEXT,
                temperature_control TEXT,
                truck_loading_sequence TEXT,
                air_shipping_option TEXT,
                flight_length TEXT,
                energy_carriers TEXT,  -- JSON string
                co2e_intensity_wtw TEXT,
                co2e_intensity_ttw TEXT,
                transport_activity_unit TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def populate_from_mock_data(self, mock_data_function):
        """Populate database from your existing mock data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        all_ids = ["100", "101", "102", "103",
                   "200", "201", "202", "203", "204"]

        for id_val in all_ids:
            data = mock_data_function(id_val)
            if data is None:
                continue

            if "hocId" in data:
                cursor.execute('''
                    INSERT OR REPLACE INTO hoc_data 
                    (hoc_id, passhub_type, energy_carriers, co2e_intensity_wtw, 
                     co2e_intensity_ttw, hub_activity_unit)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    data["hocId"],
                    data["passhubType"],
                    json.dumps(data["energyCarriers"]),
                    data["co2eIntensityWTW"],
                    data["co2eIntensityTTW"],
                    data["hubActivityUnit"]
                ))

            elif "tocId" in data:
                cursor.execute('''
                    INSERT OR REPLACE INTO toc_data 
                    (toc_id, certifications, description, mode, load_factor, 
                     empty_distance_factor, temperature_control, truck_loading_sequence,
                     air_shipping_option, flight_length, energy_carriers, 
                     co2e_intensity_wtw, co2e_intensity_ttw, transport_activity_unit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data["tocId"],
                    json.dumps(data.get("certifications", [])),
                    data["description"],
                    data["mode"],
                    data["loadFactor"],
                    data["emptyDistanceFactor"],
                    data.get("temperatureControl"),
                    data.get("truckLoadingSequence"),
                    data.get("airShippingOption"),
                    data.get("flightLength"),
                    json.dumps(data["energyCarriers"]),
                    data["co2eIntensityWTW"],
                    data["co2eIntensityTTW"],
                    data["transportActivityUnit"]
                ))

        conn.commit()
        conn.close()
