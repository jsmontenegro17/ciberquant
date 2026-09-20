# REQ-008 operations and production boundary

IQ conflict handling: [ADR-006](adr/ADR-006-iq-post-close-finality-fail-closed.md). DATA_CONFLICT is a persisted stop latch, not a recoverable network error. Restarting a worker or pause/resume does not clear it. Inspect sanitized identity/value evidence and preserve original raw/events; no overwrite, delete/reinsert or retrospective reconstruction. No automatic clearing endpoint is provided. Explicit safe operational recovery procedures remain LIVE-001; do not clear the latch merely to restore availability. Worker global RUNNING only describes process liveness, not health of a conflicted subscription.

Safeguards accepted in REQ-008 / Human Acceptance PASS on2026-09-19; actual deployment-specific TLS/firewall verification remains pending. Default Compose is **development only**, not a production template: it exposes PostgreSQL, uses development credentials and serves HTTP. Do not deploy it unchanged or claim production readiness from Docker CI.

## Production topology

Browser → HTTPS reverse proxy → private Uvicorn backend → private PostgreSQL. Serve the built frontend over HTTPS from an explicitly allowed origin. Restrict backend ingress to the proxy IP and administrative health-check network; PostgreSQL is not public. Terminate TLS at the proxy, overwrite incoming forwarding headers, and start Uvicorn with `--proxy-headers --forwarded-allow-ips=10.20.0.2` using the **actual exact private proxy address**, never `*`. Without a trusted proxy, use direct TLS or `--no-proxy-headers`. Application middleware reads ASGI scheme only, never blindly trusts request headers. HTTP is rejected before auth, not redirected with credentials.

Required environment: `ENVIRONMENT=production`, `COOKIE_SECURE=true`, `COOKIE_SAMESITE=lax` (strict also supported), `HTTPS_REQUIRED=true`, `ALLOWED_ORIGINS=["https://your-research-host"]`, a unique >=32-character JWT secret, explicit non-default seed identity/password (>=12 characters), PostgreSQL URL. Use secret injection, not committed env files/images. Never print config dumps, headers, cookie values, SSID or database URLs. Validation errors omit input values. Cross-origin production writes require an exact allowed Origin; missing Origin is rejected, including CLI writes unless explicitly supplied. SameSite none requires Secure; Origin checking remains mandatory in production.

Use identical explicit security/database settings for API and worker. Run migrations before workers, then provision administrative identity deliberately (the development Compose seed also creates demo financial data and is not a production provisioning policy). Production TLS/proxy health checks must use HTTPS or the trusted proxy path; default HTTP Docker health check is only for development. `/health` reports liveness/version/environment; `/ready` probes DB and returns sanitized503 on failure. Broker outages do not change core DB readiness.

## Ownership and recovery

No new queue or maintenance daemon. `python -m scripts.recover_jobs import|backtest|validation --minimum-age-seconds 300` from backend is an explicit privileged operator maintenance action, bounded100 rows per invocation. Keep access to DB credentials/operator host restricted. Audit is transactional: JOB_RECOVERED references original owner, entity, old/new status. Logs include only fixed event/kind/count/type codes.

In development Docker the same one-shot command is available as `docker compose exec backend python -m scripts.recover_jobs import` (or backtest/validation). It is not an HTTP request loop and needs no new service.

PostgreSQL session advisory shared locks808001/808002/808003 cover each whole synchronous lifecycle (before creating PROCESSING/RUNNING or consuming reveal, until completion/failure). The **same dedicated physical connection** owns the lock and all job transactions; a backend PID fence rejects persistence after connection replacement. Kernel/database connection loss releases ownership. Recovery tries an exclusive lock per category; any active job or competing recovery returns ACTIVE_OR_RECOVERY_BUSY, even for very old work. Age alone never establishes abandonment. This intentionally conservative category-level design can delay recovery while unrelated same-category jobs run; operators can drain traffic. Long active jobs cannot be falsely expired by TTL.

Once exclusive ownership is obtained, a bounded row-lock transaction changes only abandoned running states to existing FAILED with ABANDONED reason/completion time and audit. No synthetic trades/results, candle overwrites or completed-state recovery. Rerunning the command is idempotent; concurrent recovery cannot finalize twice. Validation RUNNING_TEST retains test_revealed_at, development evidence and consumed claim; FAILED cannot be revealed/resealed. Retry is an explicit new run, never an automatic reveal. SQLite remains a computation harness and refuses operational recovery.

**Upgrade safety:** drain/stop all pre-REQ008 API processes before enabling recovery. Older processes do not participate in lifecycle locks. Do not run mixed generations or use transaction-pooling PgBouncer for session advisory ownership. Use direct PostgreSQL or session pooling, provision connection capacity (each synchronous job uses one owned connection plus request/session overhead). Downgrading application code requires stopping maintenance first. No mathematical engine was modified.

## Migration007 and worker

007_operations adds only `worker_heartbeats(name PK, status, updated_at UTC)`. No raw/financial/research evidence is rewritten or recalculated. PostgreSQL takes ordinary short DDL locks for table creation; upgrade before starting the worker. Downgrade drops only replaceable heartbeat metadata; stop workers first. Existing006 evidence survives. Migration upgrade/downgrade has SQLite/PostgreSQL tests.

Singleton scanner ownership remains PostgreSQL lock707007. Scanner writes heartbeat per cycle and STOPPED on orderly SIGTERM/KeyboardInterrupt; an abrupt kill leaves an expiring timestamp. `/operations/status` is authenticated: global worker health, bounded owned subscription diagnostics and owned running/old-running/failure counts. Old RUNNING is a candidate, not a proven abandoned job. Provider errors/reconnect/DATA_CONFLICT have sanitized fixed-code logs; no external raw exception body. Existing interrupted-paper UNAVAILABLE semantics are unchanged.

## Local IQ operational probe

`python -m scripts.soak_iqoption --product binary --seconds 420` uses ignored local PRACTICE credentials, disposable SQLite evidence and exact pinned upstream. It requires at least3 new closes per available selected REGULAR/OTC dataset, separated forming candles, actual provider clock/payout, scanner processing and a controlled socket disconnect/reconnect with canonical bootstrap. No missed history is fabricated as LIVE. Maximum900s; CI never runs this command. Retain failed attempts and sanitized reports; a short multi-close probe is not a guarantee of prolonged reliability or future protocol compatibility.

P2: unofficial IQ protocol, longer soak/deployment monitoring, digital unsupported, optional MT5 smoke unperformed, distributed scale and broader exchange calendars remain outside this implementation.
