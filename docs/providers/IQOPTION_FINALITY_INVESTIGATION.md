# REQ-008 — IQ finality investigation, 2026-09-19 UTC

Current decision2026-09-19: human-approved OPTION A — FAIL CLOSED, recorded in [ADR-006](../adr/ADR-006-iq-post-close-finality-fail-closed.md). The policy blocker is resolved, not the upstream limitation. No immutable closed-candle finality guarantee; IQ remains unofficial/experimental/PRACTICE-only/read-only. Human Acceptance PENDING; no merge/tag/release. [Final QA correction](../REQ008_QA_UNBLOCK.md).

Historical investigation status at starting HEAD cd67e4b04344174c5081e7bbb956aadc1e161d3d: BLOCKED — UPSTREAM FINALITY POLICY REQUIRED, PR #7 draft. The evidence and alternatives below are preserved; their request for a policy decision is superseded by ADR-006, not erased.

## Scope and root cause

Classification: **IQ_UPSTREAM_POST_CLOSE_REVISION** for the newly reproduced conflicts. IQ `get-candles` served different OHLC for the same full identity after the current IQ server-clock CLOSED condition was met. This was reproduced without ScannerRuntime, database, bootstrap, pagination or reconnect. The internal broker cause (late tick, cache propagation, server-clock/data-pipeline skew, or correction) is not visible and is not asserted. The original uninstrumented failure's exact candle/layer cannot be reconstructed retrospectively; this investigation proves a mechanism, not its missing identity.

Do not infer that three successful prior soaks fixed anything. No stabilization delay, extra retry, overwrite, alternative price selection, engine/version change or relaxed conflict rule was applied.

## Methodology / reproducibility

Local authorized PRACTICE only, binary, pinned acac6e08333466ae188c7dfa7fd2a03174e34ca2. Explicit BTCUSD-OP REGULAR active1916 and EURUSD-OTC active76, source/brokerIQOPTION, timeframe1m. No fallback if requested asset is closed. `python -m scripts.diagnose_iq_finality --candles 3 --seconds 330`, then the same with `--reconnect`. Third experiment uses the existing full scanner soak with `--product binary --regular-symbol BTCUSD-OP --otc-symbol EURUSD-OTC --seconds 420`.

Eight target offsets +0/+1/+2/+3/+5/+10/+20/+30 seconds, driven by IQ server time. Each queries fixed `end=close_time,count=3`, progressing `end=provider_time,count=3`, and fixed `end,count=20`. Calls are sequential, not claimed simultaneous; actual clocks/receive times are retained. OTC follows REGULAR: experiment1 first sampled it at+1s; experiment2 includes an OTC sample in the floored +0 bucket. Dense sequential requests can run late (e.g. requested+2 actually+4); the table below groups ACTUAL floored decision-clock ages, not requested labels. A skipped target is explicitly MISSED_SAMPLE. No missing sample is counted as unchanged; other delayed requests can still fall in a skipped target's age bucket.

Existing production `_server_time()` truncates to seconds; diagnostic decision-clock ages retain that resolution. Experiment2 additionally records raw timeSync precision as `provider_response_time` (last received clock, not an interpolated clock). Different responses may share one cached timeSync tick; receive UTC supplies ordering, not authoritative broker time. No finality predicate was changed. Full local JSONL logs remain outside Git; [sanitized market-data evidence](evidence/iq-finality-2026-09-19.json) retains query sequences, identities, OHLC, clocks, samples and conflicts without wire/auth payloads.

## Exact conflict 1 — no reconnect

- Detection: LOCAL_HISTORY_OBSERVER; phase FINALITY_PROBE (direct get-candles); no database/scanner.
- IQOPTION / binary / IQOPTION / IQOPTION / BTCUSD-OP / REGULAR /1m / active1916.
- Open2026-09-19T23:36:00Z; close23:37:00Z.
- First query1: end1789861020,count3; provider23:37:00Z; received23:37:00.487306Z.
- Second query2: **same end1789861020,count3**; provider23:37:00Z; received23:37:00.736358Z.
- Both decision-clock ages0ms at one-second resolution; receive separation249.052ms. Both meet close_time<=provider_time.
- Old OHLC: 81364.0275 / 81366.4695 / 81361.5195 / **81364.6165**.
- New OHLC: 81364.0275 / 81366.4695 / 81361.5195 / **81364.3815**.
- Changed: close (difference0.2350, not rounding). BEFORE reconnect; no reconnect occurred in experiment1.
- Revised value remained unchanged across subsequent sampled windows through +30 and later queried overlap. This is an observed interval, not proof of permanent stability.

Conflict2 in experiment1: BTC candle23:37→23:38Z, first query49/50 end1789861080,count3 at provider23:38:00Z; query51 sameend,count20 at provider23:38:00Z revised low81345.7655→81345.0485 and close81345.8655→81345.0485. Received23:38:00.572189Z→23:38:00.818950Z. Later count3 queries agreed with revised values; count itself is not required for conflict1.

