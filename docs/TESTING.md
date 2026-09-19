# Testing

Unit tests cover money formulas, risk limits and market-data quality. API/integration tests use an isolated SQLite test database only as a test harness; CI additionally applies Alembic to a clean PostgreSQL service before running them. Quant regression fixtures are deterministic and must be extended for cataloger/backtesting. Run `cd backend; python -m pytest` and frontend checks with `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.
