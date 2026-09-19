"""
MuleTrace AI — Temporal Edge Cases & Explainability Tests.

Tests dictionary input polymorphism, JSON serialization, microsecond resolution,
and explainability traceability of contributing transactions.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.domain.models import TransactionEvent
from app.engines.temporal.temporal_engine import temporal_engine


def test_dict_input_polymorphism():
    """Verify that evaluate accepts raw dictionaries and TransactionEvents interchangeably."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    dict_events = [
        {"transaction_id": "TX-D1", "timestamp": str(t0), "amount": 1000.0, "sender_account": "A", "receiver_account": "B"},
        {"transaction_id": "TX-D2", "timestamp": str(t0 + timedelta(minutes=2)), "amount": 2000.0, "sender_account": "A", "receiver_account": "B"},
    ]
    model_events = [
        TransactionEvent(transaction_id="TX-D1", timestamp=t0, amount=1000.0, sender_account="A", receiver_account="B"),
        TransactionEvent(transaction_id="TX-D2", timestamp=t0 + timedelta(minutes=2), amount=2000.0, sender_account="A", receiver_account="B"),
    ]

    res_dict = temporal_engine.evaluate(events=dict_events, reference_time=t0 + timedelta(minutes=5)).to_dict()
    res_model = temporal_engine.evaluate(events=model_events, reference_time=t0 + timedelta(minutes=5)).to_dict()

    assert res_dict == res_model


def test_explainability_traceability():
    """Verify every window aggregation contains exact contributing transaction IDs."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        TransactionEvent(transaction_id="TX-EX-1", timestamp=t0 - timedelta(minutes=3), amount=100.0, sender_account="A", receiver_account="B"),
        TransactionEvent(transaction_id="TX-EX-2", timestamp=t0 - timedelta(minutes=10), amount=200.0, sender_account="A", receiver_account="B"),
        TransactionEvent(transaction_id="TX-EX-3", timestamp=t0 - timedelta(minutes=45), amount=300.0, sender_account="A", receiver_account="B"),
    ]

    features = temporal_engine.evaluate(events=events, reference_time=t0)

    # 5m window should only contain TX-EX-1
    w_5m = features.windows["5m"]
    assert set(w_5m.contributing_transaction_ids) == {"TX-EX-1"}
    assert w_5m.amount_sum == 100.0

    # 15m window should contain TX-EX-1 and TX-EX-2 in chronological order
    w_15m = features.windows["15m"]
    assert set(w_15m.contributing_transaction_ids) == {"TX-EX-1", "TX-EX-2"}
    assert w_15m.amount_sum == 300.0

    # 1h window should contain all 3
    w_1h = features.windows["1h"]
    assert set(w_1h.contributing_transaction_ids) == {"TX-EX-1", "TX-EX-2", "TX-EX-3"}
    assert w_1h.amount_sum == 600.0


def test_features_json_serializability():
    """Verify to_dict output can be serialized to valid JSON without error."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        TransactionEvent(transaction_id="TX-JSON-1", timestamp=t0, amount=150.75, sender_account="A", receiver_account="B"),
    ]

    features = temporal_engine.evaluate(events=events, reference_time=t0)
    feat_dict = features.to_dict()

    json_str = json.dumps(feat_dict)
    assert len(json_str) > 0
    parsed = json.loads(json_str)
    assert parsed["counts"]["5m"] == 1
    assert parsed["volumes"]["5m"] == 150.75


def test_microsecond_resolution():
    """Verify events separated by microseconds do not result in negative or corrupt intervals."""
    t0 = datetime(2026, 9, 19, 12, 0, 0, 1000, tzinfo=timezone.utc)
    t1 = datetime(2026, 9, 19, 12, 0, 0, 2500, tzinfo=timezone.utc)

    events = [
        TransactionEvent(transaction_id="TX-US-1", timestamp=t0, amount=50.0, sender_account="A", receiver_account="B"),
        TransactionEvent(transaction_id="TX-US-2", timestamp=t1, amount=50.0, sender_account="A", receiver_account="B"),
    ]

    features = temporal_engine.evaluate(events=events, reference_time=t1)
    assert features.minimum_interval_seconds is not None
    assert features.minimum_interval_seconds > 0.0
    assert features.minimum_interval_seconds < 0.01
