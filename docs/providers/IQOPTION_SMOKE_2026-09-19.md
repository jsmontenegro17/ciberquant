# REQ-007 — real IQ Option PRACTICE smoke

Result: PASS. Completed `2026-09-19T21:49:03.407515Z`, process exit0, Windows/Python3.12. Product **binary**, timeframe1m. Upstream pinned `acac6e08333466ae188c7dfa7fd2a03174e34ca2`.

Command from backend: `python -m scripts.smoke_iqoption --product binary --seconds 150`.

| Check | Observed evidence |
|---|---|
| Authentication/profile | PASS; PRACTICE verified; no account/profile identifiers retained |
| Discovery | 98 REGULAR /171 OTC;2 REGULAR /168 OTC open at observation |
| REGULAR history | BTCUSD-OP,20 closed candles; canonical origin21:28Z |
| OTC history | EURUSD-OTC,20 closed candles; canonical origin21:28Z |
| REGULAR realtime | Forming candle and new closed candle observed, PASS |
| OTC realtime | Forming candle and new closed candle observed, PASS |
| Scanner | EURUSD-OTC real close21:49Z, MATCH, modeLIVE |
| Features | Base candle features plus ema_3, existing frozen engine |
| Payout | 85.000000%, sourcePROVIDER, productbinary |
| Paper expiry | RESEARCH_ASSUMPTION; not an executable broker expiry claim |
| Capabilities | History, live, forming, assets, payout, server_time, market_status all observed true |
| Safety | orders_sent=0; temporary database ledger count0; cleanup successful |

This deliberately trivial positive-price research condition exercises the live pipeline, not a profitable strategy or recommendation. It proves connectivity/data/scanner wiring, not execution, profitability, digital support or all future sessions. Quotes/open counts are point-in-time. Credentials were read locally; none are present in this report, Git or CI.

An earlier attempt passed data checks but failed Windows temporary SQLite cleanup and exited1. It was not accepted as the final smoke; NullPool/explicit cleanup were added and the full run above repeated successfully. No real order was submitted in either attempt.

Human Acceptance: PENDING. REQ-007 remains subject to final automated CI and human review; no merge/tag/REQ-008 authorized.
