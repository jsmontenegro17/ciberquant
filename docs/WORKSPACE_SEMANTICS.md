# Integrated Research Workspace — REQ-008

Accepted in REQ-008, Human Acceptance PASS on2026-09-19. Workspace is a read-only projection, not a seventh engine. `/workspace` requires an explicitly chosen canonical dataset (source/broker/symbol/market_type/timeframe) and immutable StrategyVersion ID. No default substitution or ranking. Dataset availability is shared as in the existing Market Data contract; strategies/runs/watch items/events/outcomes are owned. All GETs have no side effects.

## Pipeline and evidence

DATA uses indexed SQL coverage; FEATURES points to persisted run/event evidence, not recalculated indicators (specs alone are not proof); STRATEGY links the concrete version; BACKTEST selects MANUAL only; VALIDATION keeps its own verdict and sealed/revealed lifecycle; SCANNER exposes current owned item state/heartbeat; PAPER links a persisted outcome, not a broker trade. READY means evidence is available, not profitable or approved for trading. Missing/stale/failed/incompatible/unavailable remains explicit. `/dashboard` retains its financial semantics.

Overview loads latest exact-context evidence and at most20 watch items. History/events/paper cohorts are separately paginated (max100). Large equity curves and configuration snapshots are deferred in summaries; raw candles/trade histories are never downloaded to construct the overview. Strategy list uses batched queries, not per-row child lookups. Backend canonical metrics are displayed as stored; no frontend win-rate calculations.

## Lineage and comparison

Manual runs and validation have distinct IDs, engine versions, as-of IDs, time windows and assumptions. Validation child IDs remain linked under validation, never Last manual backtest. Event inspector links owned ScannerEvent → raw candle/import/live observation provenance → ScannerOutcome with provider/received times, exact feature/DSL/live/scanner versions and stored payout/expiry sources. Provenance is limited20 per candle; raw market data is the existing shared catalog, not private strategy evidence.

Comparison flags full-identity, StrategyVersion, engine, payout, expiry, overlap and incomplete-state differences. Same context still does not mean interchangeable samples: manual in-sample, historical validation TEST, LIVE paper and REPLAY paper are never pooled. Paper counts are SQL aggregations of persisted outcomes grouped by mode, direction, engines, payout snapshot/source/product and expiry/source/result. GAP/UNAVAILABLE are not losses; pending signals are not resolved outcomes. No newly invented pooled win rate. A simple predicate used in IQ tests demonstrates plumbing only, not profitability.

Journal/sessions remain separate user-owned evidence accessible beside the research workflow; no automatic associations, copied paper trades or ledger/session writes. Settings remains outside scope: no required nonsecret user preference has been identified, and broker credentials never belong in UI.

## Human QA checklist

1. Open Research Workspace, select all five dataset axes and a specific version. Verify no automatic defaults.
2. Compare a missing context with a populated fixture; inspect each stage and timestamp.
3. Open Last manual backtest and Latest historical validation; confirm their IDs differ from validation child IDs.
4. Inspect comparison assumptions/sources and an explicitly incompatible dataset via API.
5. Inspect owned scanner event and paper outcome; check LIVE/REPLAY and timestamps/source versions.
6. Page datasets, strategies, versions, event history and paper cohorts.
7. Stop a test worker: health becomes STALE; independent research pages remain available.
8. Review failed-job recovery audit and consumed reveal; it must not reseal or rerun.
9. Verify production configuration/HTTPS/Origin/cookies using deployment checklist.
10. Review sanitized real IQ soak and provider health. Confirm PRACTICE/read-only/zero orders.
11. Test cross-user IDs and error/loading/empty states. No secret/account crossover.

Human Acceptance: PASS on2026-09-19; implementation 618301e84e8a65f2cbe7e2a46bc6384524db2e93. Closure authorized with final feature CI → merge → main CI → tag gates. No subsequent requirement authorized.
