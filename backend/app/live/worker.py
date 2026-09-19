"""Dedicated process: python -m app.live.worker (not an HTTP request task)."""

import time
from datetime import datetime
from decimal import Decimal
from dataclasses import asdict
from sqlalchemy import select, text
from ..db import SessionLocal, engine
from ..models import Candle
from ..features.engine import FeatureCandle
from ..market_data.repository import dataset_conditions, candle_data
from ..config import settings
from .providers import ReplayLiveProvider, IQOptionReadOnlyProvider
from .runtime import ScannerRuntime


def provider_factory(session, name, dataset):
    if name == "REPLAY" and settings.enable_replay_provider:
        candles = list(
            session.scalars(
                select(Candle)
                .where(*dataset_conditions(dataset))
                .order_by(Candle.open_time)
                .limit(settings.feature_engine_max_source_candles + 1)
            )
        )
        if len(candles) > settings.feature_engine_max_source_candles:
            raise ValueError("Replay source cap exceeded")
        return ReplayLiveProvider(
            [FeatureCandle(**asdict(candle_data(c)), candle_id=c.id) for c in candles],
            settings.replay_prefix_candles,
            Decimal(settings.replay_payout) if settings.replay_payout else None,
            settings.replay_speed,
        )
    if name == "MT5" and settings.enable_mt5_provider and settings.mt5_canonical_origin:
        from .mt5 import MetaTrader5Provider

        return MetaTrader5Provider(settings.mt5_broker, datetime.fromisoformat(settings.mt5_canonical_origin))
    if name == "IQOPTION" and settings.enable_iqoption_experimental:
        return IQOptionReadOnlyProvider()
    raise ConnectionError("Provider disabled")


def main():
    # Session-level global ownership held by one dedicated connection for process lifetime.
    with engine.connect() as lock:
        if engine.dialect.name == "postgresql" and not lock.scalar(text("SELECT pg_try_advisory_lock(707007)")):
            raise SystemExit("Scanner worker already active")
        runtime = ScannerRuntime(SessionLocal, provider_factory)
        runtime.recover_pending()
        try:
            while True:
                started = time.monotonic()
                runtime.cycle()
                # Replay pacing is per subscription; keep worker heartbeat/reconnect responsive.
                interval = settings.live_poll_seconds
                time.sleep(max(0.1, interval - (time.monotonic() - started)))
        except KeyboardInterrupt:
            pass
        finally:
            runtime.close()


if __name__ == "__main__":
    main()
