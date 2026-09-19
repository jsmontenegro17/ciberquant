# Indicator definitions — cq-features-v1

Official mathematical contract. Derived research features only; never trading signals. Changing seeds, formulas, gap behavior or rounding incompatibly requires a new FEATURE_ENGINE_VERSION.

## Precision and availability

All prices and arithmetic are Decimal, in a dedicated local context: precision50, ROUND_HALF_EVEN. No binary floats in the core and no explicit intermediate quantization. JSON numeric features/OHLC are decimal strings; features rounded HALF_EVEN to18 fractional places only for serialization, trailing zeroes removed. Null means unavailable, never zero. Chart coordinates alone convert strings to JS numbers; exact tooltip/table retain API strings. A candle's OHLC-derived features become knowable only at its close_time; no assumption that they existed at open_time.

## Candle features

C=close>open (bullish); P=close<open (bearish); D=equal (exact doji). body_size=abs(close-open); candle_range=high-low; upper_wick=high-max(open,close); lower_wick=min(open,close)-low. Each *_to_range_ratio divides its component by range; close_position=(close-low)/range. Range0 makes all four ratios null. close_return_percent=(close/previous_available_close-1)*100; first candle null.

## Continuity

Canonical timeframe from Market Data. First candle gap_before=false, gap_seconds=0, contiguous_run_length=1. Thereafter delta=open_time-previous_open_time; gap_before=(delta!=timeframe duration), gap_seconds=delta-duration in seconds (negative for shorter irregular intervals), run increments only if contiguous, otherwise resets1. No indicator state resets at gaps. Returns/TR compare the previous available close, including across gaps. Future strategies decide whether to accept discontinuous windows.

## SMA / EMA

SMA(n) = sum of latest n closes / n; first available index n-1. EMA alpha=2/(n+1); seed=SMA(first n closes), at index n-1. Thereafter alpha*close+(1-alpha)*previousEMA. Earlier rows null. n is an integer2–500.

## Wilder RSI

n changes require n+1 candles; first index n. gain=max(delta_close,0), loss=max(-delta_close,0). Seed averages are arithmetic means of first n gains/losses. Then avg=(previous_avg*(n-1)+current)/n. RSI=100-100/(1+avg_gain/avg_loss). Loss0/gain>0→100; gain0/loss>0→0; both0→50. Default n14.

## True Range / Wilder ATR

First TR=high-low. Subsequent TR=max(high-low,abs(high-previous_close),abs(low-previous_close)). ATR seed=mean(first n TR), at index n-1; later (previousATR*(n-1)+TR)/n. Default n14.

## Bollinger

Default n20, multiplier2. Middle=SMA(n); population variance=mean((close-middle)^2), ddof0. stddev=Decimal sqrt(variance). Upper=middle+multiplier*stddev; lower=middle-multiplier*stddev; width=(upper-lower)/middle, null if middle0. First available index n-1; earlier all5 outputs null. Explicit window variance avoids unstable subtraction of large squared prices. This is O(n*period), period capped500.

## Registry and stable keys

SMA→sma_n; EMA→ema_n; RSI→rsi_n; ATR→atr_n. BOLLINGER→bb_middle_n_m, bb_upper_n_m, bb_lower_n_m, bb_stddev_n_m, bb_width_n_m. Multiplier normalizes decimal trailing zeroes; decimal point becomes p (2.5→2p5). Multiplier must be >0 and <=10, maximum6 fractional places; JSON strings recommended, floating JSON numbers rejected. Duplicate specs/keys rejected. Definition API exposes constraints, defaults, key templates, warmup candle requirements and calculation version.

STANDARD = EMA9/20/50, RSI14, ATR14, BOLLINGER20/2. Research convenience only, not a strategy or optimal parameter claim.

## Reproducibility

Capture as_of_candle_id from dataset MAX(id) at request start or accept a nonnegative caller ceiling not exceeding that maximum. All repository queries are dataset-scoped and id<=ceiling. Origin anchor is earliest snapshot candle. start filters output only, end is exclusive by open_time. Backfill with newer IDs cannot change a saved snapshot. No future candle affects earlier outputs. Append-only source data remains untouched.

Exact computation caps: FEATURE_ENGINE_MAX_SOURCE_CANDLES=250000, FEATURE_API_MAX_RETURN_ROWS=10000, FEATURE_API_MAX_INDICATOR_SPECS=12 (environment configurable). Reject exceeded caps; never approximate a recursive seed. Empty dataset/snapshot has as_of0 and null anchor. PostgreSQL same-dataset import serialization protects ID-order snapshots against ingestion writers; no cross-dataset rows are used.
