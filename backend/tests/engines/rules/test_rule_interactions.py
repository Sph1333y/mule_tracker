"""
MuleTrace AI — Multi-Rule Interaction & Severity Aggregation Tests.

Validates that evaluating complex transaction contexts correctly aggregates
scores additively, escalates severities strictly by hierarchy, and preserves all matches.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.engines.rules.engine import modular_rule_engine
from app.engines.rules.rule_engine import rule_engine


def test_multi_rule_trigger_score_and_pattern_aggregation():
    """Verify that multiple triggered rules sum their score contributions correctly."""
    now = datetime.now(timezone.utc)

    # 22 transactions in the past hour (triggers R001: +25, HIGH)
    recent_txns = [{"timestamp": now - timedelta(minutes=i)} for i in range(22)]

    # Transaction structured at ₹49,000 (triggers R005: +35, HIGH)
    tx = {
        "amount": 49000.0,
        "timestamp": now,
        "sender_account_id": "ACC-SND",
        "receiver_account_id": "ACC-REC",
    }

    # Linked devices = 4 (triggers R006: +35, HIGH)
    res = modular_rule_engine.evaluate(
        transaction=tx,
        recent_transactions=recent_txns,
        linked_devices_count=4,
    )

    matched_codes = {m.rule_code for m in res.matches}
    assert "R001" in matched_codes
    assert "R005" in matched_codes
    assert "R006" in matched_codes

    # Total score should be at least 25 + 35 + 35 = 95
    assert res.total_risk_score_delta >= 95
    assert "High Velocity" in res.flagged_patterns
    assert "Smurfing" in res.flagged_patterns
    assert "Shared Device" in res.flagged_patterns
    assert res.highest_severity == "HIGH"


def test_multi_rule_severity_escalation_to_critical():
    """Verify that a CRITICAL rule match elevates the aggregate highest_severity."""
    now = datetime.now(timezone.utc)

    # Inflow ₹100,000 within 5 mins, outgoing ₹98,000 (triggers R004: +40, CRITICAL)
    recent = [{"amount": 100000.0, "timestamp": now - timedelta(minutes=5)}]
    tx = {
        "amount": 98000.0,
        "timestamp": now,
        "channel": "UPI",
    }

    # Linked devices = 5 (triggers R006: +35, HIGH)
    res = rule_engine.evaluate(
        transaction=tx,
        recent_transactions=recent,
        linked_devices_count=5,
    )

    matched_codes = {m.rule_code for m in res.matches}
    assert "R004" in matched_codes
    assert "R006" in matched_codes

    # CRITICAL must supersede HIGH
    assert res.highest_severity == "CRITICAL"
    assert res.total_risk_score_delta >= 75


def test_multi_rule_medium_severity_resolution():
    """Verify that MEDIUM severity remains MEDIUM when no HIGH or CRITICAL rules match."""
    now = datetime.now(timezone.utc)

    # 3 payment rails in past hour (triggers R009: +25, MEDIUM)
    recent = [
        {"channel": "UPI", "timestamp": now - timedelta(minutes=10)},
        {"channel": "NEFT", "timestamp": now - timedelta(minutes=20)},
    ]
    tx = {
        "channel": "IMPS",
        "amount": 25000.0,  # Below smurfing threshold (no R005)
        "timestamp": now,
    }

    res = modular_rule_engine.evaluate(
        transaction=tx,
        recent_transactions=recent,
        linked_devices_count=1,  # Normal (no R006)
        linked_ips_count=1,      # Normal (no R010)
    )

    matched_codes = {m.rule_code for m in res.matches}
    assert "R009" in matched_codes
    assert res.highest_severity == "MEDIUM"


def test_zero_matches_returns_default_low_and_zero_delta():
    """Verify that benign transactions return 0 score delta and LOW severity."""
    now = datetime.now(timezone.utc)
    tx = {
        "amount": 1500.0,
        "channel": "UPI",
        "timestamp": datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc),  # Daytime
        "sender_account_id": "ACC-SND-1",
        "receiver_account_id": "ACC-REC-1",
    }

    res = rule_engine.evaluate(
        transaction=tx,
        sender_account={},
        recent_transactions=[],
        linked_devices_count=1,
        linked_ips_count=1,
    )

    assert res.total_risk_score_delta == 0
    assert len(res.matches) == 0
    assert len(res.flagged_patterns) == 0
    assert res.highest_severity == "LOW"
