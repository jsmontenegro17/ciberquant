# Context Index

| Área | Documento | Código principal |
|---|---|---|
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

Machine-readable map: [CONTEXT_MANIFEST.yaml](CONTEXT_MANIFEST.yaml). Active: REQ-006, version0.6.0-dev, IN_PROGRESS / Human Acceptance PENDING. Stable main/tag v0.5.0; REQ-001–005 DONE / PASS. Next: REQ-007 Live Data & Scanner, REQ-008 Integrated Research Workspace/v1.0, neither authorized nor started.

Validation regressions: `backend/tests/test_validation_protocol.py`, `test_validation_api.py`, `test_validation_migration.py`, `validation_fixture.py`; frontend `validation.test.tsx`, `e2e/validation.spec.ts`; performance `backend/scripts/benchmark_validation.py`. P2 [VALIDATION-001](debt/VALIDATION-001-stale-validation-run-recovery.md), [VALIDATION-002](debt/VALIDATION-002-multiple-testing-research-lineage.md).

Research regressions: `backend/tests/test_backtest_engine.py`, `test_research_api.py`, `test_research_migration.py`; manual fixture `backtest_fixture.py`; UI/E2E `frontend/src/features/research/research.test.tsx`, `frontend/e2e/research.spec.ts`; benchmark `backend/scripts/benchmark_backtest.py`. Debt: [BACKTEST-001](debt/BACKTEST-001-stale-run-recovery.md), [BACKTEST-002](debt/BACKTEST-002-execution-realism.md).

P2 quant debt: [QUANT-001 — Feature checkpoints](debt/QUANT-001-feature-checkpoints.md), [QUANT-002 — Historical Engine Version Replay](debt/QUANT-002-historical-engine-version-replay.md). Official cq-features-v1, cq-strategy-dsl-v1 and cq-binary-backtest-v1 are frozen; full-candle features become available at close_time only. No multi-version dispatcher is implemented in REQ-005.

Future security debt: [SEC-001 — Production authentication configuration](debt/SEC-001-production-auth-configuration.md), required before production and not a REQ-002 blocker.

P2 data debt: [DATA-001 — Market Data Import Recovery](debt/DATA-001-stale-processing-import-recovery.md), not a v0.3.0 blocker.

Frontend entry: `frontend/src/app/router.tsx`; HTTP client: `frontend/src/api/client.ts`; feature screens: `frontend/src/features/`; regression tests: `frontend/src/features/sessions/workflow.test.tsx`; real API browser QA: `frontend/e2e/session.spec.ts`.

REQ-003 UI/tests: `frontend/src/features/market-data/`, `frontend/e2e/market-data.spec.ts`; backend tests: `backend/tests/test_req003.py`, `backend/tests/test_market_data_migration.py`; synthetic fixtures: `examples/market_data/`; benchmark: `backend/scripts/benchmark_cataloger.py`.
