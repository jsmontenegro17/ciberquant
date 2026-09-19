# VALIDATION-001 — Stale Validation Run Recovery

Status: RESOLVED
REQ-008 implementation update (Human Acceptance PENDING): PostgreSQL guarded recovery permits only abandoned RUNNING_DEVELOPMENT/RUNNING_TEST to FAILED. Consumed reveal timestamp and prior development evidence survive; FAILED cannot reveal/reseal. CI regression verifies irreversible claims. No protocol/math changes.

## Historical problem and original scope


Original status: OPEN
Priority: P2
Origin: REQ-006
Blocking v0.6.0: NO

Synchronous development/reveal claims are committed before computation. Process interruption may leave RUNNING_DEVELOPMENT or RUNNING_TEST. Each phase commits child runs/trades/summary atomically; raw candles and completed evidence remain protected. A reveal claim permanently consumes the sealed state, even when computation fails. Do not silently reseal or rerun.

Future authorized scope: stale detection, reconciliation, idempotent jobs/background computation, operator investigation and client timeout recovery with durable request identifiers. No Celery/Redis in REQ-006. A client timeout does not prove the server failed; inspect history before creating another attempt. Existing source/trade caps reject rather than approximate.
