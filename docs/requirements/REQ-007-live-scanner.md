# REQ-007 — Live Data & Strategy Scanner

Status: QA
Priority: P1
Classification: CRITICAL
Target: 0.7.0-dev
Base: main / v0.6.0 / a7a304981b50c6d30261d3460f6e547383e09e8d
Branch: codex/req-007-live-scanner
Human Acceptance: PENDING

## Mandatory real IQ acceptance — supersedes optional-provider scope below

Human review now requires real IQ Option PRACTICE authentication, REGULAR/OTC discovery, historical and realtime candles, verified closed/forming separation, product-specific payout where available, and a real OTC candle evaluated by Scanner. No DONE/merge/tag until sanitized local IQ smoke PASS and automated CI PASS. IQ is not deferred to REQ-008. Investigate/pin victalejo/iqoptionapi commit acac6e08333466ae188c7dfa7fd2a03174e34ca2; isolate the read-only async transport, guard PRACTICE, redact all auth data, retain frozen engines and the already-corrected paper config. Real credentials and open OTC market are external acceptance prerequisites; no fake PASS. Return to QA only after real-provider evidence succeeds.

## Final human QA correction — research configuration precedence

### Mandatory IQ implementation evidence (2026-09-19)

Local verification: backend179 PASS/13 PostgreSQL-dependent skips; frontend47 PASS; E2E6 PASS; lint/typecheck/build PASS. Seven new IQ tests cover fake WebSocket authentication/streaming, readonly wire/static guard, exact normalization/product payout, pagination, canonical origin and unavailable/stale clock. Existing frozen quant/research precedence regressions PASS. PostgreSQL/Docker final verification runs in CI; see PR handoff for exact final commit/run.

Real IQ smoke: **PASS**, completed21:49:03.407515Z, exit0. ProviderIQOPTION, PRACTICE profile/balance verified; productbinary; REGULAR98/OTC171 discovered (2/168 open). BTCUSD-OP REGULAR and EURUSD-OTC each20 closed1m candles, real forming and new closed updates PASS. Real EURUSD-OTC close21:49Z evaluated LIVE → MATCH using frozen base features/ema_3/DSL; payout85%, sourcePROVIDER; research expiry sourceRESEARCH_ASSUMPTION. Orders sent0, ledger writes0. [Full sanitized report](../providers/IQOPTION_SMOKE_2026-09-19.md), [setup/pin/semantics](../providers/IQOPTION_EXPERIMENTAL.md).

Pinned upstream SHA acac6e08333466ae188c7dfa7fd2a03174e34ca2. Private async read-only wire allowlist, PRACTICE/no REAL fallback, secret redaction even at DEBUG, Decimal parsing, product-specific metadata, verified dynamic capabilities, pagination/clock checks, optional installation. Backend Docker build now excludes local credentials. Original research precedence tests remain intact. Local final verification and exact final CI SHA/run are recorded in the PR handoff; only the final HEAD green checks are merge evidence. Human Acceptance remains PENDING; no merge/tag/REQ-008.

Human review requested an explicit pure paper-config resolver: normal mode uses validation expiry and provider payout with validation fallback; research mode uses research expiry and provider payout with research fallback. Historical validation remains reference metadata, never hidden research execution configuration. Add payout/expiry source evidence and truthful UI labels; regress all four cases and actual paper outcomes. Status remains QA; no merge, tag, engine version change or REQ-008. Corrected-head CI evidence will be recorded in PR #6 and the handoff report.

Implemented `resolve_paper_config`, immutable event `payout_source`/`expiry_source`, historical/reference and research input metadata; PaperObservation consumes the exact resolved config without modifying next-open/consecutive-expiry/binary semantics. Four pure precedence tests, two no-cross-mode-fallback tests and four real validated Replay integrations verify actual expiry and Decimal P&L. Two UI regressions verify research90%/3 bars versus historical84%/1 bar, with and without provider87%. Local: Backend172 PASS/13 PostgreSQL-dependent skips; Frontend46 PASS; E2E6 PASS; lint/typecheck/build PASS. Automated A–J remain green. This earlier correction is retained; the subsequent mandatory IQ integration below changes providers, not frozen engines.

## Scope

