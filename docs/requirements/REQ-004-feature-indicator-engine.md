# REQ-004 — Feature & Indicator Engine

Status: QA
Priority: P1
Classification: LARGE
Created: 2026-09-19
Target version: 0.4.0-dev
Base: main / v0.3.0
Branch: codex/req-004-feature-indicator-engine

## Scope and acceptance

Versioned pure Decimal feature engine, candle morphology/continuity/returns, SMA, SMA-seeded EMA, Wilder RSI/ATR, population Bollinger, central typed registry and STANDARD convenience preset. Read-only authenticated definitions/compute APIs with canonical dataset-origin anchoring and immutable ID snapshots. Feature Lab with real candlesticks, overlays, RSI/ATR panes, UTC tooltip, null warmup, bounded table, metadata and gap markers.

Required evidence: explicit deterministic formula/warmup/edge fixtures; prefix/future-mutation invariance; query-range independence; backfill snapshot replay; all dataset dimensions isolated; invalid specs/caps rejected; frontend and disposable E2E regressions preserving REQ-002/003; 100k STANDARD benchmark; PostgreSQL/backend, frontend/E2E and Docker CI green; documentation and open PR before QA.

No strategies, binary outcomes, backtesting, regime classification, support/resistance or additional indicators. No raw-data changes, indicator persistence, caches or empty migration. REQ-005 needs separate authorization after human acceptance; no automatic merge.

## Frozen mathematical contract

See [INDICATOR_DEFINITIONS](../INDICATOR_DEFINITIONS.md). FEATURE_ENGINE_VERSION=cq-features-v1. Decimal local context precision50/ROUND_HALF_EVEN; serialize numeric features as strings rounded only at the boundary to18 fractional places. Dataset open-time ordering, strict single identity, no lookahead. Indicator state continues across gaps. Gap seconds means actual open-time interval minus expected timeframe duration (signed for irregular intervals); first row false/0/run1. Return compares previous available close even across gaps.

## Snapshot/API design

Capture dataset MAX(candle.id), or validate caller ceiling within current maximum. Every dataset query applies id<=ceiling. Anchor is first open_time in that snapshot; compute all candles from origin with open_time<end, emit only start<=open_time<end. Empty snapshot uses ID0/anchor null. Exact caps reject rather than silently truncate. No persistence/schema migration.

## Roadmap

REQ-004 Feature & Indicator Engine → REQ-005 Strategy Lab & Binary Backtesting Engine → REQ-006 Validation & Walk-Forward Engine → REQ-007 Live Data & Scanner → REQ-008 Integrated Research Workspace / v1.0. Roadmap is not authorization for subsequent requirements.

## Validation and risks

Human Acceptance: PENDING. Local2026-09-19:87 backend PASS/4 skips (PostgreSQL-only opt-in and SQLite concurrency case),22 frontend PASS,3 E2E PASS. Lint/typecheck/build PASS. Snapshots are exercised through the existing migrated-database harness, including PostgreSQL in CI. Desktop/tablet screenshots inspected; E2E checks known EMA20/RSI14 values and no page errors.

100k STANDARD benchmark:2.996seconds, Windows11 build26200, Intel64 Family6 Model151 Stepping2,20 logical CPUs, Python3.12.14. Single process; Decimal50; generation included, SQL/serialization excluded. Not an SLA. Reproduce: `cd backend; python scripts/benchmark_features.py`.

P0/P1: none identified in automated/local visual validation. P2: synchronous CPU-bound origin calculation, future cache/checkpoints; frontend bundle warning(~520kB minified); existing DATA-001, SEC-001 and dependency deprecations. No recovery/security-debt implementation mixed into this requirement. Rollback: revert feature changes; no database rollback necessary.

## Acceptance evidence

| Scenario | Evidence | Local result |
|---|---|---|
| A EMA20 | test_ema20_exact_fixture + USER E2E seed10.5/final90.5 | PASS |
| B RSI/ATR/Bollinger | explicit manual Wilder and population-ddof0 fixtures | PASS |
| C range independence | API starts50/80, all common rows exactly equal | PASS |
| D snapshot/backfill | replay same ceiling after earlier backfill/future append, SQLite and CI PostgreSQL | PASS |
| E no-lookahead | prefix100/200 and mutated future prices | PASS |
| F gaps | signed missing seconds/run reset, warmed indicator state unchanged | PASS |
| G Feature Lab | USER fixture, real candle/overlay/RSI/ATR canvas, exact values, metadata/nulls, screenshots | PASS |

## Remote CI and handoff

[PR #3 — REQ-004 Feature & Indicator Engine](https://github.com/jsmontenegro17/ciberquant/pull/3), OPEN; base main, head codex/req-004-feature-indicator-engine. Human Acceptance remains PENDING, not inferred from CI.

Implementation SHA: `f31dc989914c2b91e410a2b9a2cfc34330df30e7`.
CI push [35459261157](https://github.com/jsmontenegro17/ciberquant/actions/runs/35459261157) and PR [35459280520](https://github.com/jsmontenegro17/ciberquant/actions/runs/35459280520): Backend PASS, Frontend/E2E PASS, Docker PASS on2026-09-19. Backend90 PASS/1 intentional SQLite concurrency skip; PostgreSQL snapshot replay executed. Frontend22 PASS, E2E3 PASS. Existing migrations001–003 and seed pass; no migration004.

This documentation-only QA handoff commit must also pass CI; its exact final-head SHA/run links are recorded in PR #3 and the delivery report to avoid a self-referential commit. No merge, tag or REQ-005 work authorized by this handoff.
