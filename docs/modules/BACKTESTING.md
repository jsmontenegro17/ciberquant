# Backtesting
Purpose: deterministic simulations without lookahead. Status: planned. Future tables: backtest_runs/backtest_trades; chronological train/validation/test and walk-forward required.

## Architecture boundary for future REQ-005 (not implemented)

REQ-005 will consume the REQ-004 Feature Engine plus a separate Binary Outcome Engine. It must request canonical feature specs/keys and preserve calculation_version/as_of_candle_id; it must not reimplement indicators.

Cataloger C/P/D describes candle open→close, not binary WIN/LOSS/DRAW. Never substitute bullish/bearish next-candle probabilities for CALL/PUT win probabilities. A future `BinaryOutcome` requires entry_time, entry_price, expiry_time, expiry_price, direction (CALL/PUT) and a result computed against the actual entry/expiry prices. For example entry100, candle open102/close101 is bearish, but PUT at100 expiring101 loses. See [Candle Direction vs Binary Outcome](CATALOGER.md#candle-direction-vs-binary-outcome). No backtesting code is added by this note.
