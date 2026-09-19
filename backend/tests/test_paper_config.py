from decimal import Decimal
import pytest
from app.live.paper_config import resolve_paper_config


@pytest.mark.parametrize(
    "research,provider,payout,source,expiry,expiry_source",
    [
        (True, None, "90", "RESEARCH_ASSUMPTION", 3, "RESEARCH_ASSUMPTION"),
        (True, "87", "87", "PROVIDER", 3, "RESEARCH_ASSUMPTION"),
        (False, None, "84", "VALIDATION_ASSUMPTION", 1, "VALIDATION_ASSUMPTION"),
        (False, "79", "79", "PROVIDER", 1, "VALIDATION_ASSUMPTION"),
    ],
)
def test_explicit_mode_precedence(research, provider, payout, source, expiry, expiry_source):
    result = resolve_paper_config(
        research_mode=research,
        provider_payout=Decimal(provider) if provider else None,
        validation_payout=Decimal("84"),
        validation_expiry=1,
        research_payout=Decimal("90"),
        research_expiry=3,
    )
    assert result.payout == Decimal(payout)
    assert isinstance(result.payout, Decimal)
    assert (result.payout_source, result.expiry_bars, result.expiry_source) == (source, expiry, expiry_source)


@pytest.mark.parametrize("research", [False, True])
def test_missing_mode_assumptions_never_fall_back_to_other_mode(research):
    result = resolve_paper_config(
        research_mode=research,
        provider_payout=None,
        validation_payout=None if not research else Decimal("84"),
        validation_expiry=None if not research else 1,
        research_payout=None if research else Decimal("90"),
        research_expiry=None if research else 3,
    )
    assert result.payout is None and result.expiry_bars is None
