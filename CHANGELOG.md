# Changelog

## [0.5.0] - 2026-09-19
### Acceptance
- REQ-005 DONE; Human Acceptance PASS on approved HEAD40981e0f25c1cda0d987c23eba0922f35d90db99. No P0/P1 within the accepted scope.
- cq-features-v1, cq-strategy-dsl-v1 and cq-binary-backtest-v1 are frozen. QUANT-002 tracks future historical version replay; no dispatcher implemented in this release.
### Added
- REQ-005 private strategies, immutable version numbering/hashes and cq-strategy-dsl-v1 typed bounded AST with three-state evaluation.
- cq-binary-backtest-v1 causal NEXT_CANDLE_OPEN execution, expiry bars, strict gaps/ranges, overlap policies, exact Decimal unit outcomes and metrics, no financial ledger/stake management.
- Frozen as-of/definition/config evidence, atomic completion/failure audits, owner-scoped paginated APIs, migration004 with PostgreSQL/JSONB constraints and indexes.
- Strategy Lab, immutable version builder/history, run setup, in-sample results, fixed payout warnings, unit equity and trade context inspector.
- Quant, ownership, snapshot, concurrency/migration and frontend/E2E regressions;100k benchmark; DSL/execution semantics and BACKTEST-001/002 debt.
### Boundaries
- cq-features-v1 unchanged. No statistical validation, ranking, martingale, live trading, historical payout/latency model or REQ-006 work. Human Acceptance PASS; results remain IN-SAMPLE / NOT VALIDATED.

## [0.4.0] - 2026-09-19
### Acceptance
- REQ-004 DONE; Human Acceptance PASS on approved HEAD9f670a922ffc1ad7f1de913337a0f5b0374b0487. cq-features-v1 is frozen for this release.
- Full-candle features become available only at close_time, never retrospectively at open_time. QUANT-001 records future exact, versioned checkpoints without implementing them.
### Added
- REQ-004 cq-features-v1: pure Decimal candle features, SMA, SMA-seeded EMA, Wilder RSI/ATR and population Bollinger; registry and convenience STANDARD preset.
- Origin-anchored calculations, immutable candle-ID snapshots, authenticated definitions/compute APIs and exact-or-reject configurable caps.
- Feature Lab with real candlesticks, overlays, RSI/ATR panes, UTC hover, null warmups, gap metadata and bounded table; Lightweight Charts5.2.1 pinned with attribution.
- Deterministic formula, range/snapshot/no-lookahead regressions, USER E2E and100k benchmark; official indicator definitions.
### Boundaries
- No raw-data mutation, derived persistence or migration; no strategies, binary outcomes, backtesting or automatic signals.
- Corrected roadmap: REQ-005 Strategy Lab/Backtesting,006 Validation,007 Live Data/Scanner,008 Integrated Workspace. Human Acceptance PASS; subsequent requirements remain unauthorized.

## [0.3.0] - 2026-09-19
### Acceptance
- REQ-003 DONE; Human Acceptance PASS includes final semantic contract correction. Candle direction is not binary trade outcome.
- DATA-001 records import recovery as separate P2 debt, not a release blocker; no recovery implementation added.
### Fixed
- Human semantic QA: catalog statistics use bullish/bearish candle-direction fields without legacy aliases; distinguish candle color from future binary trade outcomes. Mathematical results unchanged.
### Added
- REQ-003 broker-aware immutable candle identity, import provenance and migration 003.
- ADMIN-only atomic CSV ingestion with UTC/Decimal validation, limits, duplicate/conflict handling and audit events.
- Paginated dataset coverage, import history and candle inspection; backend timeframe options.
- Deterministic C/P/D cataloger for lengths 2–5, gap/doji exclusion and descriptive next-candle distributions.
- Connected Market Data/Cataloger UI, synthetic fixtures, backend/frontend/E2E and PostgreSQL concurrency/migration regressions.
### Boundaries
- No trading recommendations, strategies, indicators, backtesting or live integration. Human acceptance completed PASS; REQ-004 not started.

## [0.1.0] - 2026-09-18
### Added
- Foundation operativa, API FastAPI, PostgreSQL/Alembic, auth, accounts, ledger, sessions, trades, journal y market-data providers.
- Frontend React shell, Docker, CI, testing y documentación de contexto.

### Security
- Passwords hasheados y tokens JWT en cookies HttpOnly.

### QA
- Remote CI run 35415290649 validated backend, PostgreSQL migrations, idempotent seed, tests, frontend and Docker.

## [0.2.0] - 2026-09-19
### Acceptance
- REQ-002 DONE; final Human Acceptance PASS verifies all four financial QA findings. No functional P0/P1 remains in scope.
- Production cookie/CORS/HTTPS configuration is tracked as SEC-001 future security debt, not a blocker for local development.
### Added
- REQ-002 frontend API client, protected routes, account dashboard, session workspace, trade recording and journal workflow.
- Session summary, analytics overview, account ledger and session trade endpoints.
- Backend-authoritative risk preview, session capacity, account selection, filtered history/journal, and recent trades.
- Component workflow tests and real API Chromium QA at desktop/tablet widths, included in CI.
### Fixed
- REQ-002 human financial review: enforce per-trade percentage; calculate session capacity from net P&L; avoid zero-value DRAW/CANCELLED ledger entries; accept account-only session start and require backend RiskProfile.
- Cross-account trade references and cross-user journal links are rejected.
- Serialized PostgreSQL financial writes; fresh risk snapshot on session start and authoritative balance refresh.
- Reproducible frontend Docker dependencies, API environment variable and Compose startup smoke checks.
