# Market Data CSV format — REQ-003

One UTF-8 CSV represents exactly one dataset. Select source, broker, symbol, REGULAR or OTC, and timeframe outside the file. Do not repeat metadata columns or mix assets/feeds/markets/timeframes. Empty broker normalizes to UNSPECIFIED; labels are trimmed/uppercased. Supported timeframes: 1m,5m,15m,30m,1h (M1/M5/M15/M30/H1 aliases accepted by backend).

```csv
open_time,close_time,open,high,low,close,tick_volume,spread
2026-09-19T14:00:00Z,2026-09-19T14:01:00Z,1.1000,1.1010,1.0995,1.1008,120,0.0001
```

Required columns: open_time,close_time,open,high,low,close. Optional columns: tick_volume,spread; omit their columns or leave their cells empty. No extra/duplicate headers or mismatched row widths. Filename and MIME type do not substitute for content validation.

All timestamps must contain Z or an explicit UTC offset. 2026-09-19T09:00:00-05:00 is the same instant as 2026-09-19T14:00:00Z. Naive timestamps are rejected, never guessed. Stored/returned timestamps normalize to UTC. close_time must be greater than open_time. Rows must be strictly ascending by open_time.

Numbers use a decimal point, not localized comma separators. OHLC is parsed directly from string to Decimal, must be positive and fit NUMERIC(24,10): fewer than 14 integer digits or at most 14 within range, maximum 10 fractional places (trailing zeroes do not lose information). No NaN/infinity or silent rounding. high>=open/close, low<=open/close, high>=low; volume/spread must be nonnegative when present.

Duplicate identities within a file invalidate the whole batch. Exact database duplicates are counted/skipped. Same identity with any different stored value is DATA_CONFLICT and the whole import fails, preserving original rows and provenance. Gaps are warnings; catalog observations never cross gaps.

Default limits: 20 MiB, 100,000 data rows. Configure MARKET_DATA_MAX_UPLOAD_MB and MARKET_DATA_MAX_ROWS via environment/Compose. Requests beyond the byte cap return413; invalid parsed files yield a FAILED report with zero inserted rows. Quality report details are bounded; batch counters retain aggregate counts. No raw upload is permanently retained.

## Synthetic examples — not market history

examples/market_data/synthetic_regular.csv and synthetic_otc.csv are hand-designed 30-candle fixtures. Select source SYNTHETIC_QA, broker DEMO, symbol EURUSD, market REGULAR or OTC respectively, timeframe1m. The prices are fabricated for deterministic tests and must not be interpreted as historical broker data.

The regular fixture has two continuous 15-candle blocks on separate UTC days; each block is CCCPD repeated three times. Its gap is deliberate. Length3 produces CCC→P exactly6 times across2 distinct days. The separate OTC fixture is all bearish.

## Manual acceptance

Login ADMIN → Market Data → choose metadata/file → Review import → Confirm import → COMPLETED, inserted30, one gap warning → Inspect candles.
Reimport same file → inserted0, duplicates30.
Change one close within the OHLC range → FAILED/DATA_CONFLICT; original coverage unchanged.
Cataloger → same dataset, full default coverage date range, length3 → Analyze → examined30, eligible24, gap-skipped3, CCC samples6/next P6.
Import OTC fixture under OTC → REGULAR results unchanged; OTC PPP samples24/next P24.
USER can read but cannot see import controls; direct POST returns403.

