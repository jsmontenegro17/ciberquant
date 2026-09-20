from dataclasses import asdict, replace
from sqlalchemy import select
from ..models import Candle, LiveObservation
from ..market_data.normalization import identity, stored_utc
from ..market_data.repository import lock_dataset, existing_for
from ..market_data.quality import validate_candle, VALUE_FIELDS
from .conflicts import DataConflictError


def persist_closed(session, dataset, candles, provider, mode, server_time, received_at, phase="OBSERVED"):
    lock_dataset(session, dataset)
    existing = existing_for(session, dataset, candles)
    result = []
    for c in candles:
        if identity(c) != tuple(dataset.model_dump().values()) or validate_candle(c) or c.close_time > server_time:
            raise ValueError("INVALID_CLOSED_CANDLE")
        old = existing.get(c.open_time)
        if old is not None:
            if stored_utc(old.close_time) != c.close_time or any(getattr(old, k) != getattr(c, k) for k in VALUE_FIELDS):
                first = session.scalar(
                    select(LiveObservation).where(LiveObservation.candle_id == old.id).order_by(LiveObservation.id).limit(1)
                )
                conflict = DataConflictError(
                    dataset,
                    old,
                    c,
                    phase=phase,
                    detection_layer=f"RUNTIME_{phase}_PERSISTENCE",
                    provider=provider,
                    first_provider_time=first.provider_timestamp
                    if first and (first.phase != "BOOTSTRAP" or first.mode == "REPLAY")
                    else None,
                    second_provider_time=server_time if phase != "BOOTSTRAP" or mode == "REPLAY" else None,
                    first_received_time=first.received_at if first else None,
                    second_received_time=received_at,
                )
                # Live runtime bootstrap historically stores local receive time here.
                # Do not relabel that as an actual IQ clock in new diagnostics.
                conflict.details["first_persisted_clock_source"] = (
                    (
                        "REPLAY_LOGICAL"
                        if first.mode == "REPLAY"
                        else "LOCAL_BOOTSTRAP_RECEIVE"
                        if first.phase == "BOOTSTRAP"
                        else "PROVIDER"
                    )
                    if first
                    else "UNKNOWN"
                )
                conflict.details["second_persisted_clock_source"] = (
                    "REPLAY_LOGICAL" if mode == "REPLAY" else "LOCAL_BOOTSTRAP_RECEIVE" if phase == "BOOTSTRAP" else "PROVIDER"
                )
                raise conflict
        else:
            values = asdict(c)
            values.pop("candle_id", None)
            old = Candle(**values)
            session.add(old)
            session.flush()
            existing[c.open_time] = old
        observed = session.scalar(
            select(LiveObservation.id).where(
                LiveObservation.candle_id == old.id,
                LiveObservation.provider == provider,
                LiveObservation.mode == mode,
                LiveObservation.phase == phase,
            )
        )
        if observed is None:
            session.add(
                LiveObservation(
                    candle_id=old.id, provider=provider, mode=mode, phase=phase, provider_timestamp=server_time, received_at=received_at
                )
            )
            session.flush()
        result.append(replace(c, candle_id=old.id))
    return result
