# REQ-008 — Integrated Research Workspace / v1.0

Status: IMPLEMENTATION
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

A baseline/regression; B explicit Workspace/pipeline/navigation; C exact ID/version lineage; D descriptive nonpooled comparison/source differences; E safe idempotent concurrent recovery/reveal preservation; F production/development security; G operational diagnostics; H IQ PRACTICE read-only/zero orders and separate soak; I cross-user negatives; J PostgreSQL migration/locks/preservation; K all suites/build/Docker; L human QA checklist. Evidence pending: do not claim PASS before verification.

## Boundaries

No ranking/recommendations, optimization, money management, auto-trading, broker REAL, digital, ML, distributed compute, incidental quant checkpoints/dispatcher. Settings stays outside unless required; no secret UI. QUANT-001/002, BACKTEST-002, VALIDATION-002 and unrelated scale debt remain open. SEC-001/UX-001/DATA-001/BACKTEST-001/VALIDATION-001/LIVE-001 statuses must reflect actual verified scope, not blanket closure.
