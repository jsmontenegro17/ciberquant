# Market Data
Purpose: reproducible raw candles. Provider contract: `get_historical_candles`, `get_latest_candles`, `stream_candles`, `get_assets`. Implementations: Mock and CSV. `validate_candle`/`validate_candles` check OHLC, timestamps, duplicates and OTC separation. Database table `candles` is append-only by policy; import endpoint pending.
