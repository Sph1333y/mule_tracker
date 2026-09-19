"""
MuleTrace AI — Rule Behavioral Parity Tests.

Compares outputs between the legacy RuleEngine interface and the new modular
rule classes, verifying zero behavioral deviation on golden test scenarios.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.engines.rules.base import RuleContext
from app.engines.rules.engine import modular_rule_engine
from app.engines.rules.r001 import RuleR001HighVelocity
from app.engines.rules.r002 import RuleR002FanIn
from app.engines.rules.r003 import RuleR003FanOut
from app.engines.rules.r004 import RuleR004MuleChain
from app.engines.rules.r005 import RuleR005Smurfing
from app.engines.rules.r006 import RuleR006SharedDevice
from app.engines.rules.rule_engine import RuleEngine, rule_engine


def test_r001_parity_high_velocity():
    """Verify R001 parity between legacy helper and modular rule."""
    now = datetime.now(timezone.utc)
    recent_txns = [{"timestamp": now - timedelta(minutes=i * 2)} for i in range(25)]

    legacy_engine = RuleEngine()
    legacy_res = legacy_engine._check_high_velocity(recent_txns)

    modular_rule = RuleR001HighVelocity()
    modular_res = modular_rule.evaluate(RuleContext(transaction={}, recent_transactions=recent_txns))

    assert legacy_res.rule_code == modular_res.rule_code == "R001"
    assert legacy_res.rule_name == modular_res.rule_name == "High Velocity Transactions"
    assert legacy_res.pattern_name == modular_res.pattern_name == "High Velocity"
    assert legacy_res.matched == modular_res.matched is True
    assert legacy_res.score_contribution == modular_res.score_contribution == 25
    assert legacy_res.severity == modular_res.severity == "HIGH"
    assert legacy_res.narrative == modular_res.narrative


def test_r002_parity_fan_in():
    """Verify R002 parity between legacy helper and modular rule."""
    rec_id = "REC-ACC-100"
    recent_txns = [{"sender_account_id": f"SND-{i}", "receiver_account_id": rec_id} for i in range(12)]

    legacy_engine = RuleEngine()
    legacy_res = legacy_engine._check_fan_in(recent_txns, rec_id)

    modular_rule = RuleR002FanIn()
    modular_res = modular_rule.evaluate(RuleContext(
        transaction={"receiver_account_id": rec_id},
        recent_transactions=recent_txns,
    ))

    assert legacy_res.rule_code == modular_res.rule_code == "R002"
    assert legacy_res.rule_name == modular_res.rule_name == "Fan-In Aggregation"
    assert legacy_res.pattern_name == modular_res.pattern_name == "Fan In"
    assert legacy_res.matched == modular_res.matched is True
    assert legacy_res.score_contribution == modular_res.score_contribution == 30
    assert legacy_res.severity == modular_res.severity == "HIGH"
    assert legacy_res.narrative == modular_res.narrative


def test_r003_parity_fan_out():
    """Verify R003 parity between legacy helper and modular rule."""
    snd_id = "SND-ACC-500"
    recent_txns = [{"sender_account_id": snd_id, "receiver_account_id": f"REC-{i}"} for i in range(15)]

    legacy_engine = RuleEngine()
    legacy_res = legacy_engine._check_fan_out(recent_txns, snd_id)

    modular_rule = RuleR003FanOut()
    modular_res = modular_rule.evaluate(RuleContext(
        transaction={"sender_account_id": snd_id},
        recent_transactions=recent_txns,
    ))

    assert legacy_res.rule_code == modular_res.rule_code == "R003"
    assert legacy_res.rule_name == modular_res.rule_name == "Fan-Out Dispersion"
    assert legacy_res.pattern_name == modular_res.pattern_name == "Fan Out"
    assert legacy_res.matched == modular_res.matched is True
    assert legacy_res.score_contribution == modular_res.score_contribution == 30
    assert legacy_res.severity == modular_res.severity == "HIGH"
    assert legacy_res.narrative == modular_res.narrative


def test_r004_parity_mule_chain():
    """Verify R004 parity between legacy helper and modular rule."""
    now = datetime.now(timezone.utc)
    recent_txns = [{"amount": 50000.0, "timestamp": now - timedelta(minutes=5)}]
    tx = {"amount": 48000.0, "timestamp": now}

    legacy_engine = RuleEngine()
    legacy_res = legacy_engine._check_mule_chain(tx, recent_txns)

    modular_rule = RuleR004MuleChain()
    modular_res = modular_rule.evaluate(RuleContext(transaction=tx, recent_transactions=recent_txns))

    assert legacy_res.rule_code == modular_res.rule_code == "R004"
    assert legacy_res.rule_name == modular_res.rule_name == "Mule Chain Rapid Pass-Through"
    assert legacy_res.pattern_name == modular_res.pattern_name == "Mule Chain"
    assert legacy_res.matched == modular_res.matched is True
    assert legacy_res.score_contribution == modular_res.score_contribution == 40
    assert legacy_res.severity == modular_res.severity == "CRITICAL"
    assert legacy_res.narrative == modular_res.narrative


def test_r005_parity_smurfing():
    """Verify R005 parity between legacy helper and modular rule."""
    tx = {"amount": 49000.0}

    legacy_engine = RuleEngine()
    legacy_res = legacy_engine._check_smurfing(tx)

    modular_rule = RuleR005Smurfing()
    modular_res = modular_rule.evaluate(RuleContext(transaction=tx))

    assert legacy_res.rule_code == modular_res.rule_code == "R005"
    assert legacy_res.rule_name == modular_res.rule_name == "Smurfing / Structuring"
    assert legacy_res.pattern_name == modular_res.pattern_name == "Smurfing"
    assert legacy_res.matched == modular_res.matched is True
    assert legacy_res.score_contribution == modular_res.score_contribution == 35
    assert legacy_res.severity == modular_res.severity == "HIGH"
    assert legacy_res.narrative == modular_res.narrative


def test_r006_parity_shared_device():
    """Verify R006 parity between legacy helper and modular rule."""
    legacy_engine = RuleEngine()
    legacy_res = legacy_engine._check_shared_device(4)

    modular_rule = RuleR006SharedDevice()
    modular_res = modular_rule.evaluate(RuleContext(transaction={}, linked_devices_count=4))

    assert legacy_res.rule_code == modular_res.rule_code == "R006"
    assert legacy_res.rule_name == modular_res.rule_name == "Shared Hardware Device"
    assert legacy_res.pattern_name == modular_res.pattern_name == "Shared Device"
    assert legacy_res.matched == modular_res.matched is True
    assert legacy_res.score_contribution == modular_res.score_contribution == 35
    assert legacy_res.severity == modular_res.severity == "HIGH"
    assert legacy_res.narrative == modular_res.narrative


def test_engine_facade_parity_on_single_rule_trigger():
    """Verify that calling rule_engine.evaluate triggers the exact expected match."""
    tx = {"amount": 49200.0}
    res = rule_engine.evaluate(transaction=tx)

    assert res.total_risk_score_delta == 35
    assert "Smurfing" in res.flagged_patterns
    assert res.highest_severity == "HIGH"
    matched_codes = [m.rule_code for m in res.matches]
    assert "R005" in matched_codes
