from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator
from ..backtesting.schemas import RunCreate
from ..market_data.normalization import Dataset


class ValidationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy_version_id: int
    dataset: Dataset
    overall_start: datetime
    overall_end: datetime
    as_of_candle_id: int | None = None
    payout_percent: str
    expiry_bars: int
    overlap_policy: str = "ALLOW"

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, values):
        if not isinstance(values, dict):
            raise ValueError("Validation plan must be a JSON object")
        data = dict(values)
        child = {k: v for k, v in data.items() if k not in ("overall_start", "overall_end")}
        child.update(signal_start=data.get("overall_start"), signal_end=data.get("overall_end"))
        normalized = RunCreate(**child).model_dump()
        normalized["overall_start"] = normalized.pop("signal_start")
        normalized["overall_end"] = normalized.pop("signal_end")
        return normalized

    def child(self, start, end, ceiling):
        values = self.model_dump(exclude={"overall_start", "overall_end"})
        return RunCreate(**{**values, "signal_start": start, "signal_end": end, "as_of_candle_id": ceiling})
