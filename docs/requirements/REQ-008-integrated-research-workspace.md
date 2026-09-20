# REQ-008 — Integrated Research Workspace / v1.0

Status: QA — final push/PR CI gate required before READY FOR HUMAN ACCEPTANCE
Human-approved amendment2026-09-19 (America/Bogota): OPTION A — FAIL CLOSED accepted for IQ finality, not Human Acceptance/release. Replace NO DATA_CONFLICT OBSERVED with DATA_CONFLICT SAFELY DETECTED AND FAIL-CLOSED because identical upstream requests demonstrably return revised closed OHLC. [ADR-006](../adr/ADR-006-iq-post-close-finality-fail-closed.md) records the policy; original failed evidence remains intact.
IQ_UPSTREAM_POST_CLOSE_REVISION remains a demonstrated provider limitation, not a repaired upstream bug. The policy blocker is resolved by the human decision. The independent session E2E synchronization race is reproduced and corrected; both final CI events must pass before readiness. See [QA unblock evidence](../REQ008_QA_UNBLOCK.md) and [IQ investigation](../providers/IQOPTION_FINALITY_INVESTIGATION.md).
Human Acceptance: PENDING
Target: 1.0.0-dev
Base main/tag: 2f39bdb47d8c44056d905a923d6281246ad8fb43 / v0.7.0
Branch: codex/req-008-integrated-workspace

## Baseline audit

Fetched origin/tags; main, origin/main and v0.7.0 resolve to the expected accepted commit. Worktree clean; no partial REQ-008 found. REQ-001–007 DONE/PASS. Existing modules remain authoritative. No automatic merge/tag/release; explicit later human acceptance required.

## Scope / implementation phases

1. Read-oriented owned Workspace: explicit five-axis dataset and immutable StrategyVersion selection, bounded pipeline/lineage/comparison/history, links to authoritative modules. No workspace evidence table or recomputation. Journal side-by-side, no inferred associations or financial writes. Resolve UX-001 manual/validation distinction.
2. Operational recovery for imports/manual backtests/validation phases: PostgreSQL lifecycle ownership, conservative abandoned-job reconciliation, atomic audited FAILED transitions, idempotency/concurrency. Never fabricate completion/trades or restore consumed holdout claims. Existing live recovery remains UNAVAILABLE.
3. SEC-001: validated development/test/production config, cookie/CORS/HTTPS and trusted-proxy boundary. Secrets never in frontend/DB/logs.
4. Operational health and diagnostics: version/environment/DB, owned provider subscriptions, stale heartbeat/reconnect and failure evidence; provider outage isolated from application readiness.
5. Authorized local PRACTICE-only IQ soak tooling and sanitized multi-close/reconnect evidence. Existing exact upstream pin/read-only allowlist unchanged; CI fake-only. Digital/REAL/orders forbidden.
6. Full backend/frontend/E2E/PostgreSQL/Docker regression, query/bundle review, secret scan, docs/debt evidence, independent PR and QA checklist.

## Frozen contracts

cq-features-v1, cq-strategy-dsl-v1, cq-binary-backtest-v1, cq-validation-v1, cq-live-data-v1, cq-scanner-v1: no mathematical or incompatible semantic change. Recovery is lifecycle orchestration only; any incompatibility blocks implementation. Preserve all persisted historical evidence.

## Acceptance A–L

A baseline/regression; B explicit Workspace/pipeline/navigation; C exact ID/version lineage; D descriptive nonpooled comparison/source differences; E safe idempotent concurrent recovery/reveal preservation; F production/development security; G operational diagnostics; H IQ fail-closed boundary (below); I cross-user negatives; J PostgreSQL migration/locks/preservation; K all suites/build/Docker; L human QA readiness including both final push and PR CI. Final automated evidence is recorded in the PR #7 handoff; human acceptance remains pending.

### H — human-approved fail-closed boundary

1. PRACTICE only.
2. Read-only.
3. REAL forbidden.
4. Orders sent = 0.
5. Exact source/broker/symbol/market_type/timeframe and candle identity.
6. Exact duplicates idempotent.
7. Different duplicates detected as DATA_CONFLICT.
8. No overwrite, raw UPDATE or delete/reinsert.
9. No second event from revised identity, incremental feature continuation or new paper observation.
10. Affected subscription fail-closed; persisted latch survives worker restart.
11. Other datasets and modules isolated.
12. Diagnostic visible, including after heartbeat expiry; not ACTIVE/healthy.
13. CI has no real credentials or broker access; deterministic fakes only.
14. Post-close revision limitation documented.
15. No immutable-finality claim.
16. No automatic retry/reconstruction after DATA_CONFLICT; explicit operational investigation/action required.

## Implementation and acceptance evidence

Workspace/API, pipeline/lineage, paginated histories, descriptive comparisons, manual/validation separation, PostgreSQL guarded recovery, production security validation, heartbeat/diagnostics and local-only soak tooling implemented. See [Workspace semantics and human checklist](../WORKSPACE_SEMANTICS.md), [deployment/recovery](../OPERATIONS_DEPLOYMENT.md), [all real IQ attempts](../providers/IQOPTION_SOAK_2026-09-19.md).

Correction regression: local backend204 PASS/22 explicit skips, frontend59 PASS, isolated session E2E1 PASS, full E2E7 PASS; lint/typecheck/build PASS. PostgreSQL/concurrency and Docker require final CI, not claimed as local executions. Six mathematical engines unchanged; no persisted historical evidence rewritten. PR #7 remains draft until both final CI events pass; no merge/tag.

Historical blocker: real IQ probe observed `IQ_SOAK_DATA_CONFLICT` after two closes and reconnect, without exact candle attribution. Subsequent independent investigation demonstrated upstream post-close revisions; the original missing identity cannot be reconstructed. Successful bounded probes do not erase failures. The former zero-conflict soak gate is explicitly superseded by the human-approved H amendment, not retroactively marked passed. No incompatible finality change is authorized. Orders0; no v1.0 release approval claimed.

## Boundaries

No ranking/recommendations, optimization, money management, auto-trading, broker REAL, digital, ML, distributed compute, incidental quant checkpoints/dispatcher. Settings stays outside unless required; no secret UI. QUANT-001/002, BACKTEST-002, VALIDATION-002 and unrelated scale debt remain open. SEC-001/UX-001/DATA-001/BACKTEST-001/VALIDATION-001/LIVE-001 statuses must reflect actual verified scope, not blanket closure.
