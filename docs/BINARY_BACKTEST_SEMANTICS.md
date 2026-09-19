# cq-binary-backtest-v1

IN-SAMPLE / NOT VALIDATED. Fixed payout assumption, not historical payout. One dataset/timeframe, unit stake1; no real capital, Risk Engine, compounding, latency, slippage or spread simulation. cq-features-v1 remains unchanged. All calculations use Decimal local precision50/HALF_EVEN; no cent quantization. Persist exact unit P&L (payout maximum6 fractional places); API derived ratios use18 fractional places.

## Events / time

Stream raw candles from snapshot origin through open_time<signal_end. Per candle: process pending entry at open; expire open trades at close; consume the current Feature Engine row and evaluate the signal at close; schedule next open. Only a bounded trailing51-row context is passed to the evaluator, never future rows. Fully formed candles are retrospective data; access to close-derived values is gated by close_time. Reject non-increasing close times within the source prefix as invalid execution chronology.

signal_time=T.close_time; candidates satisfy signal_start<=signal_time<signal_end. Entry E must have open_time=T.open_time+timeframe and open_time>=signal_time, with entry_price=E.open (not T.close). An early overlapping timestamp fails temporal entry, counted ENTRY_GAP. Remaining entry→expiry opens must be timeframe-consecutive and not precede the preceding close; otherwise EXPIRY_GAP. expiry_bars1–60 counts E as1 and uses the actual close/time of the final candle. Accept only expiry_time<=signal_end; never read a later close price to resolve an outcome. Gaps never produce fabricated trades.

Skip precedence: root UNKNOWN→unavailable; true signal while active under SKIP_UNTIL_EXPIRY→overlap; pending entry with next expected open>=signal_end→outside_range; missing next observed candle before range end→no_future_data; observed nonconsecutive/too-early entry→entry_gap. Active trade: nonconsecutive interval→expiry_gap; observed close beyond end→outside_range; end-of-source expected remaining boundary>end→outside_range, otherwise no_future_data (an absent candle potentially closing exactly at end is missing data). Every true signal is either one completed trade or one mutually exclusive skip. False root is just a candidate. Expired trades settle before the same-close signal, allowing a new signal at expiry. ALLOW permits independent overlapping trades; SKIP_UNTIL_EXPIRY skips true signals while a position is active.

## Outcomes and metrics

Compare entry_price and expiry_price only: CALL higher WIN/lower LOSS; PUT lower WIN/higher LOSS; equality DRAW regardless of candle color. WIN=payout_percent/100, LOSS=-1, DRAW=0. Payout decimal string0<P<=100;83.5 produces0.835 exactly.

Trades ordered by settlement time then signal order (fixed expiry/valid chronology preserve causal order). Unit equity starts0, accumulates settled P&L; drawdown is peak-to-trough units, not percent. DRAW breaks win/loss streaks. resolved=wins+losses; win_rate=100*wins/resolved, EV=(wins*payout_fraction-losses)/resolved; both null if no resolved trades. Break-even=100/(1+payout_fraction); edge=win_rate-break_even (percentage points), null without resolved evidence. Average P&L per executed signal=total_unit_pnl/trades_executed (draw included), null without trades. Gross profit/loss are positive magnitudes; profit_factor=null when gross loss0. Skipped signals do not enter these denominators.

## Snapshot / persistence / limits

Freeze dataset MAX(candle.id) before source queries; all source queries apply identity and id<=as_of. Compute features from canonical origin, filter candidates by close-time range only. Store immutable strategy and config snapshots/hashes including versions, full identity, ceiling, range, payout, expiry and overlap. Replays require retained raw data. RUNNING plus STARTED audit is committed first; trades, metrics, COMPLETED audit/status commit atomically. Errors roll back all trade evidence, then mark FAILED with a bounded non-sensitive summary and audit. No updates to completed runs/trades or strategy versions are exposed.

BACKTEST_MAX_SOURCE_CANDLES defaults250000; BACKTEST_MAX_TRADES defaults10000. Exceeding either fails the run, never truncates or approximates. Pagination caps100. Synchronous stale RUNNING recovery and execution realism are separate BACKTEST-001/002 debt. New incompatible semantics require a new BACKTEST_ENGINE_VERSION. REQ-006 alone will address out-of-sample/walk-forward validation.
