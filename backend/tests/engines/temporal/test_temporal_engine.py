"""
MuleTrace AI — Temporal Engine Fixture Tests (Fixtures A through L).

Validates all 12 canonical test scenarios required by Milestone 6:
- Fixture A: Empty history
- Fixture B: Single transaction
- Fixture C: Normal activity
- Fixture D: High-frequency burst
- Fixture E: Rapid pass-through (<15m)
- Fixture F: Slow pass-through (>15m)
- Fixture G: Unsorted input
- Fixture H: Identical timestamps
- Fixture I: Missing optional data
- Fixture J: Activity change
- Fixture K: Zero baseline
- Fixture L: Duplicate transaction IDs
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.domain.models import TransactionEvent
from app.engines.temporal.temporal_engine import TemporalEngine, temporal_engine


def _create_tx(
    tx_id: str,
    timestamp: datetime,
    amount: float = 1000.0,
    sender: str = "ACC-A",
    receiver: str = "ACC-B",
    channel: str = "UPI",
    **kwargs,
) -> TransactionEvent:
    return TransactionEvent(
        transaction_id=tx_id,
        timestamp=timestamp,
        amount=amount,
        sender_account=sender,
        receiver_account=receiver,
        channel=channel,
        **kwargs,
    )


# -----------------------------------------------------------------------------
# FIXTURE A — EMPTY HISTORY
# -----------------------------------------------------------------------------
def test_fixture_a_empty_history():
    """Empty events input must return zero metrics without crashing."""
    ref_time = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    features = temporal_engine.evaluate(events=[], reference_time=ref_time)

    assert features.total_events_evaluated == 0
    assert features.transaction_count_5m == 0
    assert features.transaction_count_15m == 0
    assert features.transaction_count_1h == 0
    assert features.transaction_count_24h == 0
    assert features.amount_sum_5m == 0.0
    assert features.amount_sum_24h == 0.0
    assert features.average_interval_seconds is None
    assert features.minimum_interval_seconds is None
    assert features.burst_detected is False
    assert features.burst_count == 0
    assert features.rapid_in_out_detected is False
    assert features.sequence_duration_seconds == 0.0
    assert features.temporal_concentration == 0.0
    assert features.activity_change_ratio == 0.0


# -----------------------------------------------------------------------------
# FIXTURE B — SINGLE TRANSACTION
# -----------------------------------------------------------------------------
def test_fixture_b_single_transaction():
    """A single event must calculate correct count, amount, and no false burst."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    tx = _create_tx("TX-1", t0, amount=5000.0)

    features = temporal_engine.evaluate(events=[tx], reference_time=t0)

    assert features.total_events_evaluated == 1
    assert features.transaction_count_5m == 1
    assert features.transaction_count_24h == 1
    assert features.amount_sum_5m == 5000.0
    assert features.amount_sum_24h == 5000.0
    assert features.average_interval_seconds is None  # Single event has no interval
    assert features.burst_detected is False
    assert features.burst_count == 1
    assert features.rapid_in_out_detected is False
    assert features.sequence_duration_seconds == 0.0
    assert features.temporal_concentration == 1.0


# -----------------------------------------------------------------------------
# FIXTURE C — NORMAL ACTIVITY SPREAD ACROSS HOURS
# -----------------------------------------------------------------------------
def test_fixture_c_normal_activity():
    """Transactions spaced over several hours must fall into expected rolling windows."""
    ref_time = datetime(2026, 9, 19, 15, 0, 0, tzinfo=timezone.utc)
    events = [
        _create_tx("TX-1", ref_time - timedelta(hours=10), amount=1000.0),
        _create_tx("TX-2", ref_time - timedelta(hours=2), amount=2000.0),
        _create_tx("TX-3", ref_time - timedelta(minutes=30), amount=3000.0),
        _create_tx("TX-4", ref_time - timedelta(minutes=2), amount=4000.0),
    ]

    features = temporal_engine.evaluate(events=events, reference_time=ref_time)

    assert features.total_events_evaluated == 4
    assert features.transaction_count_5m == 1  # TX-4 (2 min ago)
    assert features.transaction_count_15m == 1 # TX-4
    assert features.transaction_count_1h == 2  # TX-3 (30m) & TX-4 (2m)
    assert features.transaction_count_24h == 4 # All 4
    assert features.amount_sum_5m == 4000.0
    assert features.amount_sum_1h == 7000.0
    assert features.amount_sum_24h == 10000.0
    assert features.burst_detected is False


