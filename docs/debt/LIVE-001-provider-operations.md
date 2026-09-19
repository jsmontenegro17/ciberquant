# LIVE-001 — Provider operations and recovery

Status: PARTIAL
Investigation2026-09-19: IQ_UPSTREAM_POST_CLOSE_REVISION demonstrated without DB/scanner/reconnect; identical history parameters can return changed closed OHLC. Current fail-closed rule is preserved. REQ-008 blocked pending human finality-policy decision; no silent stabilization or NEXT_CANDLE_OPEN change. See [evidence and options](../providers/IQOPTION_FINALITY_INVESTIGATION.md).
REQ-008 implementation update (Human Acceptance PENDING): Worker heartbeat/stale state, bounded owned subscription diagnostics, fixed-code logging, controlled real PRACTICE multi-close/reconnect probe implemented. Observed real closed-candle DATA_CONFLICT blocks REQ-008 acceptance despite three other bounded successful probes; root cause unresolved. Prolonged soak, unknown first probe interruption, unofficial protocol drift, digital unsupported, optional MT5 real verification and larger-scale operations remain open. See dated REQ-008 soak report.

## Historical problem and original scope


Priority: P2. Separate from REQ-007 automated acceptance.

Accepted nonblocking debt for v0.7.0. IQ protocol is unofficial; the pinned SHA cannot guarantee future external compatibility. Operational monitoring and a new real PRACTICE smoke are required after relevant provider/upstream changes. Prolonged live soak tests remain pending; digital remains unsupported. Optional real MT5 smoke remains unperformed and does not block this accepted release.

- Real terminal smoke requires a configured Windows MT5 terminal; automated fake-SDK checks are not broker connectivity evidence.
- IQ Option real PRACTICE/OTC integration is implemented and locally smoke-verified in REQ-007. Future debt: unofficial protocol drift, digital product support, deployment supervision and longer soak testing. Never silently substitute MT5. See the dated IQ smoke report; mandatory IQ integration is not deferred.
- Single worker, synchronous provider interface: IQ has bounded asynchronous transport calls; isolated subprocess supervision for other SDKs, distributed sidecars, richer exchange calendars and versioned restart checkpoints remain future operations work.
- Canonical histories are bounded by the existing source cap; at cap the subscription fails closed instead of silently truncating recursive state. Versioned checkpoints remain QUANT-001.
- Interrupted paper observations become UNAVAILABLE on recovery; no retrospective reconstructed LIVE fills. Conflict subscriptions require operator investigation and worker restart, never raw candle overwrite.
- Event retention, watchlist pagination beyond100 in UI, and large-scale SSE fanout are future capacity work. Backend watchlists/items/events are paginated; UI items/events and dataset/strategy/version selectors are paginated.

REQ-008 separately resolves essential SEC-001/DATA-001/BACKTEST-001/VALIDATION-001/UX-001 implementation; acceptance is pending. QUANT-001/002, BACKTEST-002, VALIDATION-002 and dependency/bundle warnings remain open. No automatic trading is permitted.
