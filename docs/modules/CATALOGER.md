# Candle Cataloger

REQ-003: descriptive historical classification, not strategies or trading signals.

## Deterministic semantics

C = close > open (bullish), P = close < open (bearish), D = exact equality (doji). No tolerance. Patterns contain 2–5 candles; the immediately following candle is the outcome. Every adjacent open_time in pattern + outcome must differ by the canonical timeframe duration. Broker close_time conventions do not define continuity.

Engine `app/cataloger/engine.py` is pure and has no DB dependency. Input must be quality-valid, strictly chronological and from exactly one source/broker/symbol/market/timeframe. Mixed feeds or invalid input fail instead of yielding statistics. Repository filters in SQL before streaming; never loads the whole candle table.

include_doji=false excludes any D in the entire observation, including outcome. Filtering does not delete D candles then bridge their timestamps. Start is inclusive, end exclusive, applies to all candles via open_time. No hour/day filter or implicit local timezone in V1.

## Results

GET /api/v1/cataloger/patterns requires dataset/start/end; pattern_length defaults3; include_doji defaults true. Authenticated users may read. Returns requested metadata and lexicographically ordered patterns:
sample_size, next_call/put/doji_count and probability (Decimal string count/sample_size), first/last_observation (outcome open_time UTC), distinct_days (UTC outcome dates).

General counts: candles_examined; eligible_windows (after gap/doji exclusions); windows_skipped_due_to_gaps; windows_skipped_due_to_doji. Gap exclusion takes precedence. For n candles and length L, candidates=max(0,n-L); eligible+gap-skipped+doji-skipped=candidates. Pattern aggregates sum to eligible_windows.

No confidence, recommended direction, ranking of profitability, strategy score or artificial precision. UI displays probabilities as percentages rounded to two decimal places; raw API retains Decimal strings. Small sample label means <30 observations and is exclusively a UX reminder, not a validity threshold.

Historical frequencies do not prove causality, independence, economic advantage or future profitability. Overlapping windows may be autocorrelated. Validation/backtesting and out-of-sample analysis are separate future requirements.

## Boundaries and performance

Single traversal O(n * L), bounded L<=5; sliding window and bounded pattern groups (at most 243). Distinct-day sets retain unique dates per pattern. DB equality-prefix/range query uses the candle identity B-tree. Query cap 250,000 candles by default; reject larger ranges, do not silently truncate. No Redis.

Manual regular fixture: two separate days, each CCCPD repeated three times (30 candles total). For length3: CCC=(6 samples,0 C,6 P,0 D); CCP=(6,0,0,6); CPD/DCC/PDC=(4,4,0,0). Eligible24, gap-skipped3. Separate OTC fixture is all P, never combined. See tests/test_req003.py and examples/market_data/.
