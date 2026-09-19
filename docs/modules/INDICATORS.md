# Indicators
REQ-004 implements an on-demand, pure Decimal engine (`cq-features-v1`), candle morphology/returns/continuity, SMA, SMA-seeded EMA, Wilder RSI/ATR and population Bollinger. Status and evidence: [REQ-004](../requirements/REQ-004-feature-indicator-engine.md).

Official formulas, warmups, canonical keys, precision and edge cases: [INDICATOR_DEFINITIONS](../INDICATOR_DEFINITIONS.md). Registry/specs live in `backend/app/features/`; SQL is isolated in its repository. No external TA library, raw changes, derived-data persistence or migration.

Authenticated read-only endpoints: `GET /api/v1/features/definitions` and `POST /api/v1/features/compute`. Input: dataset identity, timezone-aware start inclusive/end exclusive, optional as-of candle ID, include_candle_features, typed indicator specs. Decimal multipliers must be strings. The backend provides defaults, parameter bounds, generated keys and warmups; STANDARD is convenience, not a strategy.

Every computation captures a dataset ID ceiling and calculates from that snapshot's origin, not the requested start. Gaps are flagged without resetting recursive state. Exact origin computations above configured source/response/spec limits fail with422; no approximate seeds. Cache/checkpoints remain future work. Preserve dataset identity, version, specs, range and as-of ID to replay results.

`/features` exposes Feature Lab: coverage selector, editable specs, explicit Analyze, real candlesticks, SMA/EMA/Bollinger overlays, RSI/ATR panes, UTC hover strings, gap markers, metadata and20-row table pages. Decimal-to-number conversion occurs only for chart rendering. No signals or outcome predictions. Lightweight Charts5.2.1 is pinned; attribution is retained.

REQ-005 consumes these keys without reimplementing indicator formulas; cq-features-v1 source is unchanged from v0.4.0. Incompatible formula changes require a new engine version and deterministic regression fixtures. Backtest evaluations use full internal Decimal values; persisted signal context displays the documented18-place serialization, not a recomputation of the decision.
