# Backtesting
Purpose: deterministic simulations without lookahead. Status: planned. Future tables: backtest_runs/backtest_trades; chronological train/validation/test and walk-forward required.

## Architecture boundary for future REQ-005 (not implemented)

REQ-005 will consume the REQ-004 Feature Engine plus a separate Binary Outcome Engine. It must request canonical feature specs/keys and preserve calculation_version/as_of_candle_id; it must not reimplement indicators.

## Feature Availability

All features using the complete candle T are available only at `T.close_time`, NOT `T.open_time`: direction, morphology, close, EMA, RSI, ATR, Bollinger and any feature depending on T's closing price/high/low. A candle spanning10:00→10:01 produces its closing RSI at10:01; using that RSI for an entry at10:00 is prohibited lookahead. REQ-005 may use it only for an entry after availability under explicitly defined timing rules, and must test this invariant in the future Binary Backtesting Engine. No backtester is implemented here.

## Frozen feature snapshots

Every future backtest must store `feature_engine_version`, `as_of_candle_id`, full dataset identity and feature specifications (plus its requested time range). Never claim reproducibility against unfrozen latest data. `cq-features-v1` is the official0.4.0 engine: incompatible formula, seed, warmup, gap, precision or behavior changes require a new FEATURE_ENGINE_VERSION. Replay requires retaining the corresponding immutable raw dataset. Future acceleration must follow [QUANT-001](../debt/QUANT-001-feature-checkpoints.md), not truncate recursive warmup.

Cataloger C/P/D describes candle open→close, not binary WIN/LOSS/DRAW. Never substitute bullish/bearish next-candle probabilities for CALL/PUT win probabilities. A future `BinaryOutcome` requires entry_time, entry_price, expiry_time, expiry_price, direction (CALL/PUT) and a result computed against the actual entry/expiry prices. For example entry100, candle open102/close101 is bearish, but PUT at100 expiring101 loses. See [Candle Direction vs Binary Outcome](CATALOGER.md#candle-direction-vs-binary-outcome). No backtesting code is added by this note.