# -----------------------------------------------------------------------------
# FIXTURE D — HIGH-FREQUENCY BURST
# -----------------------------------------------------------------------------
def test_fixture_d_high_frequency_burst():
    """7 transactions within 3 minutes must trigger burst detection."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        _create_tx(f"BURST-{i}", t0 + timedelta(seconds=i * 20), amount=500.0)
        for i in range(7)
    ]

    features = temporal_engine.evaluate(events=events, reference_time=t0 + timedelta(minutes=5))

    assert features.total_events_evaluated == 7
    assert features.burst_detected is True
    assert features.burst_count >= 5
    assert len(features.burst_transaction_ids) >= 5
    assert features.minimum_interval_seconds == 20.0
    assert features.average_interval_seconds == 20.0


# -----------------------------------------------------------------------------
# FIXTURE E — RAPID PASS-THROUGH (<15m)
# -----------------------------------------------------------------------------
def test_fixture_e_rapid_pass_through():
    """Inflow followed by outflow within 5 minutes must flag rapid pass-through."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        _create_tx("TX-IN", t0, amount=100000.0, sender="VICTIM", receiver="MULE-NODE"),
        _create_tx("TX-OUT", t0 + timedelta(minutes=5), amount=98000.0, sender="MULE-NODE", receiver="CASH-OUT"),
    ]

    features = temporal_engine.evaluate(events=events, focal_account="MULE-NODE")

    assert features.rapid_in_out_detected is True
    assert features.rapid_in_out_delay_seconds == 300.0
    assert features.rapid_in_out_ratio == 0.98
    assert len(features.rapid_in_out_events) == 1
    assert features.rapid_in_out_events[0].account_id == "MULE-NODE"


# -----------------------------------------------------------------------------
# FIXTURE F — SLOW PASS-THROUGH (>15m)
# -----------------------------------------------------------------------------
def test_fixture_f_slow_pass_through():
    """Inflow followed by outflow after 2 hours must NOT flag rapid pass-through."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        _create_tx("TX-IN", t0, amount=100000.0, sender="VICTIM", receiver="MULE-NODE"),
        _create_tx("TX-OUT", t0 + timedelta(hours=2), amount=98000.0, sender="MULE-NODE", receiver="CASH-OUT"),
    ]

    features = temporal_engine.evaluate(events=events, focal_account="MULE-NODE")

    assert features.rapid_in_out_detected is False
    assert len(features.rapid_in_out_events) == 0


# -----------------------------------------------------------------------------
# FIXTURE G — UNSORTED INPUT
# -----------------------------------------------------------------------------
def test_fixture_g_unsorted_input():
    """Events provided out of chronological order must be sorted correctly."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    e1 = _create_tx("TX-1", t0, amount=100.0)
    e2 = _create_tx("TX-2", t0 + timedelta(minutes=10), amount=200.0)
    e3 = _create_tx("TX-3", t0 + timedelta(minutes=20), amount=300.0)

    # Supply out of order: e3, e1, e2
    features = temporal_engine.evaluate(events=[e3, e1, e2], reference_time=t0 + timedelta(minutes=30))

    assert features.total_events_evaluated == 3
    assert features.average_interval_seconds == 600.0  # 10 minutes between each
    assert features.sequence_duration_seconds == 1200.0 # 20 minutes total


