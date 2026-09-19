# QUANT-001 — Feature Checkpoint / Recursive Indicator Acceleration

Status: OPEN
Priority: P2
Origin: REQ-004 Human Acceptance, 2026-09-19
Blocking v0.4.0: NO

## Problem

Recursive indicators are calculated exactly from the canonical dataset origin. FEATURE_ENGINE_MAX_SOURCE_CANDLES bounds work; requests beyond that limit are rejected rather than approximated. This is the correct cq-features-v1 contract.

## Future scope

Investigate versioned checkpoints preserving engine version, as-of snapshot semantics, full indicator state, feature specifications and all dataset identity dimensions. Prove exact equality with origin calculations, query-range independence and replay stability after backfill. Define checkpoint invalidation and retained-raw-data requirements explicitly.

Never accelerate EMA/RSI/ATR by simply truncating their warmup. Incompatible semantics require a new engine version. No checkpoints, caches or other acceleration are implemented in REQ-004; a separate authorized requirement is needed.
