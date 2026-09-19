"""
MuleTrace AI — Rule Contract Tests.

Validates that all 14 forensic rules implement the BaseRule contract, have valid
metadata attributes, and can be evaluated independently with RuleContext.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult
from app.engines.rules.engine import DEFAULT_RULE_CLASSES
from app.engines.rules.r001 import RuleR001HighVelocity
from app.engines.rules.r002 import RuleR002FanIn
from app.engines.rules.r003 import RuleR003FanOut
from app.engines.rules.r004 import RuleR004MuleChain
from app.engines.rules.r005 import RuleR005Smurfing
from app.engines.rules.r006 import RuleR006SharedDevice
from app.engines.rules.r007 import RuleR007DormantActivation
from app.engines.rules.r008 import RuleR008NewAccountAbuse
from app.engines.rules.r009 import RuleR009CrossChannel
from app.engines.rules.r010 import RuleR010SharedIP
from app.engines.rules.r011 import RuleR011ImpossibleTravel
from app.engines.rules.r012 import RuleR012NightActivity
from app.engines.rules.r013 import RuleR013SharedBeneficiary
from app.engines.rules.r014 import RuleR014CircularFlow


@pytest.mark.parametrize("rule_class", DEFAULT_RULE_CLASSES)
def test_rule_class_contract(rule_class: type[BaseRule]):
    """Ensure all 14 rules fulfill BaseRule attributes and can be instantiated."""
    rule = rule_class()
    assert isinstance(rule, BaseRule)
    assert rule.rule_code.startswith("R")
    assert len(rule.rule_name) > 0
    assert len(rule.pattern_name) > 0
    assert rule.score_contribution > 0
    assert rule.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert len(rule.description) > 0

    # Test execution with an empty context
    empty_ctx = RuleContext(transaction={})
    res = rule.evaluate(empty_ctx)
    assert isinstance(res, RuleMatchResult)
    assert res.rule_code == rule.rule_code
    assert res.rule_name == rule.rule_name
    assert res.pattern_name == rule.pattern_name
    assert isinstance(res.matched, bool)
    assert isinstance(res.score_contribution, int)
    assert isinstance(res.severity, str)
    assert isinstance(res.narrative, str)


# -----------------------------------------------------------------------------
# Individual Rule Positive & Negative Tests
# -----------------------------------------------------------------------------

def test_r001_high_velocity_execution():
    rule = RuleR001HighVelocity()
    now = datetime.now(timezone.utc)

    # Negative: 5 txns in last hour (< 20)
    txns_5 = [{"timestamp": now - timedelta(minutes=i * 2)} for i in range(5)]
    res_neg = rule.evaluate(RuleContext(transaction={}, recent_transactions=txns_5))
    assert not res_neg.matched
    assert res_neg.score_contribution == 0

    # Positive: 22 txns in last hour (>= 20)
    txns_22 = [{"timestamp": now - timedelta(minutes=i * 2)} for i in range(22)]
    res_pos = rule.evaluate(RuleContext(transaction={}, recent_transactions=txns_22))
    assert res_pos.matched
    assert res_pos.score_contribution == 25
    assert res_pos.severity == "HIGH"
    assert "High velocity detected: 22 transactions" in res_pos.narrative


def test_r002_fan_in_execution():
    rule = RuleR002FanIn()
    target_rec = "ACC-COLLECTOR-1"

    # Negative: 4 senders (< 10)
    recent = [{"sender_account_id": f"SND-{i}", "receiver_account_id": target_rec} for i in range(4)]
    res_neg = rule.evaluate(RuleContext(transaction={"receiver_account_id": target_rec}, recent_transactions=recent))
    assert not res_neg.matched
    assert res_neg.score_contribution == 0

    # Positive: 12 senders (>= 10)
    recent_12 = [{"sender_account_id": f"SND-{i}", "receiver_account_id": target_rec} for i in range(12)]
    res_pos = rule.evaluate(RuleContext(transaction={"receiver_account_id": target_rec}, recent_transactions=recent_12))
    assert res_pos.matched
    assert res_pos.score_contribution == 30
    assert res_pos.severity == "HIGH"
    assert "Fan-In Collector detected: 12 unique senders" in res_pos.narrative


def test_r003_fan_out_execution():
    rule = RuleR003FanOut()
    distributor = "ACC-DIST-1"

    # Negative: 3 receivers (< 10)
    recent = [{"sender_account_id": distributor, "receiver_account_id": f"REC-{i}"} for i in range(3)]
    res_neg = rule.evaluate(RuleContext(transaction={"sender_account_id": distributor}, recent_transactions=recent))
    assert not res_neg.matched
    assert res_neg.score_contribution == 0

    # Positive: 11 receivers (>= 10)
    recent_11 = [{"sender_account_id": distributor, "receiver_account_id": f"REC-{i}"} for i in range(11)]
    res_pos = rule.evaluate(RuleContext(transaction={"sender_account_id": distributor}, recent_transactions=recent_11))
    assert res_pos.matched
    assert res_pos.score_contribution == 30
    assert res_pos.severity == "HIGH"
    assert "Fan-Out Distributor detected" in res_pos.narrative


def test_r004_mule_chain_execution():
    rule = RuleR004MuleChain()
    now = datetime.now(timezone.utc)

    # Inflow of ₹100,000 within last 10 minutes
    recent = [{"amount": 100000.0, "timestamp": now - timedelta(minutes=5)}]

    # Negative: Outflow ₹50,000 (50% < 90%)
    tx_50k = {"amount": 50000.0, "timestamp": now}
    res_neg = rule.evaluate(RuleContext(transaction=tx_50k, recent_transactions=recent))
    assert not res_neg.matched
    assert res_neg.score_contribution == 0

    # Positive: Outflow ₹95,000 (95% >= 90%)
    tx_95k = {"amount": 95000.0, "timestamp": now}
    res_pos = rule.evaluate(RuleContext(transaction=tx_95k, recent_transactions=recent))
    assert res_pos.matched
    assert res_pos.score_contribution == 40
    assert res_pos.severity == "CRITICAL"
    assert "Mule Chain Pass-Through detected" in res_pos.narrative


def test_r005_smurfing_execution():
    rule = RuleR005Smurfing()

    # Negative: ₹10,000 and ₹50,000
    res_low = rule.evaluate(RuleContext(transaction={"amount": 10000.0}))
    assert not res_low.matched
    res_exact_50k = rule.evaluate(RuleContext(transaction={"amount": 50000.0}))
    assert not res_exact_50k.matched

    # Positive: ₹49,500
    res_pos = rule.evaluate(RuleContext(transaction={"amount": 49500.0}))
    assert res_pos.matched
    assert res_pos.score_contribution == 35
    assert res_pos.severity == "HIGH"
    assert "Smurfing / Structuring detected" in res_pos.narrative


def test_r006_shared_device_execution():
    rule = RuleR006SharedDevice()

    # Negative: 2 accounts (<= 3)
    res_neg = rule.evaluate(RuleContext(transaction={}, linked_devices_count=2))
    assert not res_neg.matched

    # Positive: 4 accounts (> 3)
    res_pos = rule.evaluate(RuleContext(transaction={}, linked_devices_count=4))
    assert res_pos.matched
    assert res_pos.score_contribution == 35
    assert res_pos.severity == "HIGH"
    assert "Shared Device pattern detected: hardware fingerprint linked to 4 accounts" in res_pos.narrative


def test_r007_dormant_activation_execution():
    rule = RuleR007DormantActivation()

    # Negative: Active account
    res_neg = rule.evaluate(RuleContext(transaction={"amount": 60000.0}, sender_account={"is_dormant": False, "dormant_days": 10}))
    assert not res_neg.matched

    # Positive: Dormant >90 days
    res_pos = rule.evaluate(RuleContext(transaction={"amount": 60000.0}, sender_account={"dormant_days": 120}))
    assert res_pos.matched
    assert res_pos.score_contribution == 30
    assert res_pos.severity == "HIGH"
    assert "Dormant Account Reactivation detected" in res_pos.narrative


def test_r008_new_account_abuse_execution():
    rule = RuleR008NewAccountAbuse()

    # Negative: Account age 30 days (> 7 days)
    recent_18 = [{"id": i} for i in range(18)]
    res_neg = rule.evaluate(RuleContext(transaction={}, sender_account={"account_age_days": 30}, recent_transactions=recent_18))
    assert not res_neg.matched

    # Positive: Account age 3 days (< 7 days) with 18 transactions (> 15)
    res_pos = rule.evaluate(RuleContext(transaction={}, sender_account={"account_age_days": 3}, recent_transactions=recent_18))
    assert res_pos.matched
    assert res_pos.score_contribution == 25
    assert res_pos.severity == "HIGH"
    assert "New Account Abuse detected" in res_pos.narrative


def test_r009_cross_channel_execution():
    rule = RuleR009CrossChannel()
    now = datetime.now(timezone.utc)

    # Negative: 2 channels (UPI and NEFT)
    recent_2 = [
        {"channel": "UPI", "timestamp": now - timedelta(minutes=10)},
        {"channel": "NEFT", "timestamp": now - timedelta(minutes=20)},
    ]
    res_neg = rule.evaluate(RuleContext(transaction={"channel": "UPI"}, recent_transactions=recent_2))
    assert not res_neg.matched

    # Positive: 3 channels (UPI, NEFT, IMPS) within 1 hour
    recent_3 = [
        {"channel": "UPI", "timestamp": now - timedelta(minutes=10)},
        {"channel": "NEFT", "timestamp": now - timedelta(minutes=20)},
    ]
    res_pos = rule.evaluate(RuleContext(transaction={"channel": "IMPS"}, recent_transactions=recent_3))
    assert res_pos.matched
    assert res_pos.score_contribution == 25
    assert res_pos.severity == "MEDIUM"
    assert "Cross-Channel Hopping detected" in res_pos.narrative


def test_r010_shared_ip_execution():
    rule = RuleR010SharedIP()

    # Negative: 3 accounts (<= 5)
    res_neg = rule.evaluate(RuleContext(transaction={}, linked_ips_count=3))
    assert not res_neg.matched

    # Positive: 7 accounts (> 5)
    res_pos = rule.evaluate(RuleContext(transaction={}, linked_ips_count=7))
    assert res_pos.matched
    assert res_pos.score_contribution == 30
    assert res_pos.severity == "HIGH"
    assert "Shared IP pattern detected" in res_pos.narrative


def test_r011_impossible_travel_execution():
    rule = RuleR011ImpossibleTravel()

    # Negative: normal speed
    res_neg = rule.evaluate(RuleContext(transaction={"travel_speed_kmh": 60.0}))
    assert not res_neg.matched

    # Positive: 800 km/h (> 500 km/h)
    res_pos = rule.evaluate(RuleContext(transaction={"travel_speed_kmh": 850.0}))
    assert res_pos.matched
    assert res_pos.score_contribution == 35
    assert res_pos.severity == "HIGH"
    assert "Impossible Travel detected" in res_pos.narrative


def test_r012_night_activity_execution():
    rule = RuleR012NightActivity()

    # Negative: 2:00 PM (14:00) with ₹80,000
    day_ts = datetime(2026, 9, 19, 14, 30, tzinfo=timezone.utc)
    res_neg = rule.evaluate(RuleContext(transaction={"timestamp": day_ts, "amount": 80000.0}))
    assert not res_neg.matched

    # Positive: 2:30 AM with ₹75,000
    night_ts = datetime(2026, 9, 19, 2, 30, tzinfo=timezone.utc)
    res_pos = rule.evaluate(RuleContext(transaction={"timestamp": night_ts, "amount": 75000.0}))
    assert res_pos.matched
    assert res_pos.score_contribution == 20
    assert res_pos.severity == "MEDIUM"
    assert "Night Activity anomaly detected" in res_pos.narrative


def test_r013_shared_beneficiary_execution():
    rule = RuleR013SharedBeneficiary()

    # Negative: 2 accounts sharing beneficiary (< 5)
    res_neg = rule.evaluate(RuleContext(transaction={"beneficiary_linked_accounts_count": 2}))
    assert not res_neg.matched

    # Positive: 6 accounts sharing beneficiary (>= 5)
    res_pos = rule.evaluate(RuleContext(transaction={"beneficiary_linked_accounts_count": 6}))
    assert res_pos.matched
    assert res_pos.score_contribution == 30
    assert res_pos.severity == "HIGH"
    assert "Shared Beneficiary detected" in res_pos.narrative


def test_r014_circular_flow_execution():
    rule = RuleR014CircularFlow()

    # Negative: Linear transaction
    res_neg = rule.evaluate(RuleContext(transaction={"sender_account_id": "A", "receiver_account_id": "B"}))
    assert not res_neg.matched

    # Positive: Circular cycle detected in path
    res_pos = rule.evaluate(RuleContext(transaction={
        "sender_account_id": "ACC-ORIGIN",
        "receiver_account_id": "ACC-NODE-3",
        "cycle_path": ["ACC-NODE-1", "ACC-NODE-2", "ACC-ORIGIN"],
    }))
    assert res_pos.matched
    assert res_pos.score_contribution == 40
    assert res_pos.severity == "CRITICAL"
    assert "Circular Flow detected" in res_pos.narrative
