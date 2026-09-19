"""
MuleTrace AI — Temporal Window Engine & Timezone Normalization Tests.

Tests boundary conditions, window durations (5m, 15m, 1h, 24h), and UTC normalization.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.domain.models import TransactionEvent
from app.engines.temporal.temporal_windows import (
    STANDARD_WINDOWS,
    compute_window_aggregation,
    ensure_utc,
    filter_events_in_range,
    parse_timestamp,
)


def _tx(tx_id: str, ts: datetime, amt: float = 100.0) -> TransactionEvent:
    return TransactionEvent(
        transaction_id=tx_id,
        timestamp=ts,
        amount=amt,
        sender_account="ACC-1",
        receiver_account="ACC-2",
    )


def test_ensure_utc_naive_and_aware():
    """Verify offset-naive datetimes become UTC and offset-aware convert cleanly."""
    naive = datetime(2026, 9, 19, 10, 30, 0)
    aware_utc = ensure_utc(naive)
    assert aware_utc.tzinfo == timezone.utc
    assert aware_utc.hour == 10

    # Non-UTC timezone conversion
    ist = timezone(timedelta(hours=5, minutes=30))
    aware_ist = datetime(2026, 9, 19, 15, 30, 0, tzinfo=ist)
    converted_utc = ensure_utc(aware_ist)
    assert converted_utc.tzinfo == timezone.utc
    assert converted_utc.hour == 10  # 15:30 IST is 10:00 UTC


def test_parse_timestamp_variations():
    """Verify parse_timestamp supports datetime, ISO strings with Z, and offset strings."""
    dt_iso_z = parse_timestamp("2026-09-19T10:00:00Z")
    assert dt_iso_z.tzinfo == timezone.utc
    assert dt_iso_z.hour == 10

    dt_sql = parse_timestamp("2026-09-19 10:00:00")
    assert dt_sql.tzinfo == timezone.utc


def test_window_durations_in_seconds():
    """Verify that standard window durations match exact seconds."""
    assert STANDARD_WINDOWS["5m"] == 300
    assert STANDARD_WINDOWS["15m"] == 900
    assert STANDARD_WINDOWS["1h"] == 3600
    assert STANDARD_WINDOWS["24h"] == 86400


def test_window_boundary_inclusivity():
    """Verify that events on the exact boundary [ref - window, ref] are included."""
    ref_time = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    exact_start = ref_time - timedelta(minutes=5)
    exact_end = ref_time
    just_outside = exact_start - timedelta(seconds=1)

    events = [
        _tx("TX-OUTSIDE", just_outside, 10.0),
        _tx("TX-START", exact_start, 20.0),
        _tx("TX-MID", ref_time - timedelta(minutes=2), 30.0),
        _tx("TX-END", exact_end, 40.0),
    ]

    agg = compute_window_aggregation(
        events=events,
        window_name="5m",
        window_seconds=300,
        reference_time=ref_time,
    )

    assert agg.transaction_count == 3
    assert agg.amount_sum == 90.0
    assert "TX-OUTSIDE" not in agg.contributing_transaction_ids
    assert "TX-START" in agg.contributing_transaction_ids
    assert "TX-MID" in agg.contributing_transaction_ids
    assert "TX-END" in agg.contributing_transaction_ids
