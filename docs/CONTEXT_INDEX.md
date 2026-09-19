# Context Index

Active: [REQ-008](requirements/REQ-008-integrated-research-workspace.md), 1.0.0-dev / BLOCKED — UPSTREAM FINALITY POLICY REQUIRED / Human Acceptance PENDING. [Workspace semantics](WORKSPACE_SEMANTICS.md), [operations/deployment](OPERATIONS_DEPLOYMENT.md), [real IQ probe](providers/IQOPTION_SOAK_2026-09-19.md), [reproduced IQ finality revisions](providers/IQOPTION_FINALITY_INVESTIGATION.md). `/workspace` and `/operations/status`; backend api/workspace.py, api/operations.py, operations.py; migration007_operations. REQ-008 is now authorized; historical v0.7.0 statements below remain release context.

REQ-007 real IQ: [setup/pinned protocol](providers/IQOPTION_EXPERIMENTAL.md), [2026-09-19 real PRACTICE smoke](providers/IQOPTION_SMOKE_2026-09-19.md); `backend/app/live/iqoption.py`, `iq_transport.py`, `backend/tests/test_iqoption.py`, `backend/scripts/smoke_iqoption.py`. Mandatory in this requirement, not deferred to REQ-008.

| Área | Documento | Código principal |
|---|---|---|
| Live / Scanner | [Protocol](LIVE_DATA_PROTOCOL.md), [Semantics](SCANNER_SEMANTICS.md), [REQ-007](requirements/REQ-007-live-scanner.md) | `backend/app/live/`, `backend/app/api/scanner.py`, `frontend/src/features/scanner/`, migration006 |
| Auth / users | [AUTH](modules/AUTH.md), [USERS](modules/USERS.md) | `backend/app/api/auth.py`, `models.py` |
| Accounts / ledger | [TRADING_ACCOUNTS](modules/TRADING_ACCOUNTS.md) | `backend/app/services/finance.py` |
| Risk / sessions | [RISK_ENGINE](modules/RISK_ENGINE.md), [SESSIONS](modules/SESSIONS.md) | `backend/app/services/finance.py` |
| Trades / journal | [TRADES](modules/TRADES.md), [JOURNAL](modules/JOURNAL.md) | `backend/app/api/trading.py` |
| Market data | [MARKET_DATA](modules/MARKET_DATA.md), [CSV format](MARKET_DATA_CSV_FORMAT.md) | `backend/app/market_data/`, `backend/app/api/market_data.py` |
| Cataloger | [CATALOGER](modules/CATALOGER.md) | `backend/app/cataloger/` |
| Features / indicators | [INDICATORS](modules/INDICATORS.md), [Definitions](INDICATOR_DEFINITIONS.md) | `backend/app/features/`, `backend/app/api/features.py`, `frontend/src/features/features/` |
| Strategies | [STRATEGIES](modules/STRATEGIES.md), [DSL](STRATEGY_DSL.md) | `backend/app/strategies/`, `backend/app/api/research.py`, `frontend/src/features/research/` |
| Backtesting | [BACKTESTING](modules/BACKTESTING.md), [Semantics](BINARY_BACKTEST_SEMANTICS.md) | `backend/app/backtesting/`, migration004 |
| Validation | [VALIDATION](modules/VALIDATION.md), [Protocol](VALIDATION_PROTOCOL.md), [REQ-006](requirements/REQ-006-validation-walk-forward.md) | `backend/app/validation/`, `backend/app/api/validation.py`, `frontend/src/features/validation/`, migration005 |
| Analytics | [ANALYTICS](modules/ANALYTICS.md) | `backend/app/api/trading.py` |

Machine-readable map: [CONTEXT_MANIFEST.yaml](CONTEXT_MANIFEST.yaml). Accepted release: REQ-007, version0.7.0, DONE / Human Acceptance PASS. REQ-001–007 DONE / PASS. Integrated main SHA, CI and tag evidence: [PR #6](https://github.com/jsmontenegro17/ciberquant/pull/6). cq-live-data-v1 and cq-scanner-v1 are frozen with their four existing quant dependencies. REQ-008 Integrated Research Workspace/v1.0 is authorized and implemented in PR #7; acceptance remains blocked, not released.

Provider docs: [MT5](providers/MT5.md), [IQ experimental](providers/IQOPTION_EXPERIMENTAL.md), [Replay](providers/REPLAY.md). Scanner regressions: `test_live_engine.py`, `test_scanner_api.py`, `test_live_migration.py`, `test_mt5_provider.py`, `scanner.test.tsx`, `e2e/scanner.spec.ts`. Benchmark `backend/scripts/benchmark_live.py`; operations debt [LIVE-001](debt/LIVE-001-provider-operations.md).

Validation regressions: `backend/tests/test_validation_protocol.py`, `test_validation_api.py`, `test_validation_migration.py`, `validation_fixture.py`; frontend `validation.test.tsx`, `e2e/validation.spec.ts`; performance `backend/scripts/benchmark_validation.py`. P2 [VALIDATION-001](debt/VALIDATION-001-stale-validation-run-recovery.md), [VALIDATION-002](debt/VALIDATION-002-multiple-testing-research-lineage.md).

Official cq-validation-v1 and its three v1 engine dependencies are frozen. P2 [UX-001 — Manual vs validation child backtests](debt/UX-001-manual-vs-validation-child-backtests.md) is future presentation debt, not a v0.6.0 blocker.

Research regressions: `backend/tests/test_backtest_engine.py`, `test_research_api.py`, `test_research_migration.py`; manual fixture `backtest_fixture.py`; UI/E2E `frontend/src/features/research/research.test.tsx`, `frontend/e2e/research.spec.ts`; benchmark `backend/scripts/benchmark_backtest.py`. Debt: [BACKTEST-001](debt/BACKTEST-001-stale-run-recovery.md), [BACKTEST-002](debt/BACKTEST-002-execution-realism.md).

P2 quant debt: [QUANT-001 — Feature checkpoints](debt/QUANT-001-feature-checkpoints.md), [QUANT-002 — Historical Engine Version Replay](debt/QUANT-002-historical-engine-version-replay.md). Official cq-features-v1, cq-strategy-dsl-v1 and cq-binary-backtest-v1 are frozen; full-candle features become available at close_time only. No multi-version dispatcher is implemented in REQ-005.

Future security debt: [SEC-001 — Production authentication configuration](debt/SEC-001-production-auth-configuration.md), required before production and not a REQ-002 blocker.

P2 data debt: [DATA-001 — Market Data Import Recovery](debt/DATA-001-stale-processing-import-recovery.md), not a v0.3.0 blocker.

Frontend entry: `frontend/src/app/router.tsx`; HTTP client: `frontend/src/api/client.ts`; feature screens: `frontend/src/features/`; regression tests: `frontend/src/features/sessions/workflow.test.tsx`; real API browser QA: `frontend/e2e/session.spec.ts`.

REQ-003 UI/tests: `frontend/src/features/market-data/`, `frontend/e2e/market-data.spec.ts`; backend tests: `backend/tests/test_req003.py`, `backend/tests/test_market_data_migration.py`; synthetic fixtures: `examples/market_data/`; benchmark: `backend/scripts/benchmark_cataloger.py`.
