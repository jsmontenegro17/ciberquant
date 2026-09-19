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
| Validation | [VALIDATION](modules/VALIDATION.md) | future REQ-006 |
| Analytics | [ANALYTICS](modules/ANALYTICS.md) | `backend/app/api/trading.py` |

Machine-readable map: [CONTEXT_MANIFEST.yaml](CONTEXT_MANIFEST.yaml). Active delivery: [REQ-005](requirements/REQ-005-strategy-lab-binary-backtesting.md), version0.5.0-dev. Stable main/tag v0.4.0; REQ-001/002/003/004 remain DONE / Human Acceptance PASS. Next: REQ-006 Validation & Walk-Forward, REQ-007 Live Data & Scanner, REQ-008 Integrated Research Workspace/v1.0. None authorized or started.

Research regressions: `backend/tests/test_backtest_engine.py`, `test_research_api.py`, `test_research_migration.py`; manual fixture `backtest_fixture.py`; UI/E2E `frontend/src/features/research/research.test.tsx`, `frontend/e2e/research.spec.ts`; benchmark `backend/scripts/benchmark_backtest.py`. Debt: [BACKTEST-001](debt/BACKTEST-001-stale-run-recovery.md), [BACKTEST-002](debt/BACKTEST-002-execution-realism.md).

P2 quant debt: [QUANT-001 — Feature checkpoints](debt/QUANT-001-feature-checkpoints.md). Official cq-features-v1 is frozen; full-candle features become available at close_time only.

Future security debt: [SEC-001 — Production authentication configuration](debt/SEC-001-production-auth-configuration.md), required before production and not a REQ-002 blocker.

P2 data debt: [DATA-001 — Market Data Import Recovery](debt/DATA-001-stale-processing-import-recovery.md), not a v0.3.0 blocker.

Frontend entry: `frontend/src/app/router.tsx`; HTTP client: `frontend/src/api/client.ts`; feature screens: `frontend/src/features/`; regression tests: `frontend/src/features/sessions/workflow.test.tsx`; real API browser QA: `frontend/e2e/session.spec.ts`.

REQ-003 UI/tests: `frontend/src/features/market-data/`, `frontend/e2e/market-data.spec.ts`; backend tests: `backend/tests/test_req003.py`, `backend/tests/test_market_data_migration.py`; synthetic fixtures: `examples/market_data/`; benchmark: `backend/scripts/benchmark_cataloger.py`.
