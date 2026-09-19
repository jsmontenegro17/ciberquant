# Context Index

| Área | Documento | Código principal |
|---|---|---|
| Auth / users | [AUTH](modules/AUTH.md), [USERS](modules/USERS.md) | `backend/app/api/auth.py`, `models.py` |
| Accounts / ledger | [TRADING_ACCOUNTS](modules/TRADING_ACCOUNTS.md) | `backend/app/services/finance.py` |
| Risk / sessions | [RISK_ENGINE](modules/RISK_ENGINE.md), [SESSIONS](modules/SESSIONS.md) | `backend/app/services/finance.py` |
| Trades / journal | [TRADES](modules/TRADES.md), [JOURNAL](modules/JOURNAL.md) | `backend/app/api/trading.py` |
| Market data | [MARKET_DATA](modules/MARKET_DATA.md) | `backend/app/services/market_data.py` |
| Cataloger | [CATALOGER](modules/CATALOGER.md) | planned |
| Indicators / strategies | [INDICATORS](modules/INDICATORS.md), [STRATEGIES](modules/STRATEGIES.md) | planned |
| Backtesting / validation | [BACKTESTING](modules/BACKTESTING.md), [VALIDATION](modules/VALIDATION.md) | planned |
| Analytics | [ANALYTICS](modules/ANALYTICS.md) | `backend/app/api/trading.py` |

Machine-readable map: [CONTEXT_MANIFEST.yaml](CONTEXT_MANIFEST.yaml). Current delivery: [REQ-002](requirements/REQ-002-session-manager-trading-journal.md).

Frontend entry: `frontend/src/app/router.tsx`; HTTP client: `frontend/src/api/client.ts`; feature screens: `frontend/src/features/`; regression tests: `frontend/src/features/sessions/workflow.test.tsx`; real API browser QA: `frontend/e2e/session.spec.ts`.
