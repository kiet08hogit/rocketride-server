# Firestore Node

A standard node for interacting with Google Cloud Firestore (Native mode).

## Authentication
This node uses the shared RocketRide Google Cloud authentication logic. You can authenticate by either:
1. Uploading a **Service Account JSON Key**.
2. Leaving the key blank and relying on **Application Default Credentials (ADC)** if your RocketRide server is hosted on Google Cloud Run, GKE, or a Compute Engine VM with attached service accounts.

## Usage
When placed in a pipeline as a tool node, the LLM can:
- **`get_document`**: Fetch an existing document by its collection and document ID.
- **`set_document`**: Create or update (merge) a document with JSON data.

<!-- ROCKETRIDE:GENERATED:PARAMS START -->
<!-- ROCKETRIDE:GENERATED:PARAMS END -->
