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
| Strategies | [STRATEGIES](modules/STRATEGIES.md) | future REQ-005 |
| Backtesting / validation | [BACKTESTING](modules/BACKTESTING.md), [VALIDATION](modules/VALIDATION.md) | planned |
| Analytics | [ANALYTICS](modules/ANALYTICS.md) | `backend/app/api/trading.py` |

Machine-readable map: [CONTEXT_MANIFEST.yaml](CONTEXT_MANIFEST.yaml). Accepted delivery: [REQ-004](requirements/REQ-004-feature-indicator-engine.md), DONE / Human Acceptance PASS, version0.4.0; REQ-001/002/003 remain DONE. Next roadmap: REQ-005 Strategy Lab & Binary Backtesting, REQ-006 Validation & Walk-Forward, REQ-007 Live Data & Scanner, REQ-008 Integrated Research Workspace/v1.0. None started.

P2 quant debt: [QUANT-001 — Feature checkpoints](debt/QUANT-001-feature-checkpoints.md). Official cq-features-v1 is frozen; full-candle features become available at close_time only.

Future security debt: [SEC-001 — Production authentication configuration](debt/SEC-001-production-auth-configuration.md), required before production and not a REQ-002 blocker.

P2 data debt: [DATA-001 — Market Data Import Recovery](debt/DATA-001-stale-processing-import-recovery.md), not a v0.3.0 blocker.

Frontend entry: `frontend/src/app/router.tsx`; HTTP client: `frontend/src/api/client.ts`; feature screens: `frontend/src/features/`; regression tests: `frontend/src/features/sessions/workflow.test.tsx`; real API browser QA: `frontend/e2e/session.spec.ts`.

REQ-003 UI/tests: `frontend/src/features/market-data/`, `frontend/e2e/market-data.spec.ts`; backend tests: `backend/tests/test_req003.py`, `backend/tests/test_market_data_migration.py`; synthetic fixtures: `examples/market_data/`; benchmark: `backend/scripts/benchmark_cataloger.py`.
