from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from ..config import settings
from ..market_data.normalization import Dataset, utc


class IndicatorSpec(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    type: Literal['SMA', 'EMA', 'RSI', 'ATR', 'BOLLINGER']
    period: int = Field(ge=2, le=500, strict=True)
    stddev_multiplier: Decimal | None = None

    @field_validator('stddev_multiplier', mode='before')
    @classmethod
    def decimal_input(cls, value):
        if isinstance(value, (float, bool)):
            raise ValueError('Supply multiplier as a decimal string, not a floating number')
        return value

    @model_validator(mode='after')
    def parameters(self):
        value = self.stddev_multiplier
        if self.type == 'BOLLINGER':
            if value is None:
                object.__setattr__(self, 'stddev_multiplier', Decimal('2'))
            elif not value.is_finite() or not Decimal(0) < value <= Decimal(10) or value.as_tuple().exponent < -6:
                raise ValueError('Bollinger multiplier must be >0, <=10 and have at most6 fractional places')
        elif value is not None:
            raise ValueError('stddev_multiplier applies only to BOLLINGER')
        return self


class ComputeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    dataset: Dataset
    start: datetime
    end: datetime
    as_of_candle_id: int | None = Field(default=None, ge=0, strict=True)
    include_candle_features: bool = True
    indicators: list[IndicatorSpec] = Field(default_factory=list, max_length=50)

    @field_validator('start', 'end')
    @classmethod
    def aware(cls, value): return utc(value)

    @model_validator(mode='after')
    def valid_request(self):
        if self.end <= self.start:
            raise ValueError('end must be after start')
        if len(self.indicators) > settings.feature_api_max_indicator_specs:
            raise ValueError(f'Maximum {settings.feature_api_max_indicator_specs} indicator specs')
        if len(set(self.indicators)) != len(self.indicators):
            raise ValueError('Duplicate indicator specs are not allowed')
        return self

