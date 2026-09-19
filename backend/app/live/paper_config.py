"""Pure precedence for the unreleased cq-scanner-v1 paper configuration."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

AssumptionSource = Literal["VALIDATION_ASSUMPTION", "RESEARCH_ASSUMPTION"]


@dataclass(frozen=True)
class PaperConfig:
    payout: Decimal | None
    payout_source: Literal["PROVIDER", "VALIDATION_ASSUMPTION", "RESEARCH_ASSUMPTION"]
    expiry_bars: int | None
    expiry_source: AssumptionSource


def resolve_paper_config(
    *,
    research_mode: bool,
    provider_payout: Decimal | None,
    validation_payout: Decimal | None,
    validation_expiry: int | None,
    research_payout: Decimal | None,
    research_expiry: int | None,
) -> PaperConfig:
    source: AssumptionSource = "RESEARCH_ASSUMPTION" if research_mode else "VALIDATION_ASSUMPTION"
    fallback = research_payout if research_mode else validation_payout
    expiry = research_expiry if research_mode else validation_expiry
    return PaperConfig(
        payout=provider_payout if provider_payout is not None else fallback,
        payout_source="PROVIDER" if provider_payout is not None else source,
        expiry_bars=expiry,
        expiry_source=source,
    )
