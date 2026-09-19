"""Bounded local-only history tracker. Stores market data, never provider objects/auth."""

import json
from datetime import datetime, timezone


def emit(value):
    print(json.dumps(value, default=str), flush=True)


class HistoryTracker:
    def __init__(self, sink=emit, max_records=100000):
        self.records, self.conflicts = {}, []
        self.sequence, self.generation, self.count = 0, 0, 0
        self.sink, self.max_records = sink, max_records
        self.label = None

    def observe(self, dataset, candles, metadata):
        self.sequence += 1
        for c in candles:
            # Same frozen CLOSED criterion; forming snapshots are separately labelled.
            if c.close_time > metadata["provider_time"]:
                continue
            if self.count >= self.max_records:
                raise ValueError("IQ_DIAGNOSTIC_CAP_REACHED")
            rec = dict(
                dataset.model_dump(),
                **metadata,
                open_time=c.open_time,
                close_time=c.close_time,
                query_sequence=self.sequence,
                reconnect_generation=self.generation,
                before_or_after_reconnect="AFTER" if self.generation else "BEFORE",
                sample_label=self.label,
                age_after_close_ms=int((metadata["provider_time"] - c.close_time).total_seconds() * 1000),
                ohlc={k: str(getattr(c, k)) for k in ("open", "high", "low", "close")},
            )
            key = (*dataset.model_dump().values(), c.open_time)
            previous = self.records.setdefault(key, [])
            if previous and previous[-1]["ohlc"] != rec["ohlc"]:
                conflict = dict(
                    stage="CLOSED_REVISION",
                    detection_layer="LOCAL_HISTORY_OBSERVER",
                    first=previous[0],
                    previous=previous[-1],
                    revised=rec,
                    changed_fields=[k for k in rec["ohlc"] if previous[-1]["ohlc"][k] != rec["ohlc"][k]],
                    orders_sent=0,
                )
                self.conflicts.append(conflict)
                self.sink(conflict)
            previous.append(rec)
            self.count += 1

    def runtime_conflict(self, exc):
        details = dict(exc.details)
        observations = next(
            (
                v
                for k, v in self.records.items()
                if k[:5] == tuple(details[x] for x in ("source", "broker", "symbol", "market_type", "timeframe"))
                and k[5].isoformat() == details["open_time"]
            ),
            [],
        )
        self.sink(dict(stage="DATA_CONFLICT", **details, observations=observations, orders_sent=0))

    def snapshots(self, dataset, target):
        return self.records.get((*dataset.model_dump().values(), target), [])

    def report(self):
        self.sink(
            dict(
                stage="DIAGNOSTIC_SUMMARY",
                observations=self.count,
                queries=self.sequence,
                revisions=len(self.conflicts),
                reconnect_generation=self.generation,
                result="REPRODUCED" if self.conflicts else "NOT_REPRODUCED",
                completed_at=datetime.now(timezone.utc),
                orders_sent=0,
            )
        )
