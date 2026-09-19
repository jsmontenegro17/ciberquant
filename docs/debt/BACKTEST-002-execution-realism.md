# BACKTEST-002 — Execution realism / payout history

Status: OPEN · Priority: P2 · Origin: REQ-005 · Blocking v0.5.0: NO

cq-binary-backtest-v1 assumes fixed payout, unit stake and entry at the next consecutive candle open. It does not model historical payout, latency, slippage, spread effects or ticks. Historical in-sample metrics are conditional on these assumptions, not evidence of executable future profit.

Future work requires separate data provenance, execution contracts, versioning and deterministic fixtures. Do not retrofit new economics or temporal semantics into existing immutable runs. No implementation in REQ-005.
