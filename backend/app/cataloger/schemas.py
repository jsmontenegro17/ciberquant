from datetime import datetime
from pydantic import Field, field_validator, model_validator
from ..market_data.normalization import Dataset, utc


class CandleQuery(Dataset):
    start: datetime
    end: datetime
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0, le=10000000)

    @field_validator("start", "end")
    @classmethod
    def aware(cls, value):
        return utc(value)

    @model_validator(mode="after")
    def range_order(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self

    def dataset(self):
        return Dataset(**self.model_dump(include=set(Dataset.model_fields)))


class CatalogQuery(CandleQuery):
    pattern_length: int = Field(default=3, ge=2, le=5)
    include_doji: bool = True
