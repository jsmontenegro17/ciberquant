# cq-scanner-v1

IQ event evidence includes `payout_product` (turbo/binary) alongside observed payout/source and provider health. No digital-to-binary substitution. Product payout is an observed metadata snapshot, not a guaranteed executable quote for the paper expiry. PRACTICE/read-only unofficial-provider warnings remain visible; paper configuration precedence below is unchanged.

Evaluate frozen cq-strategy-dsl-v1 only on closed cq-features-v1 rows with available_at=close_time. Persistent generator preserves exact recursive state and trailing51 rows for bars_ago. Never recompute the full prefix per polling cycle. MATCH means conditions TRUE, not CALL/PUT now; direction is research metadata. Expected entry model NEXT_CANDLE_OPEN; boundary known, future entry price unknown.

Normal items require owned TESTING StrategyVersion and HISTORICALLY_VALIDATED state both globally and for the exact dataset. A PASS on another broker/source/market/timeframe is not compatible. Explicit research mode permits nonvalidated research with visible badges; DEGRADED suspends normal scanning immediately on each worker cycle. Live payout and validation assumption remain separate; lower live payout warns, never mutates historical evidence. Missing live payout remains unknown, not an invented provider quote.

## Paper configuration precedence (final human QA correction)

The pure `resolve_paper_config` helper freezes these unreleased cq-scanner-v1 rules:

| Mode | Paper payout | Payout source without provider quote | Expiry / source |
|---|---|---|---|
| Normal | Current provider payout, else compatible validation payout | VALIDATION_ASSUMPTION | Compatible validation expiry / VALIDATION_ASSUMPTION |
| Research | Current provider payout, else explicit research_payout | RESEARCH_ASSUMPTION | Explicit research_expiry / RESEARCH_ASSUMPTION |

A present provider payout always has source PROVIDER. Research mode never silently substitutes historical payout/expiry for its explicit inputs, even when the version has compatible historical PASS. Missing assumptions never fall back to the other mode. Historical payout/expiry remain separately labelled reference metadata; a research fallback is explicitly shown as not used when provider payout is active.

Immutable event evidence includes `payout_snapshot`, `payout_source`, `expiry_bars`, `expiry_source`, separate `validation_payout`/`validation_expiry` and research inputs. PaperObservation receives exactly the resolved payout/expiry; next-open, consecutive expiry and Decimal binary resolver are unchanged. Existing immutable events are not rewritten. No engine version bump: this corrects the intended unreleased v1 implementation, not its quant mathematics.

Each newly closed candle is a unique evaluation; MATCH per new signal candle may be persisted even after another MATCH, preserving exact signal equivalence. Duplicate polling cannot create another event. Bootstrap/reconnect history never creates retroactive LIVE MATCH. Events/outcomes are immutable, private and uniquely keyed by item/version/signal_time/state. No financial Trade, account, ledger or session writes.

Paper observations use frozen binary resolver, actual next candle open and actual consecutive expiry close; never candle colour or predicted entry. Resolve only after the corresponding data have occurred. Missing entry/expiry, discontinuity or worker restart yields unavailable/gap evidence, never fabricated fills. Paper is LIVE PAPER OBSERVATION (or REPLAY PAPER OBSERVATION), not BacktestTrade, and does not claim an executable broker quote at processing time. BACKTEST-002 still applies.
