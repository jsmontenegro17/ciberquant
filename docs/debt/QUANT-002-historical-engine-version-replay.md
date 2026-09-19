# QUANT-002 — Historical Engine Version Replay

Status: OPEN
Priority: P2
Origin: REQ-005 Human Acceptance, 2026-09-19
Blocking v0.5.0: NO

## Problem

Current strategies and runs use cq-features-v1, cq-strategy-dsl-v1 and cq-binary-backtest-v1. When an incompatible v2 is introduced, the runtime must still reproduce historical v1 evidence using its recorded versions, immutable configuration and retained raw-data snapshot. Version labels alone do not provide multi-version runtime dispatch.

## Future scope

Design an explicit engine version registry / dispatcher, for example feature_engines["cq-features-v1"], strategy_evaluators["cq-strategy-dsl-v1"] and backtest_engines["cq-binary-backtest-v1"]. Preserve compatible historical implementations and deterministic fixtures; reject unsupported versions explicitly instead of silently substituting the latest engine.

Before introducing incompatible engines, prove historical v1 replay remains identical with v1 and v2 installed together, including definition/config hashes, signals, trade evidence and exact metrics. Define retention, compatibility and unsupported-version policies.

The three v1 contracts are frozen for v0.5.0. Never modify v1 silently to adopt future formulas or semantics. No registry, dispatcher or historical replay migration is implemented in REQ-005; a separate authorized requirement is required.