Conflict3 in experiment2: BTC candle23:41→23:42Z, post reconnect; query99→100, sameend1789861320,count3. Old OHLC81291.5605/81292.8995/81288.4855/**81291.2255**; new close**81290.5635**. Decision clocks both23:42:00Z; response clocks both23:42:00.086Z (cached timeSync, age86ms), received23:41:59.925246Z→23:42:00.165009Z. Clock/receive skew is retained, not corrected. No claim that local time measures broker finality.

## Finality characterization

REVISED means a change within that offset's samples; UNCHANGED means no new change at subsequent observed samples, **not equal to the original unrevised value**. Baseline samples without variation are marked UNCHANGED. Times below are candle open UTC2026-09-19. Stable from means only earliest observed final variant in this bounded window; future immutability unknown.

| Market | Candle open UTC | +0 | +1 | +2 | +3 | +5 | +10 | +20 | +30 | Stable from (observed only) |
|---|---|---|---|---|---|---|---|---|---|---|
| REGULAR | 23:36 | REVISED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | last revision within +0 bucket |
| OTC | 23:36 | NOT OBSERVED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | NOT OBSERVED | UNCHANGED | UNCHANGED | first sampled +1 |
| REGULAR | 23:37 | REVISED | NOT OBSERVED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | last revision within +0 bucket |
| OTC | 23:37 | NOT OBSERVED | UNCHANGED | UNCHANGED | UNCHANGED | NOT OBSERVED | NOT OBSERVED | NOT OBSERVED | UNCHANGED | first sampled +1 |
| REGULAR | 23:38 | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | NOT OBSERVED | UNCHANGED | UNCHANGED | first sampled +0 |
| OTC | 23:38 | NOT OBSERVED | UNCHANGED | UNCHANGED | UNCHANGED | NOT OBSERVED | NOT OBSERVED | UNCHANGED | UNCHANGED | first sampled +1 |
| REGULAR | 23:39 | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | first sampled +0 |
| OTC | 23:39 | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | first sampled +0 |
| REGULAR | 23:40 | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | first sampled +0 |
| OTC | 23:40 | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | NOT OBSERVED | UNCHANGED | UNCHANGED | first sampled +0 |
| REGULAR | 23:41 | REVISED | UNCHANGED | UNCHANGED | NOT OBSERVED | UNCHANGED | NOT OBSERVED | UNCHANGED | UNCHANGED | last revision within +0 bucket |
| OTC | 23:41 | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | NOT OBSERVED | UNCHANGED | UNCHANGED | first sampled +0 |

## Hypotheses H1–H9

| Hypothesis | Evidence / conclusion |
|---|---|
| H1 post-close revision | Demonstrated relative to provider CLOSED criterion, including identical end/count. |
| H2 reconnect | Not necessary: two revisions with uninterrupted connection. Experiment2 also reproduced after reconnect. |
| H3 bootstrap/poll overlap | Not necessary: direct finality experiment never bootstraps/polls. No overlap identity defect found. |
| H4 double runtime bootstrap | Soak calls extra manual bootstrap before runtime bootstrap; production initializes once per new provider/subscription. Extra reads increase exposure to revisions but cannot explain same-query revision with neither bootstrap. Deterministic repeated-bootstrap test preserves identity/history. Not established as original cause; no steps removed to pass. |
| H5 end/count semantics | First and third conflicts hold both end and count constant. Count20 control/advancing-end windows converge in sampled later responses. No end arithmetic defect found. |
| H6 identity | Explicit IDs1916/76, symbols/markets/product/timeframe retained. Per-request response correlation uses request_id; installed pinned get_candles forwards numeric active/size/to/count directly, no price cache/transformation. |
| H7 normalization | JSON parses decimal numbers into Decimal; floats rejected. normalize_candle preserves prices; >10 decimals rejected without rounding. Reproduced before any DB/Numeric conversion, differences0.2350/0.6620 not formatting. New tracker also compares Decimal values rather than display scale. |
| H8 DB lookup | Not involved in direct conflicts. existing_for filters all five axes+open_time; new SQLite/PostgreSQL tests check each identity mismatch, exact Numeric roundtrip and no overwrite. |
| H9 historical correction | Historical API returned different closed values; demonstrated feed behavior. Later aged-history corrections beyond sampled windows are NOT established. Internal broker explanation remains unknown. |

## Reconnect and stream

Experiment2 disconnected and reauthenticated after two sampled closes, at23:41:37Z. Same identities downloaded again; no already-sampled candle changed specifically on that reconnect download. A fresh candle revised at23:42 after reconnect. This does not make reconnect causal: experiment1 already refutes necessity.

Last observed forming snapshots in experiment1 matched the later historical variants for all six candles, including both revised BTC candles. They did not always match the first historical response. In experiment2, five of six matched; OTC23:41 did NOT match its later history. Forming is not a finalization message, may miss ticks, and has no demonstrated immutability guarantee. No source change applied.

Production worker reconnect: runtime abandons pending paper, closes old provider, bounded retry, new provider, one bootstrap→persist→poll; missed LIVE signals are not reconstructed. Soak additionally downloads both probe datasets and polls them directly, then runtime bootstraps OTC again. It exercises additional valid reads and an orderly restart/recover_pending, not an identical transient-retry schedule. No claim that successful soak proves all production reconnect timing paths.

## NEXT_CANDLE_OPEN causality / decision gate

For conflict1 next candle opened23:37:00Z. Revised history was received23:37:00.736358Z, i.e. after that boundary; decision-clock resolution cannot make the revised signal available beforehand. Guaranteed stable signal availability is UNKNOWN. A delayed signal cannot claim an actually observable entry at that already-past open: causal entry at NEXT_CANDLE_OPEN **NO** for such a delayed stabilization proposal. The accepted paper model is observational, not an executable quote; it must not be promoted into a causal real-time fill claim. No retroactive entry/paper rule change applied.

No safe delay can be inferred from three revisions; a +1s observation is not proof that +1s always stabilizes. Do not create v2 implicitly.

| Option | Technical impact / authorization boundary |
|---|---|
| A — Fail closed | Preserve current immutable-data conflict stop. Do not certify IQ realtime/scanner support under the demonstrated revision behavior. Historical research stays separate and requires its own consistency evidence. Existing accepted evidence is not rewritten. |
| B — Stabilization | Required delay UNKNOWN; sampled stabilization is not guaranteed finality. Positive delay adds latency and misses next-open causal entry. Requires explicit policy and potentially versioned live/scanner/paper contracts; NOT implemented. |
| C — Stronger finality source | Need a demonstrated authoritative read-only finalization message from IQ. candle-generated alone does not establish it. No such source proven here. |
| D — Quarantine | Excluding uncertain/revised candles affects continuous indicators, signals, gaps, pending paper and expiry. A revision may arrive after an event already exists; must preserve history and define invalidation/quarantine policy, not silently erase. Requires human decision/version review. |

## Instrumentation / integrity / security

DataConflictError remains a ValueError with str(exc)==DATA_CONFLICT. Allowlisted details distinguish PROVIDER_BOOTSTRAP_INTERNAL, RUNTIME_BOOTSTRAP_PERSISTENCE and RUNTIME_OBSERVED_PERSISTENCE; direct soak identifies SOAK_DIRECT_OBSERVER. Provider poll has no internal comparison; its disagreements are observed by local tracker or persistence, not falsely attributed to an internal check. Runtime logs summary and calls optional local sink before normal fail-closed cleanup; sink failure cannot bypass cleanup. No health API/schema change, DB schema change or UI changes.

Live BOOTSTRAP provenance historically stores local receive time in provider_timestamp; diagnostics explicitly label LOCAL_BOOTSTRAP_RECEIVE and leave actual provider-clock fields unknown where no direct observation exists. The probe supplies true query clock independently. Existing historical timestamps are not rewritten.

Exact duplicates remain idempotent; different duplicates remain DATA_CONFLICT; no overwrite/update/delete-reinsert. FakeTransport regression verifies changed second poll→one event only→unchanged raw candle→closed provider→latched retry conflict. Migration harness checks real PostgreSQL separately in CI. Logs/project/build are checked against configured secret values; only market-data allowlists are retained. Orders0; broker probes never run in CI.

## Individual probes and regression

1. No reconnect: start23:36:54Z, finish23:39:31.286185Z,3 closes per market,144 queries,1119 closed observations,2 revisions; REPRODUCED, not a production PASS.
2. With reconnect: start23:39:52Z, finish23:42:31.390779Z,3 closes per market,140 queries,1113 observations,1 revision; reconnectPASS, target+5s of last close missed and documented. REPRODUCED, not a production PASS.
3. Full scanner soak: completed23:46:02.510159Z,54 cycles,3 new closes per market,3 OTC MATCH (23:44/45/46),gaps0,OTC persisted duplicates candles/events0,stale observations0,reconnectPASS,payout87/85,orders0. Diagnostic tracker6372 closed observations/170 queries,0 revisions: NOT REPRODUCED in this window, operational probe PASS, not FIXED. A PASS here cannot erase the above revisions.

Local automated backend203 PASS/22 explicit skips; IQ12 PASS; IQ/live/scanner27 PASS; migrated SQLite2 PASS/2 PostgreSQL-local skips. Final PostgreSQL/Docker/worker/full CI IDs and counts are in PR #7 handoff. Existing frontend is untouched, full CI still runs frontend/E2E. No semantic fix applied. REQ-008 remains BLOCKED pending a human policy decision, not merely more successful probes.
