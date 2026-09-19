"""
MuleTrace AI — Unit Tests for Temporal Evidence Extraction (M6).
"""

from datetime import datetime, timezone

from app.domain.models import TransactionEvent
from app.engines.evidence.collectors import collect_temporal_evidence
from app.engines.evidence.models import EvidenceCategory, EvidenceSeverity, EvidenceSource
from app.engines.temporal.temporal_models import (
    PassThroughEvent,
    TemporalFeatures,
    WindowAggregation,
)


def _create_sample_event() -> TransactionEvent:
    return TransactionEvent(
        transaction_id="TX_MAIN_999",
        timestamp=datetime(2026, 9, 19, 11, 0, tzinfo=timezone.utc),
        sender_account="ACC_MULE_01",
        receiver_account="ACC_CASHOUT_02",
        amount=75000.0,
    )


def test_collect_temporal_rapid_pass_through() -> None:
    """Verify rapid pass-through extracts correct metrics and transaction references."""
    event = _create_sample_event()
    ref_time = datetime(2026, 9, 19, 11, 0, tzinfo=timezone.utc)

    pt_event = PassThroughEvent(
        account_id="ACC_MULE_01",
        incoming_transaction_id="TX_IN_101",
        outgoing_transaction_id="TX_OUT_102",
        incoming_time=datetime(2026, 9, 19, 10, 55, tzinfo=timezone.utc),
        outgoing_time=datetime(2026, 9, 19, 10, 57, tzinfo=timezone.utc),
        delay_seconds=120.0,
        incoming_amount=100000.0,
        outgoing_amount=95000.0,
        pass_through_ratio=0.95,
    )

    tf = TemporalFeatures(
        reference_time=ref_time,
        rapid_in_out_detected=True,
        rapid_in_out_delay_seconds=120.0,
        rapid_in_out_ratio=0.95,
        rapid_in_out_events=[pt_event],
    )

    items = collect_temporal_evidence(tf, event=event)
    assert len(items) == 1
    item = items[0]

    assert item.source == EvidenceSource.TEMPORAL
    assert item.source_reference == "TEMPORAL:rapid_in_out"
    assert item.category == EvidenceCategory.TEMPORAL_ANOMALY
    assert item.severity == EvidenceSeverity.CRITICAL
    assert item.metrics["delay_seconds"] == 120.0
    assert item.metrics["pass_through_ratio"] == 0.95
    assert "TX_IN_101" in item.transaction_ids
    assert "TX_OUT_102" in item.transaction_ids
    assert "ACC_MULE_01" in item.account_ids


def test_collect_temporal_burst_and_velocity() -> None:
    """Verify burst activity and 1h velocity spikes generate separate evidence items."""
    ref_time = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
    w1h = WindowAggregation(
        window_name="1h",
        window_seconds=3600,
        start_time=datetime(2026, 9, 19, 11, 0, tzinfo=timezone.utc),
        end_time=ref_time,
        transaction_count=12,
        amount_sum=350000.0,
        contributing_transaction_ids=["TX_B1", "TX_B2", "TX_B3", "TX_B4"],
    )

    tf = TemporalFeatures(
        reference_time=ref_time,
        burst_detected=True,
        burst_count=6,
        burst_transaction_ids=["TX_BURST_1", "TX_BURST_2", "TX_BURST_3"],
        transaction_count_1h=12,
        amount_sum_1h=350000.0,
        windows={"1h": w1h},
    )

    items = collect_temporal_evidence(tf)
    assert len(items) == 2

    refs = [i.source_reference for i in items]
    assert "TEMPORAL:burst" in refs
    assert "TEMPORAL:velocity_1h" in refs

    burst_item = next(i for i in items if i.source_reference == "TEMPORAL:burst")
    assert burst_item.severity == EvidenceSeverity.HIGH
    assert burst_item.metrics["burst_count"] == 6
    assert "TX_BURST_1" in burst_item.transaction_ids

    vel_item = next(i for i in items if i.source_reference == "TEMPORAL:velocity_1h")
    assert vel_item.severity == EvidenceSeverity.HIGH
    assert vel_item.metrics["transaction_count_1h"] == 12
    assert "TX_B1" in vel_item.transaction_ids


def test_collect_temporal_calm_and_none() -> None:
    """Verify calm temporal features or None safely yield zero evidence."""
    assert collect_temporal_evidence(None) == []

    ref_time = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
    calm_tf = TemporalFeatures(
        reference_time=ref_time,
        transaction_count_1h=1,
        amount_sum_1h=1000.0,
        burst_detected=False,
        rapid_in_out_detected=False,
    )
    assert collect_temporal_evidence(calm_tf) == []
