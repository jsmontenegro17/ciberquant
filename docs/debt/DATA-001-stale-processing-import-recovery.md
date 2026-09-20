# DATA-001 — Market Data Import Recovery

Status: RESOLVED
REQ-008 implementation update (Human Acceptance PASS on2026-09-19): Essential abandoned-import reconciliation implemented with PostgreSQL active lifecycle ownership, exclusive recovery and audited FAILED transition; concurrency/idempotency/active-job tests. Raw candles untouched, explicit reimport remains idempotent. Background queues are not required or introduced.

## Historical problem and original scope


Original status: BACKLOG
Priority: P2
Recorded: 2026-09-19
Origin: REQ-003 final human acceptance
Blocking v0.3.0: NO

## Problem

CSV ingestion is synchronous. Process interruption after committing provenance and before finalization may leave an import batch with status PROCESSING. The batch remains visible for investigation; operators currently investigate and may retry the exact import.

## Why this is not a release blocker

Raw candles remain protected by transactional persistence and immutable identity. Exact reimport is idempotent, and the unfinished batch is visible rather than silently reported as completed. This is operational recovery debt, not a change to accepted v0.3.0 mathematical or integrity behavior.

## Future scope

Evaluate stale batch detection, recovery/reconciliation and background ingestion under a separate requirement. Recovery must distinguish active work from abandoned batches, reconcile persisted provenance/candles/audit, preserve original data and idempotency, and expose actionable status to administrators.

## Future validation

Test interruption before/after provenance creation, during transactional insertion and around completion; concurrent processing must not be falsely marked stale. Recovery/retries must not mutate historical candles, duplicate data or claim unverified completion. Document operator procedures and any job lifecycle before deployment.

No recovery implementation, scheduler, worker or schema change is included in REQ-003 closure.
