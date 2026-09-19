# REQ-007 — Live Data & Strategy Scanner

Status: QA
Priority: P1
Classification: CRITICAL
Target: 0.7.0-dev
Base: main / v0.6.0 / a7a304981b50c6d30261d3460f6e547383e09e8d
Branch: codex/req-007-live-scanner
Human Acceptance: PENDING

## Scope

cq-live-data-v1 and cq-scanner-v1: read-only provider contract, Replay/Mock, isolated optional MT5 and experimental disabled IQ Option; exact incremental frozen features/DSL, dataset-compatible validation, private watchlists/events, immutable live provenance and paper observations, dedicated worker, APIs/live UI, migration006, tests/E2E/benchmark/CI/PR. No order sending, money/session/ledger mutation, silent feed substitution, retroactive LIVE matches, checkpoint implementation or REQ-008.

## Plan / acceptance gates

Provider abstraction/Replay → incremental feature equivalence (10000 candles) → scanner/validation policy → persistence/paper outcomes → APIs/UI → optional adapter isolation → tests/PostgreSQL/E2E → benchmark/docs → PR/CI → QA. No merge or tag before independent human acceptance.

A exact feature equivalence; B exact signal timestamps; C forming excluded; D stale/disconnect suppress; E identity/OTC isolation; F validation dataset compatibility; G payout warning; H degraded suspension; I immutable/idempotent events; J frozen binary paper equivalence. Real broker smoke is separate optional evidence; CI uses Replay only.

## Implementation and evidence

- Engines: cq-live-data-v1 / cq-scanner-v1. Existing four quant engines unchanged mathematically.
- Providers: deterministic Replay and Mock; optional terminal-local MT5 with server identity/origin verification, closed/forming separation and no payout/server-clock claim. IQ Option intentionally EXPERIMENTAL / DISABLED / UNAVAILABLE. No fallback, secrets or order capability.
- Pipeline: single PostgreSQL-locked dedicated worker, shared provider/dataset subscriptions, canonical bootstrap once, persistent frozen generator and trailing51 feature rows. Bounded reconnect and independent heartbeat; one evaluation per new closed candle, historical bootstrap not emitted as LIVE.
- Scanner: owned immutable version, exact five-axis dataset compatibility and TESTING required for normal mode. Real historical PASS followed by later FAIL suspends new events. Lower live payout warns; history remains unchanged.
- Paper: actual consecutive next-open/expiry candles only; fixed assumption clearly distinguished from provider payout; gap/interruption unavailable; no account/session/ledger/Trade writes.
- Database: migration006 six tables, JSONB target, immutable event/outcome/provenance application guards, unique event/observation identities, constraints, reversible migration with destructive-downgrade warning.
- Frontend: `/scanner`, providers/capabilities, watchlist and full dataset/version selection, research filter, neutral MATCH, health/context/snapshot, payout warning, REPLAY/paper history, SSE plus polling fallback. Existing paging buttons fixed to avoid submitting containing forms.
- Local verification: Backend162 PASS/13 PostgreSQL-dependent skips, frontend44 PASS, lint/typecheck/build PASS and all6 E2E PASS. CI baseline171 backend PASS/4 intentional SQLite concurrency skips; migration006 PostgreSQL and Docker PASS. Real MT5/IQ smoke NOT RUN (not an automated gate).
- Benchmark 2026-09-19 Windows/Python3.12.14: 3 datasets ×10000 candles ×4 strategies,120000 evaluations/110190 matches in1.505s;79759.3 in-memory event decisions/sec and evaluations/sec; mean feature update33.70μs. Excludes SQL/network/JSON and is not an SLA.

## Acceptance matrix (automated)

| Gate | Evidence |
|---|---|
| A | `test_10000_live_features_exactly_equal_frozen_batch` |
| B/J | `test_replay_signals_and_paper_equal_frozen_backtest` |
| C/D | `test_forming_duplicate_stale_disconnect_and_conflict` |
| E/F/G/H | `test_real_validation_payout_dataset_isolation_and_degraded_suspension` |
| I | event/provenance immutability, duplicate polling, `test_shared_subscription_bounded_reconnect_no_duplicate_events`, migration006 |
| UI | scanner component tests and real worker-backed Replay E2E NO_MATCH→MATCH→WIN |

## Risks / boundaries

No known P0/P1 found in automated checks; independent human QA required. P2 [LIVE-001](../debt/LIVE-001-provider-operations.md), existing SEC-001 and quant/recovery debts, dependency warnings and bundle-size warning. Actual IQ OTC is a conditional v1.0 blocker if product acceptance requires it; separate authorization required, no REQ-008 implementation. Human acceptance remains PENDING; no merge/tag.

## CI and handoff

[PR #6](https://github.com/jsmontenegro17/ciberquant/pull/6), base main. Initial implementation d2034510ac2a75b0e590da06ffb26cadff9bccb6: push CI [35468326588](https://github.com/jsmontenegro17/ciberquant/actions/runs/35468326588) and PR CI [35468338708](https://github.com/jsmontenegro17/ciberquant/actions/runs/35468338708), all three jobs PASS. Final follow-up adds Docker dedicated-worker startup verification, explicit receive-latency display and frontend configuration/compatibility/forming/history regression (44 frontend tests). Its exact final HEAD/CI run IDs are recorded in the PR handoff and final report after green checks; do not merge on the earlier run alone.

Automated acceptance A–J: PASS. Status QA; Human Acceptance PENDING. Stop after final CI; no REQ-008.
