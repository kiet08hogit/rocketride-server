# Authoritative Overlay Node

Part of the **Audit-grade financial extraction node suite**.

## Overview
The `authoritative_overlay` node is a pipeline filter designed to cross-check extracted financial numbers against official regulator data. 

Currently supported regulators include:
- US SEC (EDGAR)

## Behavior

- **Input**: Pipeline `answers` (extracted financial data/numbers).
- **Process**: The node queries the live SEC EDGAR API dynamically using the configured company CIK for the official recorded value.
- **Output**: 
  - If the extracted number matches the official data, the answer is forwarded downstream.
  - If there is a mismatch or no record is found, the node **abstains** by dropping the answer and logging a warning.

> [!NOTE]
> **Strict Matching**: The node uses exact matching (`math.isclose` with a high strictness tolerance `rel_tol=1e-9`). This ensures that only exact financial figures are passed through. Filings restated to the nearest thousand will not match a value extracted to the unit.

## Configuration

See `services.json` for node configuration schemas.

<!-- ROCKETRIDE:GENERATED:PARAMS START -->
<!-- ROCKETRIDE:GENERATED:PARAMS END -->
