# REQ-008 — sanitized local PRACTICE operational probe

Overall acceptance: BLOCKED by an observed closed-candle DATA_CONFLICT; successful later probes do not erase it. No frozen close semantics or upstream pin changed. Human Acceptance PENDING.

Second attempt: PASS (bounded multi-close/reconnect probe), completed2026-09-19T23:06:01.540028Z, exit0. Productbinary. Pin acac6e08333466ae188c7dfa7fd2a03174e34ca2 unchanged. Command: `python -m scripts.soak_iqoption --product binary --seconds 420`.

- Auth/profile PRACTICE PASS;98 REGULAR/171 OTC discovered,2/168 open.
- BTCUSD-OP REGULAR and EURUSD-OTC:20 closed1m bootstrap candles each; canonical origin22:43Z.
- 51 polling observations,3 new closed candles per dataset, gaps0 for each, forming observed separately.
- Controlled disconnect/reauth/bootstrap PASS. New real OTC scanner closes23:04/23:05/23:06Z each produced MATCH; count3. Real payout85%, sourcePROVIDER, research expiry sourceRESEARCH_ASSUMPTION.
- No DATA_CONFLICT in successful probe. Existing unique raw/event identities guard persistence; repeated history observations are checked for changed OHLC. No duplicate-event exception occurred. Long-run duplicate/stale behavior also has deterministic regressions; this report does not invent an independently logged duplicate counter.
- All seven provider capabilities observed true. Orders0; disposable ledger remains empty. No credentials/SSID/profile/account IDs retained.

Earlier attempt (ETHUSD-OP + EURUSD-OTC, origin22:39Z) reconnected and observed23:00/23:01Z MATCH but endedFAIL when the test attempted to reuse a provider the runtime had closed. It is not counted as PASS. Diagnostic guards were added so a closed provider now produces a sanitized explicit failure rather than unawaited-coroutine warnings. The underlying first interruption was not conclusively classified; operational reliability remains a documented P2, not hidden by the repeated PASS.

This is several real M1 closes, not hours of unattended soak or production certification. Stale-clock/dedup/conflict/no-reconstructed-LIVE semantics retain fake/deterministic coverage. Longer live soak and deployed TLS/network validation remain operational follow-up. Human Acceptance PENDING; no order or trading recommendation.

## Additional attempts (all PRACTICE, read-only, orders 0)

Third attempt: BTCUSD-OP REGULAR / EURUSD-OTC, bootstrap origin22:51Z; scanner MATCH at23:12/23:13Z and controlled reconnect PASS, then FAIL `IQ_SOAK_DATA_CONFLICT`. The probe observed different OHLC for an already seen closed identity and stopped. This revision did not log the exact affected symbol/candle/fields, so attributing it to either market or to a particular reconnect race would be speculation. No raw overwrite or fabricated completion. Root cause remains unresolved.

Fourth attempt completed2026-09-19T23:17:02.081885Z: ETHUSD-OP REGULAR / EURUSD-OTC, origin22:54Z, PASS;50 observations,3 new closes each, gaps0 each, duplicates closed0/events0, stale observations0, reconnectPASS,3 OTC MATCH at23:15/16/17Z. Payout snapshots87/85, last provider clock23:17:01Z. Seven capabilities true; orders0.

Fifth attempt explicitly selected BTCUSD-OP with `--regular-symbol BTCUSD-OP`, completed2026-09-19T23:22:02.419949Z: BTCUSD-OP REGULAR / EURUSD-OTC, origin22:59Z, PASS;52 observations,3 new closes each, gaps0 each, duplicates closed0/events0, stale observations0, reconnectPASS,3 OTC MATCH at23:20/21/22Z. Payout snapshots87/85, last provider clock23:22:01Z. Seven capabilities true; orders0. The earlier conflict was not reproduced during this bounded window.

The tooling now emits only sanitized symbol/market/open-time/changed-field names if a conflict recurs, plus explicit duplicate/stale counters. Duplicate counters cover the temporary persisted OTC scanner dataset/events, not a claim of REGULAR database ingestion; direct observations cover both datasets. No payout change occurred in the successful windows; values were sampled, not invented updates.

## Acceptance blocker / decision required

REQ-008 section24 requires no DATA_CONFLICT in real soak. Three bounded successful attempts do not establish that the observed conflict is resolved. Keep PR #7 draft/BLOCKED. Further diagnosis or an explicitly authorized versioned finality/quarantine policy is required before declaring production IQ operational acceptance. Do not silently delay/rewrite candles, change frozen cq-live-data-v1, replace OTC, reseal evidence, or claim this is merely a successful rerun. The accepted v0.7.0 baseline/tag remains untouched.
