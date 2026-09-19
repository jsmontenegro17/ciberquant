import csv
import io
from datetime import datetime
from .base import CandleData, MarketDataProvider
from ..normalization import Dataset, utc
from ..quality import decimal_value

REQUIRED = ("open_time", "close_time", "open", "high", "low", "close")
OPTIONAL = ("tick_volume", "spread")


def parse_row(row, dataset):
    if None in row or any(value is None for value in row.values()) or any(row.get(k) is None for k in REQUIRED):
        raise ValueError("Row column count does not match header")
    return CandleData(
        **dataset.model_dump(),
        open_time=utc(datetime.fromisoformat(row["open_time"].strip().replace("Z", "+00:00"))),
        close_time=utc(datetime.fromisoformat(row["close_time"].strip().replace("Z", "+00:00"))),
        **{k: decimal_value(row[k].strip()) for k in ("open", "high", "low", "close")},
        **{k: decimal_value(row[k].strip()) if row.get(k, "").strip() else None for k in OPTIONAL},
    )


def csv_reader(raw: bytes):
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8") from exc
    if "\x00" in text:
        raise ValueError("Binary content is not CSV")
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    fields = reader.fieldnames or []
    if len(set(fields)) != len(fields) or not set(REQUIRED) <= set(fields) or set(fields) - set(REQUIRED + OPTIONAL):
        raise ValueError("CSV header must contain only required OHLC/time columns and optional tick_volume/spread")
    return reader


class CSVMarketDataProvider(MarketDataProvider):
    # Trusted local utility only. The upload API never passes a client path here.
    def __init__(self, path, dataset: Dataset | None = None):
        self.path, self.dataset = path, dataset

    def get_historical_candles(self, **kwargs):
        with open(self.path, "rb") as stream:
            raw = stream.read()
        if self.dataset:
            return [parse_row(row, self.dataset) for row in csv_reader(raw)]
        # Preserve the Foundation provider's metadata-per-row local-file contract.
        rows = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        return [parse_row(row, Dataset(**{k: row.get(k, "UNSPECIFIED") for k in Dataset.model_fields})) for row in rows]

    def get_latest_candles(self, **kwargs):
        return self.get_historical_candles()[-1:]

    def stream_candles(self, **kwargs):
        yield from self.get_historical_candles()

    def get_assets(self):
        return sorted({c.symbol for c in self.get_historical_candles()})
