"""Explicit local-only PRACTICE diagnostic. No scanner, DB, order API or finality policy."""

import argparse
import re
import time
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.live.iqoption import IQOptionReadOnlyProvider, normalize_candle
from .iq_diagnostics import HistoryTracker, emit

OFFSETS = (0, 1, 2, 3, 5, 10, 20, 30)


def make_provider(tracker, product):
    return IQOptionReadOnlyProvider(
        email=settings.iqoption_email.get_secret_value(),
        password=settings.iqoption_password.get_secret_value(),
        ssid=settings.iqoption_ssid.get_secret_value(),
        balance="PRACTICE",
        product=product,
        timeout=settings.iqoption_timeout_seconds,
        history_observer=tracker.observe,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--regular-symbol", default="BTCUSD-OP")
    parser.add_argument("--otc-symbol", default="EURUSD-OTC")
    parser.add_argument("--product", choices=["binary", "turbo"], default="binary")
    parser.add_argument("--candles", type=int, default=3)
    parser.add_argument("--seconds", type=int, default=330)
    parser.add_argument("--reconnect", action="store_true")
    args = parser.parse_args()
    if not 2 <= args.candles <= 5 or not 180 <= args.seconds <= 600:
        raise SystemExit("Invalid bounded diagnostic duration/count")
    if not settings.enable_iqoption_experimental or settings.iqoption_balance != "PRACTICE":
        raise SystemExit("Explicit PRACTICE enable required")
    tracker, provider = HistoryTracker(), None
    try:
        provider = make_provider(tracker, args.product)
        datasets = []
        for market, symbol in [("REGULAR", args.regular_symbol), ("OTC", args.otc_symbol)]:
            asset = next((a for a in provider.asset_status() if a["symbol"] == symbol and a["market_type"] == market and a["open"]), None)
            if asset is None:
                raise ValueError("IQ_EXPLICIT_ASSET_NOT_OPEN")
            dataset = next(d for d in provider.assets() if d.symbol == symbol and d.market_type == market)
            datasets.append(dataset)
            provider._call(provider._transport.start_stream(asset["active_id"], 60))
            emit(dict(stage="DATASET", **dataset.model_dump(), active_id=asset["active_id"], product=args.product))
        clock = provider._server_time()
        first_close = clock.replace(second=0, microsecond=0) + timedelta(minutes=1)
        closes = [first_close + timedelta(minutes=i) for i in range(args.candles)]
        done, last_stream = set(), {}
        deadline = time.monotonic() + args.seconds
        emit(dict(stage="START", provider_clock=clock, closes=closes, reconnect=args.reconnect, orders_sent=0))
        while time.monotonic() < deadline:
            clock = provider._server_time()
            for dataset in datasets:
                asset = provider._asset(dataset)

                async def latest():
                    return provider._transport.latest(asset["active_id"], 60)

                raw = provider._call(latest())
                if raw is not None:
                    c = normalize_candle(raw, dataset, asset["active_id"])
                    if c.open_time <= clock < c.close_time:
                        last_stream[(dataset, c.open_time)] = dict(
                            provider_time=clock,
                            received_time=datetime.now(timezone.utc),
                            ohlc={k: str(getattr(c, k)) for k in ("open", "high", "low", "close")},
                        )
            for close in closes:
                for offset in OFFSETS:
                    key = (close, offset)
                    if key in done or clock < close + timedelta(seconds=offset):
                        continue
                    # Missing timing is explicit; never label a late sample as +0.
                    if clock > close + timedelta(seconds=offset + 2):
                        emit(dict(stage="MISSED_SAMPLE", close_time=close, requested_offset=offset, provider_time=clock))
                        done.add(key)
                        continue
                    for dataset in datasets:
                        asset = provider._asset(dataset)
                        target = close - timedelta(minutes=1)
                        for kind, count in [("FIXED_END", 3), ("PROGRESSING_END", 3), ("FIXED_END_COUNT20", 20)]:
                            now = provider._server_time()
                            end = int(close.timestamp()) if kind.startswith("FIXED") else int(now.timestamp())
                            tracker.label = dict(offset=offset, window=kind)
                            before = len(tracker.snapshots(dataset, target))
                            provider._history(dataset, asset, 60, count, end, now, "FINALITY_PROBE")
                            samples = tracker.snapshots(dataset, target)
                            sample = samples[-1] if len(samples) > before else None
                            emit(
                                dict(
                                    stage="SAMPLE",
                                    requested_offset=offset,
                                    window=kind,
                                    sample=sample,
                                    target_open=target,
                                    symbol=dataset.symbol,
                                    market_type=dataset.market_type,
                                    stream_forming=last_stream.get((dataset, target)) if offset == 0 else None,
                                )
                            )
                    done.add(key)
            if args.reconnect and tracker.generation == 0 and (closes[1], 30) in done:
                provider.close()
                tracker.generation = 1
                provider = make_provider(tracker, args.product)
                for dataset in datasets:
                    asset = provider._asset(dataset)
                    provider._call(provider._transport.start_stream(asset["active_id"], 60))
                    now = provider._server_time()
                    tracker.label = dict(window="RECONNECT_HISTORY")
                    provider._history(dataset, asset, 60, 20, int(now.timestamp()), now, "RECONNECT_HISTORY")
                emit(dict(stage="RECONNECT", result="PASS", provider_time=now, orders_sent=0))
            if len(done) == len(closes) * len(OFFSETS):
                break
            time.sleep(0.15)
        emit(dict(stage="COMPLETION", scheduled=len(closes) * len(OFFSETS), handled=len(done), orders_sent=0))
        tracker.report()
        return 0 if len(done) == len(closes) * len(OFFSETS) else 2
    except Exception as exc:
        code = str(exc) if re.fullmatch(r"IQ_[A-Z0-9_]{1,80}", str(exc)) else "IQ_DIAGNOSTIC_FAILED"
        emit(dict(stage="FAILURE", code=code, exception_type=type(exc).__name__, orders_sent=0))
        tracker.report()
        return 1
    finally:
        if provider is not None:
            provider.close()


if __name__ == "__main__":
    raise SystemExit(main())
