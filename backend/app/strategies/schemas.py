from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from ..features.schemas import IndicatorSpec
from ..features import FEATURE_ENGINE_VERSION
from ..config import settings
from . import STRATEGY_DSL_VERSION
from .dsl import validate_tree, decimal_string, canonical


class StrategyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)


class StrategyStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["DRAFT", "TESTING", "DISABLED"]


class VersionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy_dsl_version: Literal[STRATEGY_DSL_VERSION] = STRATEGY_DSL_VERSION
    feature_engine_version: Literal[FEATURE_ENGINE_VERSION] = FEATURE_ENGINE_VERSION
    trade_direction: Literal["CALL", "PUT"]
    indicator_specs: list[IndicatorSpec] = Field(default_factory=list, max_length=12)
    condition_tree: dict

    @model_validator(mode="after")
    def valid(self):
        if len(self.indicator_specs) > settings.feature_api_max_indicator_specs or len(set(self.indicator_specs)) != len(
            self.indicator_specs
        ):
            raise ValueError("Too many or duplicate indicator specs")
        self.condition_tree = validate_tree(self.condition_tree, self.indicator_specs)
        return self

    def snapshot(self):
        value = self.model_dump(mode="json")
        for spec in value["indicator_specs"]:
            if spec["stddev_multiplier"] is None:
                spec.pop("stddev_multiplier")
            else:
                from decimal import Decimal

                spec["stddev_multiplier"] = decimal_string(Decimal(spec["stddev_multiplier"]))
        value["indicator_specs"].sort(key=canonical)
        return value
