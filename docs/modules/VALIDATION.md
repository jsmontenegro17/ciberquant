# Validation
Purpose: statistical validation beyond in-sample backtests. Status: planned. Required evidence includes OOS, walk-forward, sample size, temporal stability and paper/live behavior.

REQ-005 produces IN-SAMPLE / NOT VALIDATED historical results under a fixed payout and next-open execution assumption. A positive result does not promote a strategy to VALIDATED or imply future profitability. REQ-006 (not started) will own train/validation/test, OOS, walk-forward, temporal stability and degradation. It must preserve dataset/as-of/engine/definition/config snapshots and enforce close-time availability and fully-resolved range boundaries defined in BINARY_BACKTEST_SEMANTICS.md.
