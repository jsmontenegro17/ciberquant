from dataclasses import asdict, replace
from sqlalchemy import select
from ..models import Candle, LiveObservation
from ..market_data.normalization import identity, stored_utc
from ..market_data.repository import lock_dataset, existing_for
from ..market_data.quality import validate_candle, VALUE_FIELDS


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
                raise ValueError("DATA_CONFLICT")
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
