# Vertex AI Vector Search Node

A tool node for interacting with Google Cloud Vertex AI Vector Search (formerly Matching Engine).

This node exposes a `search` tool only. It is not a full vector store adapter (no add/upsert via `DocumentStoreBase`).

## Authentication
This node uses the shared RocketRide Google Cloud authentication logic. You can authenticate by either:
1. Uploading a **Service Account JSON Key**.
2. Leaving the key blank and relying on **Application Default Credentials (ADC)** if your RocketRide server is hosted on Google Cloud Run, GKE, or a Compute Engine VM with attached service accounts.

## Usage
When placed in a pipeline as a tool node, it provides the `search` tool for finding K-nearest neighbors to a given embedding vector, honoring `top_k` and `score_threshold`.

`score_threshold` assumes **similarity** semantics (higher is better), such as `DOT_PRODUCT_DISTANCE`. It is **not** correct for `SQUARED_L2_DISTANCE` (where lower distance is better).

<!-- ROCKETRIDE:GENERATED:PARAMS START -->
<!-- ROCKETRIDE:GENERATED:PARAMS END -->
