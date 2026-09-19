# LIVE-001 — Provider operations and recovery

Priority: P2. Separate from REQ-007 automated acceptance.

- Real terminal smoke requires a configured Windows MT5 terminal; automated fake-SDK checks are not broker connectivity evidence.
- IQ Option external transport remains EXPERIMENTAL / DISABLED. Actual IQ OTC is a conditional v1.0 blocker if required; resolve in independently authorized REQ-008 scope, never silently substitute MT5.
- Single worker, synchronous provider reads: per-call SDK timeouts/isolated subprocess supervision, distributed sidecars, richer exchange calendars and versioned restart checkpoints remain future operations work.
- Canonical histories are bounded by the existing source cap; at cap the subscription fails closed instead of silently truncating recursive state. Versioned checkpoints remain QUANT-001.
- Interrupted paper observations become UNAVAILABLE on recovery; no retrospective reconstructed LIVE fills. Conflict subscriptions require operator investigation and worker restart, never raw candle overwrite.
- Event retention, watchlist pagination beyond100 in UI, and large-scale SSE fanout are future capacity work. Backend watchlists/items/events are paginated; UI items/events and dataset/strategy/version selectors are paginated.

Existing SEC-001, DATA-001, QUANT/BACKTEST/VALIDATION debts and dependency/bundle warnings are unchanged. No automatic trading is permitted.
