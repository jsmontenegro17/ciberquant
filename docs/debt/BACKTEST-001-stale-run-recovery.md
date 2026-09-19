# BACKTEST-001 — Stale synchronous run recovery

Status: RESOLVED
REQ-008 implementation update (Human Acceptance PENDING): PostgreSQL lifecycle ownership and bounded explicit recovery finalize abandoned RUNNING as audited FAILED, never fabricate trades/completion. Active jobs block recovery, completed evidence remains unchanged; explicit retry is a new run.

## Historical problem and original scope


Original status: OPEN · Priority: P2 · Origin: REQ-005 · Blocking v0.5.0: NO

The synchronous service commits RUNNING and BACKTEST_STARTED before computation. Process termination or database unavailability can prevent finalization, leaving RUNNING. Trades/metrics/completion commit atomically, so unfinished work is never presented as a partial COMPLETED result. Catchable failures roll back evidence and record FAILED; failure of that recovery transaction still requires operator investigation.

Future separately authorized scope: stale detection, reconciliation, background jobs, idempotent dispatch and cancellation. No recovery implementation in REQ-005. Inspect run status and audits before rerunning; a new request creates a distinct run, not an update to prior evidence.
