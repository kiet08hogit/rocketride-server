# Authoritative Overlay Node

Part of the **Audit-grade financial extraction node suite**.

## Overview
The `authoritative_overlay` node is a pipeline filter designed to cross-check extracted financial numbers against official regulator data. 

Currently supported regulators include:
- US SEC (EDGAR)
- EU/UK IFRS
- UK Companies House
- Japan EDINET

## Behavior
- **Input**: Pipeline `answers` (extracted financial data/numbers).
- **Process**: The node queries the configured regulator database for the official recorded value.
- **Output**: 
  - If the extracted number matches the official data, the answer is forwarded downstream.
  - If there is a mismatch or no record is found, the node **abstains** by dropping the answer and logging a warning.

## Configuration
See `services.json` for node configuration schemas.

<!-- ROCKETRIDE:GENERATED:PARAMS START -->
<!-- ROCKETRIDE:GENERATED:PARAMS END -->
