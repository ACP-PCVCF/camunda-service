# Business Process Service (Camunda Service) for TRACE

This repository contains the Business Process Service, a core component of the **TRACE (Trusted Real-time Assessment of Chained Emissions)** system. This Python-based microservice is responsible for orchestrating workflow processes for transport carbon tracking using the Camunda 8 Zeebe engine.

## TRACE System Overview

TRACE is a decentralized system for verifiable Product Carbon Footprint (PCF) tracking in logistics and supply chains. It leverages zero-knowledge proofs and cryptographic verification to ensure data integrity and privacy while enabling efficient aggregation of emission data. The system is built on established industry standards, including the **iLEAP** and **GLEC** frameworks.

For more information about the TRACE system, please see the main [TRACE repository](https://github.com/ACP-PCVCF/TRACE).

## Role in the TRACE Architecture

The Business Process Service acts as the central orchestrator in the TRACE architecture. It manages BPMN workflows, coordinates tasks, and integrates with all other system components, including:

-   **[Proving Service](https://github.com/ACP-PCVCF/proving-service)**: Generates and verifies zero-knowledge proofs for carbon footprint calculations.
-   **[Verifier Service](https://github.com/ACP-PCVCF/verifier)**: Independently verifies ZK proofs and digital signatures.
-   **[Sensor Data Service](https://github.com/ACP-PCVCF/sensor-data-service)**: Simulates and provides signed sensor data.
-   **[Sensor Key Registry](https://github.com/ACP-PCVCF/sensor-key-registry)**: Manages and validates RSA public keys for sensor authentication.
-   **[PCF Registry](https://github.com/ACP-PCVCF/pcf-registry)**: Stores and manages PCF proofs.

## Key Features

-   **Workflow Orchestration**: Manages Zeebe workflow tasks for comprehensive transport carbon emission tracking.
-   **Data Integration**: Collects and processes sensor data from transport operations.
-   **Product Footprint Management**: Creates and manages Product Carbon Footprint (PCF) templates.
-   **Proof Generation**: Integrates with proofing service via Kafka messaging to generate carbon footprint proofs.
-   **Receipt Verification**: Verifies proof receipts through gRPC-based service.
-   **Registry Integration**: Interfaces with a PCF registry for proof storage and retrieval.
-   **Logistics Operations**: Manages hub and transport procedures, including TCE data tracking.

## Getting Started

### Prerequisites

-   Python 3.12+ (Docker image uses `python:3.12-slim`)
-   Zeebe Server (Camunda 8 Platform)
-   Dependencies as listed in `requirements.txt`

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ACP-PCVCF/camunda-service.git
    cd camunda-service
    ```
2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **To start the service, run the following command**:
    ```bash
    python main.py
    ```

The service will connect to the configured Zeebe gateway, initialize all dependencies, register task handlers, and begin processing workflow tasks.

## Development

### Project Structure

```
├── config/              # Configuration
├── data/               # BPMN files, example data, and scripts
├── k8s/                # Kubernetes deployment manifests
├── helm-chart/         # Helm chart files
├── logs/               # Application logs
├── models/             # Pydantic data models
├── services/           # Business logic services
│   ├── pb/            # gRPC protocol buffer files
│   └── *.py           # Service implementations
├── tasks/              # Zeebe worker task handlers
├── tests/              # Unit tests
├── utils/              # Utility functions
├── main.py             # Application entry point
└── requirements.txt    # Python dependencies
```

### Testing

The project includes a suite of unit tests. To run all tests, use the provided test runner:

```bash
python tests/run_tests.py
```

### CI/CD Integration

Tests are automatically executed as part of the CI/CD pipeline in GitHub Actions. The workflow is configured to:

1.  Run all tests on every push to the `main` branch.
2.  Build and push the Docker image only if all tests pass.
3.  Push the Docker image to the GitHub Container Registry (ghcr.io).
4.  Generate an artifact attestation for the Docker image.

For the complete workflow configuration, see `.github/workflows/push-to-registry.yml`.

## Example Data

The `data/` directory provides sample data.

### Proof Document Examples (`data/proof_documents_examples/`)

Example JSON files in this directory illustrate proof document schemas for various supply chain entities. These files are primarily intended for internal documentation purposes, with the option for companies to publish them publicly (complete or partial) to support transparency initiatives.

-   `Amazing Company 1.json`
-   `Amazing Company 2.json`
-   `Amazing Company 3.json`

### Proof Verification Example (`data/proof_verify_example/`)

This folder contains a proof receipt generated by the Proving Service. This receipt is designed to be stored in the PCF Registry and passed to the next participant in the supply chain.

-   `receipt_output.json`

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

This project was developed as part of an academic research initiative and is open source software that can be freely used, modified, and distributed.

---