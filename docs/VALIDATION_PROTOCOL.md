# cq-validation-v1

Immutable fixed-strategy historical evaluation, not optimization. Strategy lifecycle remains DRAFT/TESTING/DISABLED. Creation requires TESTING. Freeze one version/definition hash, all engine versions, full dataset identity, as-of candle ceiling, UTC overall range, payout, expiry, overlap, boundaries and canonical config hash. Unit stake only, fixed payout; no future-profit guarantee.

## Chronology and sealing

Select raw candles with overall_start <= open_time < overall_end and id <= as_of, ordered by open_time. Require at least20 candles and strictly increasing open/close times. Cuts are floor(3*N/5), floor(4*N/5). Internal boundaries are the open_time of the candle at the cut index; outer boundaries are the requested range. Require positive ranges. Four folds divide the validation candle indices at floor(k*M/4), k=0..4; endpoints exactly cover VALIDATION. Boundaries never depend on signals/trades/results. Each segment uses signal_start inclusive, signal_end exclusive and expiry <= signal_end under frozen binary-v1. No candle open at a partition end enters that segment; never use the next partition outcome.

Features retain canonical origin, never reset at folds. Development computes features only on candles open before test_start and executes TRAIN, VALIDATION and four folds. TEST segment exists without child backtest, trades, metrics or bootstrap. Explicit reveal atomically claims SEALED→RUNNING_TEST once; it cannot reseal, even on failure. Completed plans/segments/evidence cannot mutate. Failures retain visible audit/status without partial phase evidence.

## Evidence and gates

Walk-forward evaluation of a fixed strategy, not walk-forward optimization. TRAIN descriptive only. Validation and test monthly UTC signal-month summaries are descriptive, never extra gates.

Bootstrap groups executed trades (including DRAW) by UTC signal day. Resample D complete day blocks with replacement D times per iteration; compute sum(unit P&L)/sum(executed trades), preserving unequal block sizes.2000 iterations; deterministic SHA-256 counter generator seeded from config_sha256; unbiased integer rejection sampling. Sorted replicates use linear percentile interpolation at (n-1)*p for p=.025/.975. Store seed, iterations, active block count, point estimate and interval. Day blocks preserve intraday dependence but do not demonstrate interday independence. These thresholds are protocol rules, not universal statistical laws; changing them requires a new version.

First evaluate sufficiency: test >=100 resolved trades, >=10 active UTC signal days, >=3 folds with >=20 resolved trades each. Otherwise INCONCLUSIVE regardless of performance. With sufficient evidence PASS requires >=3 evaluable positive-P&L folds, validation edge>0, test edge>0, test total unit P&L>0, test bootstrap lower95>0. Otherwise FAIL. Before reveal verdict PENDING_TEST only. No manual override.

## State and research warnings

Derive per-version state from completed decisive attempts ordered by test_end, test_start, created_at, id (historical chronology, not reveal timing). Never PASS→NOT_VALIDATED due to INCONCLUSIVE. Without any PASS: NOT_VALIDATED; latest decisive PASS: HISTORICALLY_VALIDATED; later decisive FAIL after PASS: DEGRADED. Exact config replays do not count as independent evidence.

Record prior attempt count for same version/full dataset; record prior revealed holdout count, strict half-open overlapping ranges and exact-config replay count. Refresh warnings at reveal under a version lock, since another previously sealed plan may have been revealed meanwhile. REUSED HOLDOUT is not independent evidence. Scope does not detect related versions, other users or external research; future lineage debt covers that. CiberQuant cannot guarantee users never inspected raw holdout data elsewhere (no perfect blindness).