# -----------------------------------------------------------------------------
# FIXTURE H — IDENTICAL TIMESTAMPS
# -----------------------------------------------------------------------------
def test_fixture_h_identical_timestamps():
    """Multiple events at the exact same timestamp must not cause division by zero."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        _create_tx("TX-1", t0, amount=1000.0),
        _create_tx("TX-2", t0, amount=2000.0),
        _create_tx("TX-3", t0, amount=3000.0),
    ]

    features = temporal_engine.evaluate(events=events, reference_time=t0)

    assert features.total_events_evaluated == 3
    assert features.minimum_interval_seconds == 0.0
    assert features.average_interval_seconds == 0.0
    assert features.amount_sum_5m == 6000.0
    assert features.sequence_duration_seconds == 0.0


# -----------------------------------------------------------------------------
# FIXTURE I — MISSING OPTIONAL DATA
# -----------------------------------------------------------------------------
def test_fixture_i_missing_optional_data():
    """Events missing device, IP, location must compute temporal features cleanly."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        _create_tx("TX-NO-META-1", t0, amount=500.0, device_id=None, ip_address=None, location_city=None),
        _create_tx("TX-NO-META-2", t0 + timedelta(minutes=2), amount=700.0, device_id=None, ip_address=None),
    ]

    features = temporal_engine.evaluate(events=events, reference_time=t0 + timedelta(minutes=5))

    assert features.total_events_evaluated == 2
    assert features.transaction_count_5m == 2
    assert features.amount_sum_5m == 1200.0
    assert features.average_interval_seconds == 120.0


# -----------------------------------------------------------------------------
# FIXTURE J — ACTIVITY CHANGE
# -----------------------------------------------------------------------------
def test_fixture_j_activity_change():
    """Previous window has 2 txns, current window has 6 txns -> change ratio = 3.0."""
    ref_time = datetime(2026, 9, 19, 14, 0, 0, tzinfo=timezone.utc)

    # Previous 1h window: [12:00, 13:00] -> 2 transactions
    prev_events = [
        _create_tx("PREV-1", ref_time - timedelta(minutes=100)),
        _create_tx("PREV-2", ref_time - timedelta(minutes=80)),
    ]

    # Current 1h window: [13:00, 14:00] -> 6 transactions
    curr_events = [
        _create_tx(f"CURR-{i}", ref_time - timedelta(minutes=10 + i * 5))
        for i in range(6)
    ]

    features = temporal_engine.evaluate(events=prev_events + curr_events, reference_time=ref_time)

    assert features.previous_window_count == 2
    assert features.current_window_count == 6
    assert features.activity_change_ratio == 3.0


# -----------------------------------------------------------------------------
# FIXTURE K — ZERO BASELINE
# -----------------------------------------------------------------------------
def test_fixture_k_zero_baseline():
    """When previous window has 0 transactions and current window has 4, ratio safely reports 4.0."""
    ref_time = datetime(2026, 9, 19, 14, 0, 0, tzinfo=timezone.utc)

    curr_events = [
        _create_tx(f"SURGE-{i}", ref_time - timedelta(minutes=10 + i * 5))
        for i in range(4)
    ]

    features = temporal_engine.evaluate(events=curr_events, reference_time=ref_time)

    assert features.previous_window_count == 0
    assert features.current_window_count == 4
    assert features.activity_change_ratio == 4.0  # Safe non-zero representation


# -----------------------------------------------------------------------------
# FIXTURE L — DUPLICATE TRANSACTION ID
# -----------------------------------------------------------------------------
def test_fixture_l_duplicate_transaction_id():
    """Duplicate transaction IDs are deduplicated, preserving the first instance."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        _create_tx("TX-DUP", t0, amount=1000.0),
        _create_tx("TX-DUP", t0 + timedelta(seconds=10), amount=9999.0),
        _create_tx("TX-UNIQUE", t0 + timedelta(seconds=30), amount=2000.0),
    ]

    features = temporal_engine.evaluate(events=events, reference_time=t0 + timedelta(minutes=5))

    assert features.total_events_evaluated == 2
    assert features.transaction_count_5m == 2
    assert features.amount_sum_5m == 3000.0  # 1000.0 + 2000.0 (duplicate 9999.0 was omitted)
