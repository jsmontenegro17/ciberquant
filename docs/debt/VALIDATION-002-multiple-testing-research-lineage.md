# VALIDATION-002 — Multiple Testing / Research Lineage

Status: OPEN
Priority: P2
Origin: REQ-006
Blocking v0.6.0: NO

REQ-006 records prior attempts, revealed overlapping holdouts and exact config replays for the same immutable StrategyVersion and full dataset identity. Warnings are refreshed at reveal; REUSED HOLDOUT and REPLAY never imply independent new evidence. This does not detect related/new strategy versions, other datasets with shared raw history, other users or external exploration. No perfect blindness or multiple-testing correction is claimed.

Future scope: explicit research lineage, dataset overlap provenance and statistically reviewed repeated-testing protocols. Do not add automatic optimization/rankings or silently alter cq-validation-v1 thresholds. Changes need an independently authorized requirement and, when incompatible, a new protocol version.
