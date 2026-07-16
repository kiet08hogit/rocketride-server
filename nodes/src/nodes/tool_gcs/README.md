# Google Cloud Storage (GCS) Node

A tool node for interacting with Google Cloud Storage buckets.

## Authentication
This node uses the shared RocketRide Google Cloud authentication logic. You can authenticate by either:
1. Uploading a **Service Account JSON Key**.
2. Leaving the key blank and relying on **Application Default Credentials (ADC)** if your RocketRide server is hosted on Google Cloud Run, GKE, or a Compute Engine VM with attached service accounts.

## Usage
When placed in a pipeline as a tool node, the LLM can:
- **`list_files`**: List objects in the configured bucket (with optional prefix filtering).
- **`download_file`**: Download an object from the bucket to a temporary local file on the server.

<!-- ROCKETRIDE:GENERATED:PARAMS START -->
<!-- ROCKETRIDE:GENERATED:PARAMS END -->
