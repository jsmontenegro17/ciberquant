# Backtesting
REQ-005 implements deterministic IN-SAMPLE historical simulations, not statistical validation. Tables: backtest_runs/backtest_trades. Train/validation/test and walk-forward remain REQ-006 scope.

## REQ-005 architecture

REQ-005 consumes the unchanged REQ-004 Feature Engine plus a separate Binary Outcome Engine. It requests canonical specs/keys and preserves feature_engine_version/as_of_candle_id. No indicator is reimplemented. [BINARY_BACKTEST_SEMANTICS](../BINARY_BACKTEST_SEMANTICS.md) is the frozen cq-binary-backtest-v1 contract.

POST `/api/v1/backtests` starts a synchronous, owned run from an immutable strategy version. GET `/backtests`, `/backtests/{id}`, `/backtests/{id}/trades` return owned paginated evidence (trades20/page, max100). FAILED runs return a persisted run/status/error, not fabricated metrics. Strategy snapshot, config snapshot, both hashes, engine versions, dataset ceiling and every trade's signal/entry/expiry/context are stored. No edits/deletes of completed evidence. Migration004 adds only derived research tables/indexes/constraints; no raw or financial table change.

BACKTEST_MAX_SOURCE_CANDLES250000 and BACKTEST_MAX_TRADES10000 are environment-configurable; source/trade limits reject exact calculation instead of truncating. Research JSON bodies are bounded to64KiB. BACKTEST-001 tracks stale RUNNING recovery; BACKTEST-002 tracks execution realism. Output is unit equity, not money. UI always displays IN-SAMPLE / NOT VALIDATED and the fixed payout assumption.

## Feature Availability

All features using the complete candle T are available only at `T.close_time`, NOT `T.open_time`: direction, morphology, close, EMA, RSI, ATR, Bollinger and any feature depending on T's closing price/high/low. A candle spanning10:00→10:01 produces its closing RSI at10:01; using that RSI for an entry at10:00 is prohibited lookahead. The engine enforces next-open entry>=signal_time, with deterministic regression and a database causality constraint.

## Frozen feature snapshots

Every future backtest must store `feature_engine_version`, `as_of_candle_id`, full dataset identity and feature specifications (plus its requested time range). Never claim reproducibility against unfrozen latest data. `cq-features-v1` is the official0.4.0 engine: incompatible formula, seed, warmup, gap, precision or behavior changes require a new FEATURE_ENGINE_VERSION. Replay requires retaining the corresponding immutable raw dataset. Future acceleration must follow [QUANT-001](../debt/QUANT-001-feature-checkpoints.md), not truncate recursive warmup.

Cataloger C/P/D describes candle open→close, not binary WIN/LOSS/DRAW. Never substitute bullish/bearish next-candle probabilities for CALL/PUT win probabilities. BinaryOutcome compares actual entry/expiry prices and direction. Entry100, expiry candle open102/close101 is bearish, but PUT at100 expiring101 loses: permanent regression. See [Candle Direction vs Binary Outcome](CATALOGER.md#candle-direction-vs-binary-outcome).
