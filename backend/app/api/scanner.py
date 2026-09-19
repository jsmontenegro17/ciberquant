import asyncio
import json
from datetime import timedelta
from decimal import Decimal
from typing import Literal
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .deps import current_user, db
from .research import record, page
from ..db import SessionLocal
from ..models import ScannerWatchlist, ScannerWatchItem, ScannerEvent, ScannerOutcome, LiveSubscription, now
from ..market_data.normalization import Dataset, stored_utc
from ..strategies.dsl import digest, number
from ..strategies.repository import owned, audit
from ..live.policy import compatibility
from ..live.providers import CAPABILITIES
from ..live import LIVE_DATA_ENGINE_VERSION, SCANNER_ENGINE_VERSION
from ..features.serialization import serialize
from ..config import settings

router = APIRouter(tags=["scanner"])


class WatchlistCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["REPLAY", "MT5", "IQOPTION"]
    dataset: Dataset
    strategy_version_id: int = Field(gt=0, strict=True)
    research_mode: bool = Field(default=False, strict=True)
    research_payout: str | None = None
    research_expiry: int | None = Field(default=None, ge=1, le=60, strict=True)

    @field_validator("research_payout")
    @classmethod
    def payout(cls, value):
        if value is not None and not 0 < number(value, 6) <= 100:
            raise ValueError("Invalid paper payout")
        return value


class Toggle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = Field(strict=True)


def provider_definitions():
    return [
        dict(
            provider="REPLAY",
            enabled=settings.enable_replay_provider,
            mode="REPLAY",
            capabilities={**CAPABILITIES, "payout": True, "forming_candle": False},
        ),
        dict(
            provider="MT5",
            enabled=settings.enable_mt5_provider,
            mode="LIVE",
            capabilities={**CAPABILITIES, "server_time": False, "market_status": False},
        ),
        dict(
            provider="IQOPTION",
            enabled=settings.enable_iqoption_experimental,
            mode="EXPERIMENTAL",
            capabilities={k: False for k in CAPABILITIES},
            warning="EXPERIMENTAL DATA PROVIDER / PROVIDER UNAVAILABLE",
        ),
    ]


def item_view(item):
    data = record(item)
    if item.enabled and now() - stored_utc(item.updated_at) > timedelta(seconds=settings.live_heartbeat_seconds):
        data.update(state="PROVIDER_DOWN", latest={**(data["latest"] or {}), "state": "PROVIDER_DOWN", "error": "WORKER_HEARTBEAT_EXPIRED"})
    return data


@router.get("/live/providers")
def providers(user=Depends(current_user)):
    return dict(
        items=provider_definitions(),
        live_data_engine_version=LIVE_DATA_ENGINE_VERSION,
        scanner_engine_version=SCANNER_ENGINE_VERSION,
        stale_factor=settings.live_stale_factor,
        heartbeat_seconds=settings.live_heartbeat_seconds,
    )


@router.get("/live/providers/{provider}/health")
def health(provider: str, user=Depends(current_user), session=Depends(db)):
    keys = select(ScannerWatchItem.subscription_key).where(ScannerWatchItem.user_id == user.id, ScannerWatchItem.provider == provider)
    result = []
    for sub in session.scalars(select(LiveSubscription).where(LiveSubscription.key.in_(keys))):
        value = record(sub)
        value.pop("snapshot", None)
        if now() - stored_utc(sub.updated_at) > timedelta(seconds=settings.live_heartbeat_seconds):
            value["status"] = "DISCONNECTED"
        result.append(value)
    return result


@router.get("/live/snapshot")
def snapshot(item_id: int, user=Depends(current_user), session=Depends(db)):
    item = owned(session, ScannerWatchItem, item_id, user.id)
    sub = session.get(LiveSubscription, item.subscription_key)
    value = record(sub) if sub else None
    if sub and now() - stored_utc(sub.updated_at) > timedelta(seconds=settings.live_heartbeat_seconds):
        value["status"] = "DISCONNECTED"
        value["health"] = {**value["health"], "status": "DISCONNECTED", "error": "WORKER_HEARTBEAT_EXPIRED"}
        value["snapshot"] = {**(value["snapshot"] or {}), "forming": None, "forming_state": None}
    return dict(item=item_view(item), subscription=value)


