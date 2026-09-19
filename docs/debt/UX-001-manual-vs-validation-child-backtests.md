# UX-001 — Distinguish manual vs validation child backtests

Status: RESOLVED
REQ-008 implementation update (Human Acceptance PENDING): Strategy list filters MANUAL with bounded batched lookups; Workspace separately exposes latest historical validation and child lineage. API/E2E regressions distinguish manual IDs from validation child IDs. No calculation change.

## Historical problem and original scope


Original status: OPEN
Priority: P2
Origin: REQ-006 Human Acceptance, 2026-09-19
Blocking v0.6.0: NO

## Problem

The Strategy list last_backtest may select an internal child run with purpose=VALIDATION. GET /backtests correctly defaults to MANUAL only, and validation child evidence remains accessible through the owned Validation workspace. This presentation distinction does not affect calculations, ownership or historical evidence.

## Future scope

Show Last manual backtest and Latest validation separately, or filter Strategy.last_backtest to MANUAL. Preserve explicit access to validation child evidence and add UI/API regressions for both kinds. No implementation or functional change is included in the REQ-006 release closure; requires separately authorized work.