cq-live-data-v1 and cq-scanner-v1: read-only provider contract, Replay/Mock, isolated optional MT5 and mandatory real PRACTICE-only IQ Option; exact incremental frozen features/DSL, dataset-compatible validation, private watchlists/events, immutable live provenance and paper observations, dedicated worker, APIs/live UI, migration006, tests/E2E/benchmark/CI/PR. No order sending, money/session/ledger mutation, silent feed substitution, retroactive LIVE matches, checkpoint implementation or REQ-008.

## Plan / acceptance gates

Provider abstraction/Replay → incremental feature equivalence (10000 candles) → scanner/validation policy → persistence/paper outcomes → APIs/UI → optional adapter isolation → tests/PostgreSQL/E2E → benchmark/docs → PR/CI → QA. No merge or tag before independent human acceptance.

A exact feature equivalence; B exact signal timestamps; C forming excluded; D stale/disconnect suppress; E identity/OTC isolation; F validation dataset compatibility; G payout warning; H degraded suspension; I immutable/idempotent events; J frozen binary paper equivalence. Real IQ PRACTICE/OTC smoke is mandatory separate local evidence; CI uses Replay and fake IQ WebSocket fixtures without secrets. MT5 smoke remains optional.

## Implementation and evidence

- Engines: cq-live-data-v1 / cq-scanner-v1. Existing four quant engines unchanged mathematically.
- Providers: deterministic Replay and Mock; optional terminal-local MT5 with server identity/origin verification, closed/forming separation and no payout/server-clock claim. IQ Option uses a pinned async read-only transport with verified real PRACTICE/REGULAR/OTC data. Defaults disabled; unofficial protocol warning remains. No fallback, secrets or order capability.
- Pipeline: single PostgreSQL-locked dedicated worker, shared provider/dataset subscriptions, canonical bootstrap once, persistent frozen generator and trailing51 feature rows. Bounded reconnect and independent heartbeat; one evaluation per new closed candle, historical bootstrap not emitted as LIVE.
- Scanner: owned immutable version, exact five-axis dataset compatibility and TESTING required for normal mode. Real historical PASS followed by later FAIL suspends new events. Lower live payout warns; history remains unchanged.
- Paper: actual consecutive next-open/expiry candles only; fixed assumption clearly distinguished from provider payout; gap/interruption unavailable; no account/session/ledger/Trade writes.
- Database: migration006 six tables, JSONB target, immutable event/outcome/provenance application guards, unique event/observation identities, constraints, reversible migration with destructive-downgrade warning.
- Frontend: `/scanner`, providers/capabilities, watchlist and full dataset/version selection, research filter, neutral MATCH, health/context/snapshot, payout warning, REPLAY/paper history, SSE plus polling fallback. Existing paging buttons fixed to avoid submitting containing forms.
- Local verification: Backend162 PASS/13 PostgreSQL-dependent skips, frontend44 PASS, lint/typecheck/build PASS and all6 E2E PASS. CI baseline171 backend PASS/4 intentional SQLite concurrency skips; migration006 PostgreSQL and Docker PASS. These are earlier baseline counts. MT5 smoke NOT RUN; mandatory IQ smoke now PASS (dated report below).
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

No known P0/P1 found in automated checks; independent human QA required. P2 [LIVE-001](../debt/LIVE-001-provider-operations.md), existing SEC-001 and quant/recovery debts, dependency warnings and bundle-size warning. Real IQ OTC is implemented and smoke-verified in REQ-007; no REQ-008 implementation. Human acceptance remains PENDING; no merge/tag.

## CI and handoff

[PR #6](https://github.com/jsmontenegro17/ciberquant/pull/6), base main. Initial implementation d2034510ac2a75b0e590da06ffb26cadff9bccb6: push CI [35468326588](https://github.com/jsmontenegro17/ciberquant/actions/runs/35468326588) and PR CI [35468338708](https://github.com/jsmontenegro17/ciberquant/actions/runs/35468338708), all three jobs PASS. Final follow-up adds Docker dedicated-worker startup verification, explicit receive-latency display and frontend configuration/compatibility/forming/history regression (44 frontend tests). Its exact final HEAD/CI run IDs are recorded in the PR handoff and final report after green checks; do not merge on the earlier run alone.

Automated acceptance A–J: PASS. Status QA; Human Acceptance PENDING. Stop after final CI; no REQ-008.
