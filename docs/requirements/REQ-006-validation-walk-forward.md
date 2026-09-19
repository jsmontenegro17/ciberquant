# REQ-006 — Validation & Walk-Forward Engine

Status: QA
Priority: P1
Classification: CRITICAL
Target: 0.6.0-dev
Base: main / v0.5.0 / 2e2de69ba6fdcfdce0167f44f9f62869aa11774a
Branch: codex/req-006-validation-walk-forward
Human Acceptance: PENDING

## Scope and gates

Implement cq-validation-v1: immutable owned plans for one TESTING StrategyVersion, frozen dataset/as-of/config, chronological candle-based 60/20/20, four fixed-strategy validation folds, computationally sealed test and explicit single reveal, UTC-day block bootstrap, sufficient-evidence-first verdict, derived historical version state, holdout reuse warnings, migration005, APIs and Validation UI.

Reuse frozen cq-features-v1, cq-strategy-dsl-v1 and cq-binary-backtest-v1. Any computation reuse refactor requires exact-output equivalence regression. No optimization, fitting, ranking, automatic trading, money management, hourly analysis or REQ-007.

## Implementation sequence

Protocol and schema → pure chronological/statistical functions → persistence and sealed lifecycle → APIs → UI → deterministic A–I fixtures, ownership, leakage, replay, concurrency and PostgreSQL → E2E →100k benchmark → documentation → PR and green CI → QA. No automatic merge or tag.

## Acceptance A–I

A deterministic 60/20/20; B computational sealing; C four chronological folds; D deterministic bootstrap; E PASS/FAIL/INCONCLUSIVE; F no cross-partition outcomes; G as-of replay after backfill; H historical state/degradation; I full UI reveal workflow. Automated/agent QA PASS; Human Acceptance PENDING.

## Implemented / local evidence — 2026-09-19

Protocol frozen in [VALIDATION_PROTOCOL](../VALIDATION_PROTOCOL.md). Migration005, private APIs, immutable plans/segments, atomic phase persistence, CAS/version-lock reveal, audit, manual/validation backtest purpose, UI preview and explicit confirmation implemented. Feature/DSL/outcome/metrics source unchanged; `simulate_rows` extraction matches six baseline v0.5.0 golden hashes (expiry1/5/60, both overlaps), plus all prior regression.

Backend149 PASS/12 local skips (PostgreSQL opt-in and nonapplicable SQLite locking cases); frontend36 PASS, lint/typecheck/build PASS; full5 E2E PASS, preserving REQ-002–005. PostgreSQL/Docker/remote CI PASS below. No new dependencies; frontend bundle warning~554kB remains P2.

| Acceptance | Evidence | Local result |
|---|---|---|
| A |100-candle exact60/20/20 timestamps; min20 and chronology checks | PASS |
| B | compute spy never reaches test rows; TEST child null, six development runs only | PASS |
| C | four nonoverlapping folds cover validation; canonical-origin indicators | PASS |
| D | two manual unequal day blocks: point1/3,95%[-1,1], fixed seed/2000 resamples | PASS |
| E |1500 deterministic hourly candles PASS; losing final20% FAIL;100-candle INCONCLUSIVE | PASS |
| F | strict segment end/expiry IDs, mutation of future candles leaves trades unchanged | PASS |
| G | same as-of after inserted historical candle gives identical hash/boundaries/evidence | PASS |
| H | persisted PASS then chronologically later FAIL→DEGRADED; inconclusive ignored; replay dedup | PASS |
| I | real USER login→TESTING→preview→SEALED/folds→confirmation→PASS/bootstrap | PASS |

Browser fixture: definition hash `1efbccd7f578c6e43e298eaa8b0e304b53b3e392c48be2dc7233f80a36a9ad58`, dataset VALIDATION_FIXTURE/DEMO/EURUSD/REGULAR/1h, immutable version1, as-of1500, overall2026-01-01→2026-03-04T12:00Z, payout83.5%, expiry1/ALLOW. Config hash `060a6cbbd8317fd526954474672e8d031a82ba449cc17ace90a3655b9a72cec8` in isolated fresh fixture. TRAIN899 trades/750.665units; VALIDATION300/250.5; folds75 trades each/62.625; TEST300/250.5,13 active days, bootstrap[0.835,0.835], PASS. IDs in a shared test suite may differ without changing causal evidence. Screenshots desktop/tablet reviewed; viewport overflow assertion and page-error capture pass.

100k benchmark: development features2.020s, train1.565s, validation0.507s, folds0.144/0.148/0.229/0.152s; separate reveal features2.483s, simulation0.583s, bootstrap0.046s. Windows11/Intel64 Family6 Model151/20 logical CPUs/Python3.12.14. Pure computation, no SQL/JSON/SLA; explicit benchmark cap100000, API cap10000 unchanged.

P0/P1: none identified in automated/agent QA. P2: VALIDATION-001/002, BACKTEST-001/002, QUANT-001/002, DATA-001, SEC-001, dependency and bundle warnings. Human Acceptance PENDING. No merge, tag or REQ-007.

## Remote CI / QA handoff

[PR #5 — REQ-006 Validation & Walk-Forward Engine](https://github.com/jsmontenegro17/ciberquant/pull/5): OPEN, base main, head codex/req-006-validation-walk-forward.

Implementation commit: `3224966b9137e61520ab2390886dd579cf9242d6`. PR CI [35464481642](https://github.com/jsmontenegro17/ciberquant/actions/runs/35464481642) and push CI [35464479292](https://github.com/jsmontenegro17/ciberquant/actions/runs/35464479292): Backend, Frontend/E2E and Docker PASS. PostgreSQL migration005, JSONB/FK/constraints/uniqueness, ORM immutability and concurrent single reveal execute in CI, not merely SQLite. Existing migrations and idempotent seed PASS.

Final QA review additionally enforces section7: changed validation payout/expiry requires a new StrategyVersion and ValidationRun. Preview/creation reject changed parameters; concurrent first plans serialize the choice under the version lock, with PostgreSQL regression. No frozen engine semantics change.

Final QA commit must also retain green CI. Its SHA/run IDs are recorded in PR #5 and the delivery report to avoid a self-referential commit. Stop at QA; require independent Human Acceptance before merge and independent REQ-007 authorization.
