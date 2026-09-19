# Project State

## Current version
0.7.0-dev — REQ-007 QA on codex/req-007-live-scanner / PR #6. Baseline main/v0.6.0 a7a304981b50c6d30261d3460f6e547383e09e8d. REQ-001–006 remain DONE / Human Acceptance PASS. No merge or release tag authorized for REQ-007 before separate human acceptance.

## Functional
REQ-006 — DONE, Human Acceptance PASS on 2026-09-19. CiberQuant provides Authentication, Trading Accounts, Risk Engine, Session Manager, Trading Journal, Market Data, Dataset Provenance, Data Quality, Candle Cataloger, Feature Engine, Indicator Engine, Strategy DSL, Strategy Lab, Binary Outcome Engine, Binary Backtesting Engine, Validation Engine, Chronological Holdout, Walk-Forward Evaluation, Block Bootstrap and Historical Validation State. Official cq-validation-v1 and its three v1 dependencies are frozen; incompatible changes require new versions. Historical validation PASS is not a guarantee of future profitability, safety or external blindness.
REQ-005 — DONE, Human Acceptance PASS on 2026-09-19. CiberQuant provides Authentication, Trading Accounts, Risk Engine, Session Manager, Trading Journal, Market Data Ingestion, Dataset Provenance, Data Quality, Candle Cataloger, Feature Engine, Indicator Engine, Strategy DSL, Strategy Lab, Binary Outcome Engine, Binary Backtesting Engine and Backtest Evidence. cq-features-v1, cq-strategy-dsl-v1 and cq-binary-backtest-v1 are frozen. Research results remain IN-SAMPLE / NOT VALIDATED, using exact unit stake and fixed payout assumptions.
REQ-004 — DONE, Human Acceptance PASS on2026-09-19. CiberQuant provides Authentication, Trading Accounts, Risk Engine, Session Manager, Trading Journal, Market Data Ingestion, Dataset Provenance, Data Quality, Candle Cataloger, Feature Engine, Indicator Engine and Feature Lab. Official engine cq-features-v1 is frozen; full-candle features are available at close_time only.
REQ-003 — DONE, Human Acceptance PASS on 2026-09-19. CiberQuant provides Authentication, Trading Accounts, Risk Engine, Session Manager, Trading Journal, Market Data Ingestion, Dataset Provenance, Data Quality and Candle Cataloger. The accepted catalog contract describes bullish/bearish/doji candles, never binary trade results.
REQ-002 is DONE with Human Acceptance PASS. Functional flow: login → account → risk → session → trades → ledger → journal → analytics. Real authentication, accounts, auditable ledger, Risk Engine, session manager, trade journal, connected dashboard, analytics and journal are supported by backend/frontend tests, browser E2E, Docker and CI. Backend health and market-data providers remain functional.

## Partial
Behavioural analytics remain future scope. RiskProfile retains the user-scoped Foundation model; profile editing/account-specific assignments are not part of this delivery. Import recovery/background ingestion is separate P2 debt DATA-001.

## Foundation only
Historical validation is human-accepted in REQ-006. REQ-007 adds read-only live/replay scanning and separate paper observations; positive in-sample results never automatically confer statistical validation.

## Planned
Integrated research workspace (REQ-008, not started).

## Modules in development
REQ-007 final human QA correction: research-mode explicit payout fallback/expiry now take precedence over historical reference assumptions. Pure paper-config resolver and source evidence; truthful research/provider UI; four-case integration regressions verify actual next-open/expiry/Decimal outcomes. Status remains QA, Human Acceptance PENDING; no merge or REQ-008.
REQ-007 Live Data & Strategy Scanner: cq-live-data-v1 / cq-scanner-v1; dedicated singleton worker, canonical incremental feature state, private watchlists, exact dataset validation compatibility, payout warning, immutable events and paper outcomes, migration006, SSE/snapshot UI, deterministic Replay/Mock, isolated optional MT5. Evidence and current gates: [REQ-007](requirements/REQ-007-live-scanner.md).

## Experimental / disabled
MT5, IQ Option and Replay flags default false. IQ has a pinned real PRACTICE-only async read-only transport; real binary REGULAR/OTC history/realtime and OTC scanner smoke PASS on2026-09-19. No OTC fallback. MT5 real terminal smoke remains optional/unperformed. Auto-trading/order sending absent; ML not implemented.

