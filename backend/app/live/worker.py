"""Dedicated process: python -m app.live.worker (not an HTTP request task)."""

import time
from datetime import datetime
from decimal import Decimal
from dataclasses import asdict
from sqlalchemy import select, text
from ..db import SessionLocal, engine
from ..models import Candle, WorkerHeartbeat, now
import logging
import signal
from ..features.engine import FeatureCandle
from ..market_data.repository import dataset_conditions, candle_data
from ..config import settings
from .providers import ReplayLiveProvider
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
        from .iqoption import IQOptionReadOnlyProvider

        return IQOptionReadOnlyProvider(
            email=settings.iqoption_email.get_secret_value(),
            password=settings.iqoption_password.get_secret_value(),
            ssid=settings.iqoption_ssid.get_secret_value(),
            balance=settings.iqoption_balance,
            product=settings.iqoption_product,
            origin=datetime.fromisoformat(settings.iqoption_canonical_origin) if settings.iqoption_canonical_origin else None,
            max_history=settings.feature_engine_max_source_candles,
            timeout=settings.iqoption_timeout_seconds,
        )
    raise ConnectionError("Provider disabled")


def main():
    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    # Session-level global ownership held by one dedicated connection for process lifetime.
    with engine.connect() as lock:
        if engine.dialect.name == "postgresql" and not lock.scalar(text("SELECT pg_try_advisory_lock(707007)")):
            raise SystemExit("Scanner worker already active")
        runtime = ScannerRuntime(SessionLocal, provider_factory)
        logger = logging.getLogger('ciberquant.worker')
        def beat(status):
            with SessionLocal() as session:
                session.merge(WorkerHeartbeat(name='scanner', status=status, updated_at=now()))
                session.commit()
        logger.warning('worker_start name=scanner')
        beat('RUNNING')
        runtime.recover_pending()
        try:
            while True:
                started = time.monotonic()
                runtime.cycle()
                beat('RUNNING')
                # Replay pacing is per subscription; keep worker heartbeat/reconnect responsive.
                interval = settings.live_poll_seconds
                time.sleep(max(0.1, interval - (time.monotonic() - started)))
        except KeyboardInterrupt:
            pass
        finally:
            runtime.close()
            beat('STOPPED')
            logger.warning('worker_stop name=scanner')


if __name__ == "__main__":
    main()
