import os

# Zeebe connection settings
ZEEBE_ADDRESS = os.environ.get("ZEEBE_ADDRESS", "localhost:26500")

# kafka connection
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')


# API endpoints
SENSOR_DATA_SERVICE_URL = os.getenv(
    "SENSOR_SERVICE_API_URL", "http://localhost:8000")
VERIFIER_SERVICE_API_URL = os.getenv(
    'VERIFIER_SERVICE_API_URL', "localhost:50051")

# Authentication

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# File paths
ACTIVITIES_OUTPUT_PATH = os.environ.get(
    "ACTIVITIES_OUTPUT_PATH", "activities.json")

# Service timeouts (seconds)
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))
