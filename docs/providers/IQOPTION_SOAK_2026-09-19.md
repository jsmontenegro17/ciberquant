# REQ-008 — sanitized local PRACTICE operational probe

Release acceptance update2026-09-19 (America/Bogota): REQ-008 DONE / Human Acceptance PASS under ADR-006 fail-closed policy. The earlier pending/blocked assessments below are historical probe evidence and are not erased or relabeled as conflict-free. See [final acceptance](../requirements/REQ-008-integrated-research-workspace.md). Orders0; immutable finality NOT GUARANTEED.

Current policy update2026-09-19: [ADR-006](../adr/ADR-006-iq-post-close-finality-fail-closed.md) adopts fail-closed by human decision. REQ-008 H now requires DATA_CONFLICT SAFELY DETECTED AND FAIL-CLOSED, not a conflict-free soak. The historical blocked assessment and all probe results below are preserved. No upstream repair/finality guarantee is claimed; Human Acceptance PENDING.

Historical overall assessment before the policy decision: BLOCKED by an observed closed-candle DATA_CONFLICT; successful later probes do not erase it. No frozen close semantics or upstream pin changed.

Historical investigation update2026-09-19: **IQ_UPSTREAM_POST_CLOSE_REVISION reproduced** independently of ScannerRuntime/DB/reconnect, including identical end/count requests. [Detailed investigation](IQOPTION_FINALITY_INVESTIGATION.md). At that time REQ-008 was BLOCKED — UPSTREAM FINALITY POLICY REQUIRED; the decision above supersedes that gate. The original uninstrumented candle/layer is still not retrospectively identifiable; the mechanism is demonstrated by new evidence, not guessed from successful retries.

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

Third attempt: BTCUSD-OP REGULAR / EURUSD-OTC, bootstrap origin22:51Z; scanner MATCH at23:12/23:13Z and controlled reconnect PASS, then FAIL `IQ_SOAK_DATA_CONFLICT`. The code can emit this from either the direct observer or the runtime failure wrapper; the retained failure does not identify which. This revision did not log the exact affected symbol/candle/fields, so attributing that original failure to either market or a particular reconnect race would be speculation. No raw overwrite or fabricated completion. At this stage root cause remained unresolved; see the later independent reproduction above.

Fourth attempt completed2026-09-19T23:17:02.081885Z: ETHUSD-OP REGULAR / EURUSD-OTC, origin22:54Z, PASS;50 observations,3 new closes each, gaps0 each, duplicates closed0/events0, stale observations0, reconnectPASS,3 OTC MATCH at23:15/16/17Z. Payout snapshots87/85, last provider clock23:17:01Z. Seven capabilities true; orders0.

Fifth attempt explicitly selected BTCUSD-OP with `--regular-symbol BTCUSD-OP`, completed2026-09-19T23:22:02.419949Z: BTCUSD-OP REGULAR / EURUSD-OTC, origin22:59Z, PASS;52 observations,3 new closes each, gaps0 each, duplicates closed0/events0, stale observations0, reconnectPASS,3 OTC MATCH at23:20/21/22Z. Payout snapshots87/85, last provider clock23:22:01Z. Seven capabilities true; orders0. The earlier conflict was not reproduced during this bounded window.

The tooling now emits only sanitized symbol/market/open-time/changed-field names if a conflict recurs, plus explicit duplicate/stale counters. Duplicate counters cover the temporary persisted OTC scanner dataset/events, not a claim of REGULAR database ingestion; direct observations cover both datasets. No payout change occurred in the successful windows; values were sampled, not invented updates.

## Acceptance blocker / decision required

REQ-008 section24 requires no DATA_CONFLICT in real soak. Three bounded successful attempts do not establish that the observed conflict is resolved. Keep PR #7 draft/BLOCKED. Further diagnosis or an explicitly authorized versioned finality/quarantine policy is required before declaring production IQ operational acceptance. Do not silently delay/rewrite candles, change frozen cq-live-data-v1, replace OTC, reseal evidence, or claim this is merely a successful rerun. The accepted v0.7.0 baseline/tag remains untouched.

## Investigation scanner probe (separate, not a fix)

Completed2026-09-19T23:46:02.510159Z; binary/PRACTICE BTCUSD-OP REGULAR + EURUSD-OTC, canonical origin23:23Z.54 cycles,3 new closes each,gaps0,OTC persisted duplicate candles/events0,stale observations0,controlled reconnectPASS,3 OTC MATCH at23:44/45/46Z,payout snapshots87/85,orders0. Local observer6372 closed observations/170 queries/0 revisions. Operational probe PASS; conflict NOT REPRODUCED in this window, **not FIXED**. Independent finality experiments immediately before it reproduced three revisions across three BTC candles; see investigation report. No semantic fix was made.
