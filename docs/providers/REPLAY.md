# Replay / Mock providers

Replay is development/test only, disabled by default (`ENABLE_REPLAY_PROVIDER=false`). It reads one exact stored dataset, loads a canonical prefix (`REPLAY_PREFIX_CANDLES`, default100), and emits subsequent closed candles individually. `REPLAY_SPEED=1x|10x|MAX` changes wall-clock pacing only; logical candle timestamps stay unchanged. Each dataset has independent pacing; health/reconnect polling stays responsive. Optional `REPLAY_PAYOUT` is a synthetic provider assumption, never a real broker quote.

Start after migrations using `python -m app.live.worker` from backend, or `docker compose --profile scanner up --build`. Set the flag in both API and worker environments. Create watchlist/item through `/scanner`; an enabled item subscribes the dataset and starts replay. Normal mode needs an owned TESTING version with exact-dataset historical PASS; the research filter explicitly allows other versions with paper payout/expiry inputs. Disabled/draft strategies do not evaluate.

Replay never emits historical final OHLC as a fake forming candle. Prefix candles are BOOTSTRAP provenance only. Replayed events and paper outcomes are labelled REPLAY, never live broker evidence. End-of-source is UNAVAILABLE (closed feed); the final unresolved paper observation awaits future data/recovery rather than inventing a fill. Event identity prevents duplicates after replay restart.

Mock supplies controlled closed/forming/status/payout frames for tests. CI uses deterministic fixtures and a separate Replay worker process in browser QA; it never needs broker accounts or the internet for feed data.
