# IQ Option — unofficial community integration / read-only

## Current v1.0 operational policy (REQ-008)

UNOFFICIAL / EXPERIMENTAL / PRACTICE-ONLY / READ-ONLY / FAIL-CLOSED. **IMMUTABLE CLOSED-CANDLE FINALITY NOT GUARANTEED.** REQ-008 subsequently demonstrated upstream post-close OHLC revisions, including identical requests. [ADR-006](../adr/ADR-006-iq-post-close-finality-fail-closed.md) records the human-approved policy: preserve first evidence, DATA_CONFLICT on different duplicate, stop affected subscription without automatic retry (including worker restart). No overwrite, second event, incremental feature continuation, new paper observation or retrospective repair. Explicit operational investigation/action is required. Existing close_time<=provider server_time stays unchanged; no stabilization guarantee. REQ-008 Human Acceptance PASS on2026-09-19 explicitly includes this operational limitation and ADR-006. Historical REQ-007 acceptance below is not rewritten.

REQ-007 includes a working real IQ provider, not an unavailable placeholder. `ENABLE_IQOPTION_EXPERIMENTAL=false` by default. **UNOFFICIAL COMMUNITY INTEGRATION — protocol may change without notice.** Human Acceptance PASS on2026-09-19; this is not an official SDK or execution system.

## Pinned dependency and isolation

Upstream: [victalejo/iqoptionapi](https://github.com/victalejo/iqoptionapi/tree/acac6e08333466ae188c7dfa7fd2a03174e34ca2), exact SHA `acac6e08333466ae188c7dfa7fd2a03174e34ca2`. Python >=3.10, tested on3.12. Install from `backend/` with `python -m pip install -r requirements-iqoption.txt`. The optional async client stays private in `app/live/iq_transport.py`, with one dedicated event loop per provider. Default Docker/Replay installations do not install this optional SDK; run the IQ worker locally with this dependency and the same PostgreSQL database as the API.

The private bridge overrides authentication error handling, socket logging, Decimal JSON decoding and bounded message size. Wire allowlist permits only authentication, heartbeat, profile/balance verification, initialization metadata, candles and candle subscriptions. There is no order API on the provider/transport; other wire requests are rejected. Per-operation timeouts are bounded. Never enable raw upstream traffic logging.

## Local configuration

Use ignored `backend/.env`, not a tracked config, browser input or database record:

```dotenv
ENABLE_IQOPTION_EXPERIMENTAL=true
IQOPTION_EMAIL=
IQOPTION_PASSWORD=
IQOPTION_BALANCE=PRACTICE
IQOPTION_PRODUCT=turbo
IQOPTION_CANONICAL_ORIGIN=2026-09-19T00:00:00Z
IQOPTION_TIMEOUT_SECONDS=15
```

Set your own available canonical history origin; the date above is only an example. Origin must be an actual candle boundary available for every subscribed dataset. Missing/incomplete origin fails closed, never silently reseeds recursive indicators. Optional `IQOPTION_SSID` is a secret session token with the same protection; it is not required with successful email/password login. A challenge/no session is a sanitized authentication failure, never bypassed.

Run `python -m app.live.worker` from `backend/`. API and worker must share configuration/database. `.env` files are excluded from Git and backend Docker build context. CI uses synthetic credentials only. Never paste credentials, cookies, profiles or balance IDs into reports.

## PRACTICE and data contract

- Authentication verifies profile and existence of type4 PRACTICE balance, selecting its ID privately. REAL is rejected; there is no REAL fallback. Candle requests are balance-independent; no account trade or balance mutation is sent.
- Asset IDs, symbols, market status and payout come from initialization metadata. No hardcoded trading asset IDs, simulated payout or MT5 substitution. REGULAR and `-OTC` remain isolated source/broker/symbol/market/timeframe identities.
- `IQOPTION_PRODUCT` selects **turbo** or **binary**, never an implicit cross-product payout. Payout is `100 - option.profit.commission` for that product and open asset. Digital is explicitly unsupported. This is observed current product payout, not a guaranteed executable quote for an arbitrary paper expiry.
- Provider `timeSync` is the clock; missing/stale (>30s)/disconnected clock fails closed. No local-clock extrapolation. Openness is refreshed from metadata at most every5s.
- OHLC uses Decimal, timestamps UTC, size/identity/quality are validated. IQ fractional `volume` is not verified tick volume, so `tick_volume` and spread remain null rather than rounded or mislabeled.
- Historical pagination preserves a fixed cutoff and exact canonical origin. Bootstrap is not emitted as LIVE. Streaming forming candles are for display only; new closed candles are confirmed through history before scanner evaluation. Raw conflicts remain immutable/fail closed.
- Capabilities start false and become true only after observation. API exposes fresh verified capabilities only from the requesting user's active subscription health; configured flag alone is not proof of connectivity.

## Verification

`python -m scripts.smoke_iqoption --product binary --seconds 150` performs real PRACTICE authentication/discovery, >=20 closed candles, forming/new closed stream evidence and an actual OTC scanner evaluation in a disposable database. No ledger changes or orders. No open OTC means BLOCKED_EXTERNAL, not PASS. REGULAR availability is reported explicitly.

[Sanitized real smoke evidence, 2026-09-19](IQOPTION_SMOKE_2026-09-19.md). Automated `tests/test_iqoption.py` uses a local fake WebSocket server and deterministic fixtures: no broker credentials/network in CI. Optional MT5 verification is separate. IQ is mandatory in REQ-007, not deferred to REQ-008.
