# ADR-006 — IQ Option post-close finality and fail-closed policy

Status: Accepted by explicit human policy decision · Date: 2026-09-19

## Context

REQ-008 demonstrated IQ_UPSTREAM_POST_CLOSE_REVISION: identical historical requests can return different OHLC after close_time<=provider server time. See IQOPTION_FINALITY_INVESTIGATION.md. The historical REQ-007/v0.7.0 acceptance remains unchanged. Guaranteed immutable finality is not established by a successful soak.

## Decision

OPTION A — FAIL CLOSED for v1.0. Same full identity/open_time and same values is idempotent; different values retain the first persisted evidence, report DATA_CONFLICT and stop the affected subscription. No overwrite, reconciliation, automatic network retry, new signals/features/paper on ambiguous history or retrospective reconstruction. Restart/pause-resume must not silently clear a persisted conflict. Recovery requires explicit operational investigation/action; no automatic clearing API is introduced.

IQ remains UNOFFICIAL / EXPERIMENTAL / PRACTICE-ONLY / READ-ONLY / FAIL-CLOSED. IMMUTABLE CLOSED-CANDLE FINALITY NOT GUARANTEED. Existing close criterion and six frozen mathematical engines unchanged. No broker orders.

Human-approved REQ-008 acceptance amendment: replace NO DATA_CONFLICT OBSERVED with DATA_CONFLICT SAFELY DETECTED AND FAIL-CLOSED. This is not Human Acceptance PASS, release approval or concealment of failed evidence.

## Rejected alternatives for v1.0

- Stabilization: safe delay unknown; delayed signal cannot claim causal entry at a past NEXT_CANDLE_OPEN; would require contract review.
- Stronger finality source: no authoritative source demonstrated.
- Quarantine: changes continuity, indicators, signals, gaps and paper expiry; requires separate policy/contracts.
- Last-write-wins/revision selection: destroys immutable evidence and is forbidden.

## Consequences

Lower availability in exchange for integrity; DATA_CONFLICT may stop an experimental IQ subscription. Other datasets/modules remain isolated. No finality guarantee or retroactive rewrite of historical releases/evidence. Stronger-finality research, prolonged soak, protocol drift, supervision and operational recovery procedures remain LIVE-001. Different future semantics require explicit authorization and separate versioned contracts.