## Migrations / integrations
006_live_scanner adds watchlists/items, provider snapshot cache, live observation provenance, immutable scanner events and outcomes. No financial/raw candle schema change. Downgrade loses scanner/provenance evidence; export/backup first. PostgreSQL migration/tests PASS in CI35468326588/35468338708; final HEAD checks and counts recorded in REQ-007/PR #6 handoff.
005_validation adds validation_runs/validation_segments and backtest purpose MANUAL/VALIDATION. PostgreSQL migration validation PASS in CI. Downgrade deletes validation plans and loses child-purpose distinction; backup/export first. No raw/financial schema changes.
Alembic001–003 stable;004_strategy_backtesting adds accepted strategies, strategy_versions, backtest_runs, backtest_trades and constraints/indexes. PostgreSQL/JSONB target; SQLite local test harness. Raw candles and financial tables/contracts unchanged. Downgrade004 discards derived research evidence; export/backup first.

## Git workflow
REQ-001 is the bootstrap exception. `main` was created from the validated REQ-001 branch and configured as the default branch; both branches are synchronized. REQ-002 onward requires feature branch, Pull Request, CI and QA before merge. See [ADR-005](adr/ADR-005-git-development-workflow.md).

## Known issues
[LIVE-001](debt/LIVE-001-provider-operations.md): provider smoke/operations, bounded canonical history, interrupted-paper recovery and capacity follow-ups. Real IQ OTC is delivered in REQ-007; unofficial protocol drift/digital support/soak testing remain separate future work. REQ-008 is not started.
[UX-001](debt/UX-001-manual-vs-validation-child-backtests.md): Strategy list last_backtest can reference a validation child although GET /backtests correctly defaults to MANUAL. Separate presentation improvement, not a calculation/evidence defect. All listed debts remain nonblocking for v0.6.0; no debt implementation during release closure.
[VALIDATION-001](debt/VALIDATION-001-stale-validation-run-recovery.md) stale phase recovery and [VALIDATION-002](debt/VALIDATION-002-multiple-testing-research-lineage.md) broader multiple-testing lineage are separate P2 scope. Holdout reuse warnings exist; perfect external blindness is not claimed.
[QUANT-002 — Historical Engine Version Replay](debt/QUANT-002-historical-engine-version-replay.md): future registry/dispatcher must preserve replay of frozen v1 evidence when incompatible engines arrive. P2, not a v0.5.0 blocker; documentation only in REQ-005. All existing debts below remain nonblocking for v0.5.0.
[BACKTEST-001](debt/BACKTEST-001-stale-run-recovery.md): stale synchronous RUNNING recovery. [BACKTEST-002](debt/BACKTEST-002-execution-realism.md): payout history/latency/spread realism. Both P2, separate future scope. UI flat AND/OR editor; nested DSL supported through API, never silently flattened.
[QUANT-001 — Feature checkpoints](debt/QUANT-001-feature-checkpoints.md): future versioned exact acceleration; current origin calculation rejects requests beyond caps without approximation. No implementation in REQ-004. Frontend bundle size warning and dependency warnings remain P2.
REQ-003 P2: [DATA-001 — Market Data Import Recovery](debt/DATA-001-stale-processing-import-recovery.md). Interrupted synchronous imports can remain PROCESSING; raw data stays protected, exact reimport is idempotent and batches remain visible. Not a v0.3.0 blocker; no recovery implementation in this release.
Final human acceptance PASS on 2026-09-19 verified all four financial corrections: hard per-trade risk cap, net session loss, no DRAW/CANCELLED ledger movements, and backend-only session start requiring RiskProfile. No functional P0/P1 remains within REQ-002. P2: existing authentication dependencies emit deprecation warnings; list pagination is a future scalability improvement. [SEC-001](debt/SEC-001-production-auth-configuration.md) records environment-aware cookie/CORS/HTTPS configuration required before production, not a REQ-002 blocker.

## Active requirements
[REQ-007](requirements/REQ-007-live-scanner.md): QA; automated A–J PASS, Human Acceptance PENDING. REQ-001–006 DONE / PASS. No optimization, ranking, money management, automatic trading or strategy recommendation.

## Next milestones
REQ-007 Live Data & Scanner.
REQ-008 Integrated Research Workspace / v1.0.
REQ-006 is closed. REQ-007 is authorized in development; REQ-008 still requires independent authorization and has not started.
