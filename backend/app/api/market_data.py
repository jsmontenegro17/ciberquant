from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy import select, func
from .deps import db, current_user, require_admin
from ..config import settings
from ..models import Candle, MarketDataImport
from ..market_data.normalization import Dataset, stored_utc
from ..market_data.timeframe import TIMEFRAMES
from ..market_data.ingestion import ingest
from ..market_data.repository import coverage, candle_query, candle_data
from ..cataloger.schemas import CandleQuery, CatalogQuery
from ..cataloger.engine import analyze

router = APIRouter(tags=["market-data"])


def encoded(value):
    return jsonable_encoder(value, custom_encoder={Decimal: str, datetime: lambda d: stored_utc(d).isoformat()})


def import_out(batch):
    values = {column.name: getattr(batch, column.name) for column in MarketDataImport.__table__.columns}
    values["import_id"] = batch.id
    values["errors"] = (batch.error_summary or {}).get("errors", [])
    values["warnings"] = (batch.error_summary or {}).get("warnings", [])
    return values


@router.get("/market-data/options")
def options(user=Depends(current_user)):
    return {
        "timeframes": list(TIMEFRAMES),
        "market_types": ["REGULAR", "OTC"],
        "max_upload_mb": settings.market_data_max_upload_mb,
        "max_rows": settings.market_data_max_rows,
    }


@router.post("/market-data/imports/csv")
def import_csv(
    file: UploadFile = File(...),
    source: str = Form(...),
    symbol: str = Form(...),
    market_type: str = Form(...),
    timeframe: str = Form(...),
    broker: str = Form("UNSPECIFIED"),
    user=Depends(require_admin),
    session=Depends(db),
):
    try:
        dataset = Dataset(source=source, broker=broker, symbol=symbol, market_type=market_type, timeframe=timeframe)
    except ValidationError as exc:
        raise HTTPException(422, str(exc))
    try:
        raw = file.file.read(settings.market_data_max_upload_mb * 1024 * 1024 + 1)
    finally:
        file.file.close()
    if len(raw) > settings.market_data_max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "CSV exceeds configured upload limit")
    # Content is validated independently of filename and client MIME type.
    batch = ingest(session, user.id, dataset, raw, file.filename, settings.market_data_max_rows)
    return encoded(import_out(batch) | {"coverage": coverage(session, dataset)})


@router.get("/market-data/imports")
def imports(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user=Depends(current_user), session=Depends(db)):
    rows = session.scalars(
        select(MarketDataImport).order_by(MarketDataImport.created_at.desc(), MarketDataImport.id.desc()).offset(offset).limit(limit)
    )
    return encoded(
        {
            "items": [import_out(row) for row in rows],
            "total": session.scalar(select(func.count()).select_from(MarketDataImport)),
            "limit": limit,
            "offset": offset,
        }
    )


@router.get("/market-data/coverage")
def dataset_coverage(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), user=Depends(current_user), session=Depends(db)):
    groups = select(*[getattr(Candle, k) for k in Dataset.model_fields]).distinct().subquery()
    return encoded(
        {
            "items": coverage(session, offset=offset, limit=limit),
            "total": session.scalar(select(func.count()).select_from(groups)),
            "limit": limit,
            "offset": offset,
        }
    )


@router.get("/market-data/candles")
def candles(query: CandleQuery = Query(), user=Depends(current_user), session=Depends(db)):
    statement = candle_query(query.dataset(), query.start, query.end)
    rows = list(session.scalars(statement.offset(query.offset).limit(query.limit)))
    total = session.scalar(select(func.count()).select_from(statement.order_by(None).subquery()))
    return encoded(
        {
            "items": [dict(id=c.id, import_id=c.import_id, **candle_data(c).__dict__) for c in rows],
            "total": total,
            "limit": query.limit,
            "offset": query.offset,
        }
    )


@router.get("/cataloger/patterns")
def patterns(query: CatalogQuery = Query(), user=Depends(current_user), session=Depends(db)):
    statement = candle_query(query.dataset(), query.start, query.end)
    total = session.scalar(select(func.count()).select_from(statement.order_by(None).subquery()))
    if total > settings.market_data_max_catalog_candles:
        raise HTTPException(422, f"Range exceeds {settings.market_data_max_catalog_candles} candles; narrow dates")
    rows = session.scalars(statement.limit(settings.market_data_max_catalog_candles + 1).execution_options(yield_per=1000))
    try:
        result = analyze((candle_data(c) for c in rows), query.pattern_length, query.include_doji)
    except ValueError as exc:
        raise HTTPException(422, f"Dataset quality prevents cataloging: {exc}")
    if result["candles_examined"] > settings.market_data_max_catalog_candles:
        raise HTTPException(422, "Dataset grew during query; narrow dates and retry")
    return encoded(
        {
            "metadata": query.model_dump(exclude={"limit", "offset"}),
            **result,
            "limitation": "Historical descriptive frequencies only. Overlapping windows may be autocorrelated; no causal or profitability claim.",
        }
    )
