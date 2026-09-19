from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from ..market_data.normalization import Dataset, utc
from ..strategies.dsl import number, decimal_string


class RunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy_version_id: int = Field(gt=0, strict=True)
    dataset: Dataset
    signal_start: datetime
    signal_end: datetime
    as_of_candle_id: int | None = Field(default=None, ge=0, strict=True)
    payout_percent: str
    expiry_bars: int = Field(ge=1, le=60, strict=True)
    overlap_policy: Literal["ALLOW", "SKIP_UNTIL_EXPIRY"] = "ALLOW"

    @field_validator("signal_start", "signal_end")
    @classmethod
    def aware(cls, value):
        return utc(value)

    @field_validator("payout_percent")
    @classmethod
    def payout(cls, value):
        parsed = number(value, 6)
        if not 0 < parsed <= 100:
            raise ValueError("Payout must be >0 and <=100")
        return decimal_string(parsed)

    @model_validator(mode="after")
    def range(self):
        if self.signal_end <= self.signal_start:
            raise ValueError("signal_end must be after signal_start")
        return self
