# LIVE-001 — Provider operations and recovery

Status: PARTIAL
Decision2026-09-19: IQ_UPSTREAM_POST_CLOSE_REVISION is a demonstrated upstream limitation, not an unresolved application bug. [ADR-006](../adr/ADR-006-iq-post-close-finality-fail-closed.md) adopts human-approved fail-closed: preserve first evidence, no automatic retry, no immutable-finality guarantee. Policy blocker resolved; REQ-008 Human Acceptance PASS on2026-09-19. See [evidence](../providers/IQOPTION_FINALITY_INVESTIGATION.md).
REQ-008 implements worker heartbeat/stale state, bounded owned diagnostics, fixed-code logging, PRACTICE multi-close/reconnect evidence and durable conflict latch/UI warning. LIVE-001 remains PARTIAL: stronger finality research, prolonged soak, unofficial protocol drift, supervision, explicit operational recovery procedures, digital unsupported, optional MT5 real verification and larger-scale operations remain future work. Unknown first probe interruption/identity remains an evidence limitation; later evidence must not invent it.

## Historical problem and original scope


Priority: P2. Separate from REQ-007 automated acceptance.

Accepted nonblocking debt for v0.7.0. IQ protocol is unofficial; the pinned SHA cannot guarantee future external compatibility. Operational monitoring and a new real PRACTICE smoke are required after relevant provider/upstream changes. Prolonged live soak tests remain pending; digital remains unsupported. Optional real MT5 smoke remains unperformed and does not block this accepted release.

- Real terminal smoke requires a configured Windows MT5 terminal; automated fake-SDK checks are not broker connectivity evidence.
- IQ Option real PRACTICE/OTC integration is implemented and locally smoke-verified in REQ-007. Future debt: unofficial protocol drift, digital product support, deployment supervision and longer soak testing. Never silently substitute MT5. See the dated IQ smoke report; mandatory IQ integration is not deferred.
- Single worker, synchronous provider interface: IQ has bounded asynchronous transport calls; isolated subprocess supervision for other SDKs, distributed sidecars, richer exchange calendars and versioned restart checkpoints remain future operations work.
- Canonical histories are bounded by the existing source cap; at cap the subscription fails closed instead of silently truncating recursive state. Versioned checkpoints remain QUANT-001.
- Interrupted paper observations become UNAVAILABLE on recovery; no retrospective reconstructed LIVE fills. Conflict subscriptions require explicit operational investigation/action, never raw candle overwrite. Worker restart alone does not clear the persisted conflict latch.
- Event retention, watchlist pagination beyond100 in UI, and large-scale SSE fanout are future capacity work. Backend watchlists/items/events are paginated; UI items/events and dataset/strategy/version selectors are paginated.

REQ-008 separately resolves essential SEC-001/DATA-001/BACKTEST-001/VALIDATION-001/UX-001 implementation; acceptance is PASS on2026-09-19. QUANT-001/002, BACKTEST-002, VALIDATION-002 and dependency/bundle warnings remain open. No automatic trading is permitted.
