# REQ-008 — final QA unblock evidence

Decision date2026-09-19 America/Bogota; test execution extends into2026-09-20 UTC. Baseline7b022f963ec14d58360b05c7e88f5afa627f5384 on codex/req-008-integrated-workspace, PR7; accepted main/v0.7.0 remains2f39bdb47d8c44056d905a923d6281246ad8fb43. Human Acceptance PENDING; target1.0.0-dev; no merge/tag/release.

## IQ policy, not an upstream repair

[ADR-006](adr/ADR-006-iq-post-close-finality-fail-closed.md) records OPTION A. Historical independent probes already prove IQ_UPSTREAM_POST_CLOSE_REVISION. No further soak was run to seek a clean sequence. Deterministic tests are the authority for conflict handling. Close criterion, upstream pin and all six mathematical engines are unchanged.

Added explicit provider policy metadata and small Scanner/Workspace warnings. A persisted DATA_CONFLICT is checked before constructing/reconnecting a provider: restarting the worker cannot silently resume that subscription. Expired heartbeat cannot obscure the conflict diagnostic; Workspace reports FAILED rather than READY/STALE for that conflict. No automatic clearing endpoint exists. Tests preserve raw/event/paper counts and incremental state, prove restart latch and other-dataset/core-account isolation. Recovery requires explicit operational investigation; stronger recovery procedures remain LIVE-001.

## E2E investigation and evidence limitations

Previous push35477137971 passed7 E2E; PR35477140245 failed6/7 twice. Attempt1 points to the DRAW/CANCELLED loop's Save interaction (line69); attempt2 points to WIN/LOSS loop (line48). The original logs do not identify the exact iteration or POST lifecycle. GitHub artifacts API returned total_count0; workflow did not upload trace/screenshot. Consequently no original screenshot/trace/console/request evidence can be reconstructed or claimed inspected.

Compared workflow and fetched PR merge tree against approved HEAD: no difference in frontend/backend/workflow contents. Both use the same commands/environment, Node20.20.2, Python3.12.14, one Playwright worker and the shared temporary SQLite API/scanner fixture. PostgreSQL is a service of the backend job, not the E2E fixture. Runner host load was not measured; it is not asserted as the cause.

Unmodified local isolated session and full suite passed before the controlled reproduction. The old test waited for zero buttons named Save trade. Production TradeForm changes that name to Saving… while its mutation is still pending. Thus zero Save buttons does NOT mean the form closed. The next loop can edit the same still-open form; the previous request's onSuccess then closes it, leaving the next Save click waiting for a nonexistent form.

Temporary, subsequently removed instrumentation intercepted the real successful WIN stake20.00 response, and released it only when the old test had already selected LOSS. The real API completed with200 in27ms. Diagnostic showed Save count0, Saving count1 while LOSS was being edited. Previous WIN success then closed the form; the LOSS Save click timed out at30.1s. No LOSS POST was sent. Invalid WIN20.01 returned422. Local trace/page snapshot confirmed OPEN session,2016.80 balance,1/4 operations and WIN16.80 with no form. There was no observed SQLite busy/locked or backend5xx in this reproduction. Browser and route.fetch trace entries represent the same successful WIN, not two trades.

Only allowlisted result/stake/status/timing diagnostics were inspected. Raw local trace files are ignored and not committed/published: they can contain session cookies. Original CI step cannot be narrowed beyond its loop; controlled reproduction establishes the precise LOSS-after-valid-WIN race and reproduces the same timeout mechanism without slow API or database contention.

## Fix and regression

Register waitForResponse for POST /api/v1/trades before clicking Save; assert expected422 for invalid risk or200 for success, then await disappearance of the Record trade heading (actual form lifecycle). No sleeps, retries or timeout increase. Accepted Risk Engine, ledger, session and trade UI production logic unchanged. Deferred-mutation unit regression proves Save disappears while the form remains pending; onDone occurs only after completion.

Corrected isolated session:1 PASS; full suite:7 PASS. Frontend59 PASS; local backend204 PASS/22 skipped. The one intentional diagnostic reproduction failure is not counted as a final suite pass. PostgreSQL-only tests and Docker are final-CI gates, not local passes.

## Heartbeat analysis

Existing loop: runtime.cycle → WorkerHeartbeat merge/commit RUNNING → sleep(max(0.1, live_poll_seconds - elapsed)). In E2E poll is1s; persistence is once per cycle, approximately1s when processing fits that interval, longer otherwise. Initial RUNNING and final STOPPED unchanged. live_heartbeat_seconds=15 is the stale threshold, not persistence cadence; worker/subscription timestamps and snapshot/operations consumers retain that meaning. A stopped/crashed worker eventually exceeds15s and is not healthy.

Heartbeat was not the demonstrated cause: the race reproduces with the real POST already completed in27ms and before any LOSS POST exists. This does not prove SQLite can never contend under load. No evidence justifies changing worker cadence in this correction. PostgreSQL remains authority; no schema/cadence change. Migration007_operations remains the sole REQ-008 migration. Existing recovery/security/stale tests remain in the complete regression.

## Final gates and handoff

Both new push and PR CI must pass on the correction HEAD, including backend/PostgreSQL, frontend/E2E and Docker/worker. Before that, readiness is pending. PR7 handoff records final SHA, run IDs, job results and A–L; after green checks it may become ready for review. Human Acceptance remains PENDING independently of automated QA. No merge/tag is authorized.
