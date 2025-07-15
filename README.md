# Camunda Service

A Python-based microservice for handling Camunda/Zeebe workflow tasks in a transport carbon emission (TCE) tracking system. This service connects to a Zeebe workflow engine and orchestrates interactions with various external services for sensor data collection, PCF registry, receipt verification, and carbon footprint proofing.

## Overview

This service implements a worker that connects to Camunda 8 Zeebe engine and acts as an orchestrator for carbon footprint tracking workflows. It manages the complete lifecycle of transport emission tracking including:

- **Workflow Orchestration**: Handles Zeebe workflow tasks for transport carbon emission tracking
- **Data Integration**: Collects sensor data from transport operations
- **Product Footprint Management**: Creates and manages Product Carbon Footprint templates
- **Proof Generation**: Integrates with proofing services via Kafka messaging
- **Receipt Verification**: Verifies transport receipts through gRPC services
- **Registry Integration**: Interfaces with PCF registry for proof storage and retrieval
- **Logistics Operations**: Manages hub and transport procedures with TCE data tracking

## Architecture

The service is built around several core components:

- **Worker Tasks** (`tasks/worker_tasks.py`): Zeebe task handlers
- **Services Layer** (`services/`): Modular services for different functionalities
- **Data Models** (`models/`): Pydantic models for data validation
- **Configuration** (`config/`): Environment-based configuration management
- **Utilities** (`utils/`): Logging, error handling, and Kafka utilities

## Requirements

- Python 3.12+ (Docker uses 3.12-slim)
- Zeebe Server (Camunda 8 Platform)
- Dependencies listed in `requirements.txt`

## Installation

### Local Development

1. Clone this repository
2. Create a virtual environment (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

### Docker Deployment

Build and run using Docker:
```bash
docker build -t camunda-service:latest .
docker run -e ZEEBE_ADDRESS=your-zeebe-gateway:26500 camunda-service:latest
```

### Kubernetes Deployment

Deploy to Kubernetes using the provided manifest:
```bash
kubectl apply -f k8s/camunda-service.yaml
```

## Configuration

Configure the service through environment variables or by editing `config/settings.py`:

### Core Settings
- `ZEEBE_ADDRESS`: Zeebe gateway address (default: `localhost:26500`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### External Services
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka bootstrap servers (default: `localhost:9092`)
- `SENSOR_DATA_SERVICE_URL`: Sensor data service endpoint (default: `http://localhost:8000`)
- `VERIFIER_SERVICE_API_URL`: Receipt verifier gRPC service (default: `localhost:50051`)
- `PCF_REGISTRY_SERVER_ADDRESS`: PCF registry gRPC service (default: `localhost:50052`)

### Additional Settings
- `REQUEST_TIMEOUT`: Service request timeout in seconds (default: `30`)

## Usage

Start the service by running:

```bash
python main.py
```

The service will:

1. Connect to the configured Zeebe gateway
2. Initialize all service dependencies (database, Kafka, gRPC clients)
3. Register task handlers for workflow orchestration
4. Begin processing tasks from the workflow engine

### Available Zeebe Tasks

The service registers the following task handlers:

1. **`determine_job_sequence`** - Determines workflow execution sequence
2. **`send_to_proofing_service`** - Sends documents to proofing service via Kafka
3. **`notify_next_node`** - Publishes messages to notify downstream workflow nodes
4. **`send_data_to_origin`** - Returns processed data to workflow origin
5. **`define_product_footprint_template`** - Creates PCF templates for shipments
6. **`hub_procedure`** - Executes hub-based logistics operations
7. **`transport_procedure`** - Handles transport logistics with sensor data integration
8. **`set_shipment_information`** - Initializes shipment metadata
9. **`collect_hoc_toc_data`** - Collects hub and transport data
10. **`verify_receipt`** - Verifies proof receipts via gRPC
11. **`consume_proof_response`** - Consumes proof responses from Kafka and uploads proofs to PCF registry
12. **`get_proof_from_pcf_registry`** - Downloads proofs from PCF registry

### Monitoring and Logging

The service provides comprehensive logging for all operations. Logs are written to:
- Console output (configurable log level)
- Log files in `logs/camunda_service.log`

### Development Scripts

The repository includes helpful scripts in `data/scripts/`:
- **`camunda_forward.sh`** - Sets up port forwarding for Camunda Platform services
- **`camunda-service-rollout.sh`** - Automates Kubernetes deployment and rollout

## Development

### Project Structure

```
├── config/              # Configuration management
├── data/               # BPMN files, example data, and scripts
├── k8s/                # Kubernetes deployment manifests
├── logs/               # Application logs
├── models/             # Pydantic data models
├── services/           # Business logic services
│   ├── pb/            # gRPC protocol buffer files
│   └── *.py           # Service implementations
├── tasks/              # Zeebe worker task handlers
├── tests/              # Unit tests
├── utils/              # Utility functions
├── main.py             # Application entry point
├── Dockerfile          # Container definition
└── requirements.txt    # Python dependencies
```

### Adding New Tasks

To add a new Zeebe task:

1. Implement the task function in `tasks/worker_tasks.py`
2. Register the task in the `_register_tasks` method with appropriate decorators
3. Update your BPMN workflow to include the new task type
4. Add any required service dependencies to the constructor

Example:
```python
def _register_tasks(self):
    self.worker.task(task_type="my_new_task",
                     exception_handler=on_error)(self.my_new_task_handler)

def my_new_task_handler(self, param1: str, param2: dict) -> dict:
    log_task_start("my_new_task")
    # Implementation here
    log_task_completion("my_new_task")
    return {"result": "success"}
```

### Service Development

Services are organized in the `services/` directory with clear separation of concerns:

- **Database Service** (`database.py`) - HOC/TOC data persistence
- **Sensor Data Service** (`sensor_data_service.py`) - Transport sensor integration
- **Product Footprint Service** (`product_footprint.py`) - PCF template management
- **Proving Service** (`proving_service.py`) - Kafka-based proof messaging
- **Verifier Service** (`verifier_service.py`) - gRPC receipt verification
- **Logistics Operation Service** (`logistics_operation_service.py`) - Transport/hub operations
- **PCF Registry Service** (`pcf_registry_service.py`) - Proof registry integration

### Testing

Run the tests using:

```bash
python -m unittest discover tests
```

Current test coverage includes:
- Product footprint service validation
- Kafka messaging functionality
- Service verification workflows

### Docker and Kubernetes

The service is containerized and ready for Kubernetes deployment:

- **Dockerfile**: Multi-stage build with Python 3.12-slim base
- **Kubernetes Manifest**: Includes init containers for Zeebe dependency checks
- **Environment Configuration**: Supports environment-based configuration for different deployment targets

### Dependencies

Key dependencies include:
- **pyzeebe**: Zeebe client and worker framework
- **confluent-kafka**: Kafka messaging integration
- **grpcio**: gRPC communication for external services
- **pydantic**: Data validation and serialization
- **cryptography**: Security and encryption support