@router.post("/scanner/watchlists")
def create_list(body: WatchlistCreate, user=Depends(current_user), session=Depends(db)):
    watch = ScannerWatchlist(user_id=user.id, name=body.name)
    session.add(watch)
    session.flush()
    audit(session, user.id, "SCANNER_WATCHLIST_CREATED", "scanner_watchlist", watch.id)
    session.commit()
    return record(watch)


@router.get("/scanner/watchlists")
def lists(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user=Depends(current_user), session=Depends(db)):
    return page(session, ScannerWatchlist, [ScannerWatchlist.user_id == user.id], ScannerWatchlist.id.desc(), limit, offset)


@router.get("/scanner/items")
def items(
    include_research: bool = False,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(current_user),
    session=Depends(db),
):
    where = [ScannerWatchItem.user_id == user.id]
    if not include_research:
        where.append(ScannerWatchItem.research_mode.is_(False))
    return page(session, ScannerWatchItem, where, ScannerWatchItem.id.desc(), limit, offset, item_view)


@router.post("/scanner/watchlists/{list_id}/items")
def new_item(list_id: int, body: ItemCreate, user=Depends(current_user), session=Depends(db)):
    owned(session, ScannerWatchlist, list_id, user.id)
    _, policy = compatibility(session, user.id, body.strategy_version_id, body.dataset)
    if not body.research_mode and not policy["compatible"]:
        raise HTTPException(422, "HISTORICALLY_VALIDATED on the exact dataset and TESTING lifecycle required")
    if body.research_mode and (body.research_payout is None or body.research_expiry is None):
        raise HTTPException(422, "Research mode requires explicit paper payout/expiry assumptions")
    if body.provider == "MT5" and (body.dataset.source != "MT5" or body.dataset.market_type != "REGULAR"):
        raise HTTPException(422, "MT5 supports its own REGULAR datasets only; no OTC substitution")
    if body.provider == "IQOPTION" and body.dataset.source != "IQOPTION":
        raise HTTPException(422, "IQOPTION dataset required")
    item = ScannerWatchItem(
        user_id=user.id,
        watchlist_id=list_id,
        **body.model_dump(exclude={"dataset", "research_payout"}),
        dataset=body.dataset.model_dump(),
        research_payout=Decimal(body.research_payout) if body.research_payout else None,
        subscription_key=digest(dict(provider=body.provider, dataset=body.dataset.model_dump())),
    )
    session.add(item)
    try:
        session.flush()
        audit(session, user.id, "SCANNER_ITEM_CREATED", "scanner_item", item.id)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Duplicate watch item")
    return item_view(item)


@router.patch("/scanner/items/{item_id}")
def toggle(item_id: int, body: Toggle, user=Depends(current_user), session=Depends(db)):
    item = owned(session, ScannerWatchItem, item_id, user.id)
    item.enabled = body.enabled
    item.state = "PROVIDER_DOWN" if body.enabled else "PAUSED"
    item.latest = {"state": item.state}
    item.updated_at = now()
    audit(session, user.id, "SCANNER_ITEM_ENABLED" if body.enabled else "SCANNER_ITEM_DISABLED", "scanner_item", item.id)
    session.commit()
    return item_view(item)


@router.get("/scanner/events")
def events(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user=Depends(current_user), session=Depends(db)):
    def convert(e):
        outcome = session.scalar(select(ScannerOutcome).where(ScannerOutcome.scanner_event_id == e.id))
        return {**record(e), "paper_outcome": record(outcome) if outcome else None}

    return page(session, ScannerEvent, [ScannerEvent.user_id == user.id], ScannerEvent.id.desc(), limit, offset, convert)


@router.get("/scanner/stream")
def stream(user=Depends(current_user)):
    uid = user.id

    async def messages():
        # Bounded connection lifetime forces periodic authentication on browser reconnection.
        for _ in range(30):
            with SessionLocal() as session:
                rows = [item_view(i) for i in session.scalars(select(ScannerWatchItem).where(ScannerWatchItem.user_id == uid).limit(100))]
            yield "data: " + json.dumps(serialize(rows)) + "\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(messages(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
