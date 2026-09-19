"""
MuleTrace AI — Temporal Window Engine & Timezone Normalization.

Provides deterministic timestamp normalization, window slicing (5m, 15m, 1h, 24h),
and window aggregations over Canonical TransactionEvents.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.domain.models import TransactionEvent
from app.engines.temporal.temporal_models import WindowAggregation

# Standard temporal window definitions in seconds
STANDARD_WINDOWS: dict[str, int] = {
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "24h": 86400,
}


def ensure_utc(dt: datetime) -> datetime:
    """Normalize a datetime to timezone-aware UTC.

    Treats offset-naive datetimes as UTC and converts offset-aware datetimes to UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_timestamp(value: Any) -> datetime:
    """Safely convert datetime, string, or timestamp into timezone-aware UTC datetime."""
    if isinstance(value, datetime):
        return ensure_utc(value)
    if isinstance(value, str):
        # Handle ISO-8601 strings
        cleaned = value.replace("Z", "+00:00")
        try:
            return ensure_utc(datetime.fromisoformat(cleaned))
        except ValueError:
            # Common SQL format fallback
            return ensure_utc(datetime.strptime(value, "%Y-%m-%d %H:%M:%S"))
    raise TypeError(f"Unsupported timestamp type: {type(value)} ({value})")


def filter_events_in_range(
    events: list[TransactionEvent],
    start_time: datetime,
    end_time: datetime,
) -> list[TransactionEvent]:
    """Filter events within the closed interval [start_time, end_time].

    Assumes events have normalized UTC timestamps.
    """
    start_utc = ensure_utc(start_time)
    end_utc = ensure_utc(end_time)
    return [
        e for e in events
        if start_utc <= ensure_utc(e.timestamp) <= end_utc
    ]


def compute_window_aggregation(
    events: list[TransactionEvent],
    window_name: str,
    window_seconds: int,
    reference_time: datetime,
) -> WindowAggregation:
    """Compute deterministic count, volume, and contributing transaction IDs for a time window."""
    ref_utc = ensure_utc(reference_time)
    start_utc = ref_utc - timedelta(seconds=window_seconds)

    matched_events = filter_events_in_range(events, start_utc, ref_utc)
    tx_ids = [e.transaction_id for e in matched_events]
    amount_sum = sum(e.amount for e in matched_events)

    return WindowAggregation(
        window_name=window_name,
        window_seconds=window_seconds,
        start_time=start_utc,
        end_time=ref_utc,
        transaction_count=len(matched_events),
        amount_sum=amount_sum,
        contributing_transaction_ids=tx_ids,
    )
