# REQ-005 — Strategy Lab & Binary Backtesting Engine

Status: DONE
Priority: P1
Classification: CRITICAL
Target: 0.5.0
Base: main / v0.4.0 / 6a3a5bdf9beb69241807f48660f11117fdc55034
Branch: codex/req-005-strategy-backtesting
Human Acceptance: PASS
Acceptance date: 2026-09-19
Approved HEAD: 40981e0f25c1cda0d987c23eba0922f35d90db99

## Scope

Immutable private strategy versions and canonical hashes; cq-strategy-dsl-v1 typed bounded AST; cq-binary-backtest-v1 causal next-open binary execution; frozen cq-features-v1 reused unchanged. Origin/as-of snapshot replay, Decimal unit metrics, persisted atomic run/trade evidence, migration004, owned APIs, Strategy Lab and backtest inspector. Results are IN-SAMPLE / NOT VALIDATED under a fixed payout assumption, not financial recommendations.

## Plan / evidence gates

Freeze DSL and execution semantics → models/migration → pure evaluator/outcome/event engine → transactional repositories/APIs → frontend → deterministic regression/ownership/PostgreSQL/migration tests → E2E preserving REQ-002/003/004 →100k benchmark → docs → PR/CI → QA. No merge without Human Acceptance. No REQ-006, auto-trading, money management, martingale, feature-math changes, statistical validation or strategy rankings.

Acceptance A–H: exact execution; bearish candle != PUT win;83.5%→0.835; no execution across gaps; bars_ago/warmup/availability; backfill replay; overlap policies; real UI→backtest→inspector. Automated/agent QA PASS; Human Acceptance PASS.

## Implemented contracts

Versions: cq-features-v1 (source unchanged from v0.4.0), cq-strategy-dsl-v1, cq-binary-backtest-v1. [STRATEGY_DSL](../STRATEGY_DSL.md) and [BINARY_BACKTEST_SEMANTICS](../BINARY_BACKTEST_SEMANTICS.md) freeze the mathematical/temporal contracts. Migration004 adds derived strategy/run/trade tables only, with JSONB, ownership, unique version/sequence and causal-time constraints. Downgrade deletes derived evidence; export/backup first. No raw or financial table/schema change.

## Local validation — 2026-09-19

- Backend126 PASS/7 skips: PostgreSQL opt-in plus nonapplicable SQLite concurrency cases. Remote PostgreSQL/Docker PASS; evidence below.
- Frontend27 PASS; lint/typecheck/build PASS; all4 E2E PASS, preserving REQ-002/003/004.
- Manual browser fixture: RSI2/BB2 rule,3 trades DRAW/LOSS/WIN, unit P&L0/-1/+0.835,total-0.165, unavailable2. Desktop/tablet screenshots reviewed; no page errors or horizontal viewport overflow.
-100k STANDARD benchmark: features3.696s, signal0.391s, execution2.375s,total6.738s;94,243 trades; Windows11 build26200, Intel64 Family6 Model151 Stepping2,20 logical CPUs, Python3.12.14. Pure engine cap100000 explicitly for benchmark; no SQL/JSON; no SLA.

## Acceptance evidence

| Scenario | Evidence | Local result |
|---|---|---|
| A exact entry/expiry | next open105 vs signal close100; expiry1/2 and availability | PASS |
| B bearish != PUT WIN | entry100/expiry bearish102→101 yields LOSS | PASS |
| C payout |83.5→0.835 exact; unit metrics manually verified | PASS |
| D gaps | entry/expiry gaps skip without fabricated trade | PASS |
| E causal DSL | bars_ago/CCC/warmup/tri-state/future mutation tests | PASS |
| F replay | backfill same ceiling and same config/definition hash, version history retained | PASS including PostgreSQL |
| G overlap | expiry5, ALLOW15 vs SKIP3, deterministic settlement-before-signal | PASS |
| H UI | real USER→DRAFT→version→backtest→trade context E2E | PASS |

P0/P1: none within the human-accepted scope. P2: BACKTEST-001 stale run recovery, BACKTEST-002 execution realism, QUANT-001 checkpoints, [QUANT-002 historical engine version replay](../debt/QUANT-002-historical-engine-version-replay.md), DATA-001, SEC-001, dependency warnings and frontend bundle warning(~539kB minified). None blocks v0.5.0. UI intentionally supports flat groups, nested AST supported through API. No statistical validation claim; REQ-006 is not authorized.

## Remote CI / handoff

[PR #4 — REQ-005 Strategy Lab & Binary Backtesting Engine](https://github.com/jsmontenegro17/ciberquant/pull/4): integration into main authorized after final green CI, head codex/req-005-strategy-backtesting.

Implementation SHA: `b7612005681903010547d56082a7ee9386e09359`.
CI PR [35461839133](https://github.com/jsmontenegro17/ciberquant/actions/runs/35461839133) and push [35461837203](https://github.com/jsmontenegro17/ciberquant/actions/runs/35461837203): Backend PASS, Frontend/E2E PASS, Docker PASS on2026-09-19. Backend131 PASS/2 intentional SQLite-only concurrency skips; PostgreSQL migration004, version locking/uniqueness, ownership, JSONB, causality, persistence and replay executed. Frontend27 PASS; E2E4 PASS. Existing migrations and idempotent seed PASS.

Approved-head CI PR [35462021513](https://github.com/jsmontenegro17/ciberquant/actions/runs/35462021513) and push [35462018759](https://github.com/jsmontenegro17/ciberquant/actions/runs/35462018759): Backend, Frontend/E2E and Docker PASS.

Final human acceptance freezes cq-features-v1, cq-strategy-dsl-v1 and cq-binary-backtest-v1 for v0.5.0. Incompatible formulas or semantics require new versions; never silently reinterpret historical evidence. Accepted temporal, outcome, payout, overlap, gap, immutability, replay and metric contracts remain unchanged. All results remain IN-SAMPLE / NOT VALIDATED; only a separately authorized REQ-006 may implement statistical validation.

Release gates: final documentation/version commit CI green → PR merge → integrated main CI green → v0.5.0 tag on that exact main commit. Final feature SHA, main SHA, CI run IDs, test counts and tag verification are recorded in the final release evidence comment on PR #4 and the delivery report, avoiding a self-referential commit. No functional changes or REQ-006 work are part of this closure.
