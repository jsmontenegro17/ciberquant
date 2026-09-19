from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, field_validator
from .timeframe import normalize_timeframe


def utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timezone-aware timestamp required")
    return value.astimezone(timezone.utc)


def stored_utc(value: datetime) -> datetime:
    # SQLite test harness drops timezone; PostgreSQL returns aware timestamptz.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else utc(value)


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source: str
    broker: str = "UNSPECIFIED"
    symbol: str
    market_type: str
    timeframe: str

    @field_validator("source", "broker", "symbol", "market_type")
    @classmethod
    def normalize(cls, value, info):
        value = value.strip().upper()
        if info.field_name == "broker" and not value:
            value = "UNSPECIFIED"
        maximum = 120 if info.field_name == "broker" else 50
        if not value or len(value) > maximum or any(ord(c) < 32 for c in value):
            raise ValueError("Invalid dataset label")
        if info.field_name == "market_type" and value not in ("REGULAR", "OTC"):
            raise ValueError("market_type must be REGULAR or OTC")
        return value

    @field_validator("timeframe")
    @classmethod
    def timeframe_value(cls, value):
        return normalize_timeframe(value)


def identity(candle):
    return tuple(getattr(candle, k) for k in Dataset.model_fields)
