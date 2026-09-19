"""
MuleTrace AI — Rule Registry Tests.

Validates the deterministic rule registry, ensuring completeness of R001 - R014,
uniqueness of rule codes, correct ordering, and registry lookup methods.
"""

from __future__ import annotations

from app.engines.rules.base import BaseRule, RuleContext
from app.engines.rules.engine import (
    DEFAULT_RULE_CLASSES,
    ModularRuleEngine,
    modular_rule_engine,
)


def test_registry_completeness():
    """Verify that exactly 14 rules are configured in the default rule classes."""
    assert len(DEFAULT_RULE_CLASSES) == 14

    expected_codes = [f"R{i:03d}" for i in range(1, 15)]
    instantiated_rules = [cls() for cls in DEFAULT_RULE_CLASSES]
    actual_codes = [r.rule_code for r in instantiated_rules]

    assert actual_codes == expected_codes


def test_registry_unique_rule_codes():
    """Verify that every rule code in the engine is unique."""
    engine = ModularRuleEngine()
    rules = engine.list_rules()
    assert len(rules) == 14

    codes = [r.rule_code for r in rules]
    assert len(codes) == len(set(codes)), "Duplicate rule code detected in registry!"


def test_registry_lookup_and_retrieval():
    """Verify get_rule retrieves the correct rule instance by rule_code."""
    engine = ModularRuleEngine()

    for i in range(1, 15):
        code = f"R{i:03d}"
        rule = engine.get_rule(code)
        assert rule is not None
        assert isinstance(rule, BaseRule)
        assert rule.rule_code == code

    # Non-existent code returns None
    assert engine.get_rule("R999") is None


def test_registry_evaluate_rule_isolation():
    """Verify evaluate_rule evaluates an individual rule by its code."""
    engine = ModularRuleEngine()
    ctx = RuleContext(transaction={"amount": 49500.0})

    # R005 triggers on 49500
    res_r5 = engine.evaluate_rule("R005", ctx)
    assert res_r5 is not None
    assert res_r5.rule_code == "R005"
    assert res_r5.matched is True

    # R006 does not trigger on default linked_devices_count = 1
    res_r6 = engine.evaluate_rule("R006", ctx)
    assert res_r6 is not None
    assert res_r6.rule_code == "R006"
    assert res_r6.matched is False

    # Unknown rule code returns None
    assert engine.evaluate_rule("R999", ctx) is None


def test_singleton_registry():
    """Verify that the module singleton modular_rule_engine is fully initialized."""
    assert modular_rule_engine is not None
    assert len(modular_rule_engine.list_rules()) == 14
