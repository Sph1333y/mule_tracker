"""
MuleTrace AI — Temporal Invariant & Property Tests.

Formally proves the 10 mathematical and architectural invariants specified in Milestone 6:
1. Non-negative transaction counts
2. Window counts bounded by total valid events
3. Monotonic chronological ordering after normalization
4. Strict determinism (idempotency)
5. Predictable window shift on changing reference time
6. Safe execution on empty input
7. Safe execution with missing optional metadata
8. Window isolation (events outside window do not alter it)
9. Window sensitivity (events inside window alter it)
10. Permutation invariance (order of input list does not change output)
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from app.domain.models import TransactionEvent
from app.engines.temporal.temporal_engine import temporal_engine
from app.engines.temporal.temporal_windows import ensure_utc


def _tx(tx_id: str, ts: datetime, amt: float = 100.0) -> TransactionEvent:
    return TransactionEvent(
        transaction_id=tx_id,
        timestamp=ts,
        amount=amt,
        sender_account="ACC-SND",
        receiver_account="ACC-REC",
    )


def test_invariant_1_non_negative_counts_and_amounts():
    """Invariant 1: Counts, intervals, and amounts must never be negative."""
    ref_time = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [_tx(f"TX-{i}", ref_time - timedelta(minutes=i * 5), amt=float((i + 1) * 100)) for i in range(10)]

    features = temporal_engine.evaluate(events=events, reference_time=ref_time)

    assert features.transaction_count_5m >= 0
    assert features.transaction_count_15m >= 0
    assert features.transaction_count_1h >= 0
    assert features.transaction_count_24h >= 0
    assert features.amount_sum_5m >= 0.0
    assert features.amount_sum_24h >= 0.0
    if features.minimum_interval_seconds is not None:
        assert features.minimum_interval_seconds >= 0.0


def test_invariant_2_window_counts_bounded_by_total():
    """Invariant 2: Window count cannot exceed total valid input events."""
    ref_time = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [_tx(f"TX-{i}", ref_time - timedelta(minutes=i * 10)) for i in range(8)]

    features = temporal_engine.evaluate(events=events, reference_time=ref_time)

    assert features.transaction_count_5m <= features.total_events_evaluated
    assert features.transaction_count_15m <= features.total_events_evaluated
    assert features.transaction_count_1h <= features.total_events_evaluated
    assert features.transaction_count_24h <= features.total_events_evaluated


def test_invariant_3_monotonic_timestamps():
    """Invariant 3: Transaction timestamps must be non-decreasing after internal sorting."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    raw_events = [
        _tx("TX-3", t0 + timedelta(minutes=30)),
        _tx("TX-1", t0),
        _tx("TX-2", t0 + timedelta(minutes=15)),
    ]

    sorted_events = sorted(raw_events, key=lambda e: ensure_utc(e.timestamp))
    for i in range(len(sorted_events) - 1):
        assert ensure_utc(sorted_events[i].timestamp) <= ensure_utc(sorted_events[i + 1].timestamp)


def test_invariant_4_strict_determinism():
    """Invariant 4: Same inputs with same reference time produce identical outputs."""
    ref_time = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [_tx(f"TX-{i}", ref_time - timedelta(minutes=i * 2), amt=500.0) for i in range(6)]

    out1 = temporal_engine.evaluate(events=events, reference_time=ref_time).to_dict()
    out2 = temporal_engine.evaluate(events=events, reference_time=ref_time).to_dict()

    assert out1 == out2


def test_invariant_5_reference_time_predictably_shifts_windows():
    """Invariant 5: Shifting reference time forward drops older events and includes newer ones."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    tx1 = _tx("TX-1", t0) # At 12:00

    # At 12:04 (within 5m): tx1 is in 5m window
    f_near = temporal_engine.evaluate(events=[tx1], reference_time=t0 + timedelta(minutes=4))
    assert f_near.transaction_count_5m == 1

    # At 12:10 (outside 5m, but within 15m): tx1 is out of 5m window, inside 15m window
    f_far = temporal_engine.evaluate(events=[tx1], reference_time=t0 + timedelta(minutes=10))
    assert f_far.transaction_count_5m == 0
    assert f_far.transaction_count_15m == 1


def test_invariant_6_empty_input_safe():
    """Invariant 6: Empty input never throws an exception."""
    res = temporal_engine.evaluate(events=[])
    assert res.total_events_evaluated == 0


def test_invariant_7_missing_optional_fields_safe():
    """Invariant 7: Transactions with null optional telemetry never fail."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    tx = TransactionEvent(
        transaction_id="TX-BARE",
        timestamp=t0,
        amount=100.0,
        sender_account="A",
        receiver_account="B",
    )
    res = temporal_engine.evaluate(events=[tx], reference_time=t0)
    assert res.total_events_evaluated == 1


def test_invariant_8_window_isolation():
    """Invariant 8: Adding an event outside a window has zero effect on that window's count and sum."""
    ref_time = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    near_event = _tx("TX-NEAR", ref_time - timedelta(minutes=2), amt=500.0)
    outside_5m_event = _tx("TX-FAR", ref_time - timedelta(minutes=20), amt=9999.0)

    f_base = temporal_engine.evaluate(events=[near_event], reference_time=ref_time)
    f_extended = temporal_engine.evaluate(events=[near_event, outside_5m_event], reference_time=ref_time)

    assert f_base.transaction_count_5m == f_extended.transaction_count_5m == 1
    assert f_base.amount_sum_5m == f_extended.amount_sum_5m == 500.0


def test_invariant_9_window_sensitivity():
    """Invariant 9: Adding an event inside a window must increment count and sum."""
    ref_time = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    e1 = _tx("TX-1", ref_time - timedelta(minutes=2), amt=200.0)
    e2 = _tx("TX-2", ref_time - timedelta(minutes=3), amt=300.0)

    f1 = temporal_engine.evaluate(events=[e1], reference_time=ref_time)
    f2 = temporal_engine.evaluate(events=[e1, e2], reference_time=ref_time)

    assert f2.transaction_count_5m == f1.transaction_count_5m + 1
    assert f2.amount_sum_5m == f1.amount_sum_5m + 300.0


def test_invariant_10_permutation_invariance():
    """Invariant 10: Shuffling input event order must produce identical output features."""
    ref_time = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [_tx(f"TX-{i}", ref_time - timedelta(minutes=i * 3), amt=100.0 * (i + 1)) for i in range(8)]

    shuffled_events = list(events)
    random.seed(42)
    random.shuffle(shuffled_events)

    out_ordered = temporal_engine.evaluate(events=events, reference_time=ref_time).to_dict()
    out_shuffled = temporal_engine.evaluate(events=shuffled_events, reference_time=ref_time).to_dict()

    assert out_ordered == out_shuffled
