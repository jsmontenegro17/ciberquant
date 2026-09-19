"""Read-only boundary. No order methods, credentials or external SDK objects cross it."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from time import monotonic
from ..features.engine import FeatureCandle
from ..market_data.normalization import Dataset
from ..market_data.timeframe import duration

CAPABILITIES = dict(
    historical_candles=True, live_candles=True, forming_candle=True, assets=True, payout=False, server_time=True, market_status=True
)


@dataclass(frozen=True)
class ProviderFrame:
    server_time: datetime
    closed: tuple[FeatureCandle, ...] = ()
    forming: FeatureCandle | None = None
    payout: Decimal | None = None
    market_open: bool | None = None
    status: str = "CONNECTED"
    mode: str = "LIVE"


class LiveMarketDataProvider(Protocol):
    capabilities: dict

    def assets(self) -> list[Dataset]: ...
    def bootstrap(self, dataset: Dataset) -> list[FeatureCandle]: ...
    def poll(self, dataset: Dataset) -> ProviderFrame: ...
    def close(self) -> None: ...


@dataclass
class ReplayLiveProvider:
    candles: list[FeatureCandle]
    initial: int = 1
    payout: Decimal | None = None
    speed: str = "MAX"
    capabilities: dict = field(default_factory=lambda: {**CAPABILITIES, "payout": True, "forming_candle": False})

    def __post_init__(self):
        if not self.candles or not 1 <= self.initial <= len(self.candles) or self.speed not in ("1x", "10x", "MAX"):
            raise ValueError("Invalid replay prefix/speed")
        self.cursor = self.initial
        self.logical_time = self.candles[self.cursor - 1].close_time
        self.next_emit = monotonic()

    def assets(self):
        return [Dataset(**{k: getattr(self.candles[0], k) for k in Dataset.model_fields})]

    def bootstrap(self, dataset):
        if dataset != self.assets()[0]:
            raise ValueError("Replay dataset mismatch")
        return self.candles[: self.cursor]

    def poll(self, dataset):
        if dataset != self.assets()[0]:
            raise ValueError("Replay dataset mismatch")
        if self.cursor >= len(self.candles):
            return ProviderFrame(self.logical_time, mode="REPLAY", payout=self.payout, market_open=False)
        if monotonic() < self.next_emit:
            return ProviderFrame(self.logical_time, mode="REPLAY", payout=self.payout, market_open=True)
        c = self.candles[self.cursor]
        self.cursor += 1
        self.logical_time = c.close_time
        self.next_emit = monotonic() + (
            0 if self.speed == "MAX" else duration(dataset.timeframe).total_seconds() / (10 if self.speed == "10x" else 1)
        )
        # Do not expose the next historical candle as a forming candle: its final OHLC is future data.
        return ProviderFrame(self.logical_time, (c,), payout=self.payout, mode="REPLAY", market_open=True)

    def close(self):
        pass


class MockLiveProvider:
    capabilities = {**CAPABILITIES, "payout": True}

    def __init__(self, history, frames):
        self.history, self.frames = history, iter(frames)

    def assets(self):
        return []

    def bootstrap(self, dataset):
        return self.history

    def poll(self, dataset):
        return next(self.frames)

    def close(self):
        pass
