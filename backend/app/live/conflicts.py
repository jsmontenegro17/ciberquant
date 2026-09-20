"""Allowlisted market-data diagnostics; external failure contract is unchanged."""

from ..market_data.normalization import stored_utc
from ..market_data.quality import VALUE_FIELDS


class DataConflictError(ValueError):
    def __init__(
        self,
        dataset,
        old,
        new,
        *,
        phase,
        detection_layer,
        provider=None,
        first_provider_time=None,
        second_provider_time=None,
        first_received_time=None,
        second_received_time=None,
    ):
        super().__init__("DATA_CONFLICT")
        self.details = dict(
            dataset.model_dump(),
            provider=provider,
            phase=phase,
            detection_layer=detection_layer,
            open_time=stored_utc(new.open_time).isoformat(),
            close_time=stored_utc(new.close_time).isoformat(),
            changed_fields=[k for k in VALUE_FIELDS if getattr(old, k) != getattr(new, k)],
        )
        if stored_utc(old.close_time) != stored_utc(new.close_time):
            self.details["changed_fields"].append("close_time")
        for prefix, candle in [("old", old), ("new", new)]:
            for field in ("open", "high", "low", "close"):
                self.details[f"{prefix}_{field}"] = str(getattr(candle, field))
        for prefix, clock, received in [
            ("first", first_provider_time, first_received_time),
            ("second", second_provider_time, second_received_time),
        ]:
            self.details[f"{prefix}_seen_provider_time"] = stored_utc(clock).isoformat() if clock else None
            self.details[f"{prefix}_seen_received_time"] = stored_utc(received).isoformat() if received else None
            self.details[f"age_after_close_{prefix}_ms"] = (
                int((stored_utc(clock) - stored_utc(new.close_time)).total_seconds() * 1000) if clock else None
            )

    @property
    def summary(self):
        return {
            k: self.details[k]
            for k in (
                "provider",
                "source",
                "broker",
                "symbol",
                "market_type",
                "timeframe",
                "open_time",
                "phase",
                "detection_layer",
                "changed_fields",
            )
        }
