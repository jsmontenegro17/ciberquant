# Testing

Unit tests cover money formulas, risk limits and market-data quality. API/integration tests use an isolated SQLite test database only as a test harness; production remains PostgreSQL. Quant regression fixtures are deterministic and must be extended for cataloger/backtesting. Run `cd backend; python -m pytest` and frontend checks with `npm run lint`, `npm run typecheck`, `npm run build`.
