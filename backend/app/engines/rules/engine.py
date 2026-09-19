"""
MuleTrace AI — Modular Rule Engine & Registry.

Coordinates deterministic execution of forensic detection rules (R001 - R014).
Provides rule registration, isolated rule execution, and aggregate evaluation.
"""

from __future__ import annotations

import logging
from typing import Any

from app.engines.rules.base import BaseRule, EvaluationResult, RuleContext, RuleMatchResult
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

logger = logging.getLogger("app.engines.rules.engine")

# Canonical deterministic list of all 14 forensic rules in sequence
DEFAULT_RULE_CLASSES: list[type[BaseRule]] = [
    RuleR001HighVelocity,
    RuleR002FanIn,
    RuleR003FanOut,
    RuleR004MuleChain,
    RuleR005Smurfing,
    RuleR006SharedDevice,
    RuleR007DormantActivation,
    RuleR008NewAccountAbuse,
    RuleR009CrossChannel,
    RuleR010SharedIP,
    RuleR011ImpossibleTravel,
    RuleR012NightActivity,
    RuleR013SharedBeneficiary,
    RuleR014CircularFlow,
]


class ModularRuleEngine:
    """Deterministic, modular rule evaluation engine for R001 - R014."""

    def __init__(self, rules: list[BaseRule] | None = None) -> None:
        """Initialize the rule engine with default or custom rules.

        Args:
            rules: Optional list of BaseRule instances. If None, instantiates DEFAULT_RULE_CLASSES.
        """
        self._rules: dict[str, BaseRule] = {}
        if rules is not None:
            for r in rules:
                self.register_rule(r)
        else:
            for cls in DEFAULT_RULE_CLASSES:
                self.register_rule(cls())

    def register_rule(self, rule: BaseRule) -> None:
        """Register a single rule instance in the engine."""
        self._rules[rule.rule_code] = rule

    def get_rule(self, rule_code: str) -> BaseRule | None:
        """Retrieve a registered rule instance by its rule code."""
        return self._rules.get(rule_code)

    def list_rules(self) -> list[BaseRule]:
        """Return all registered rules in deterministic order."""
        return list(self._rules.values())

    def evaluate_rule(self, rule_code: str, context: RuleContext) -> RuleMatchResult | None:
        """Evaluate a single rule in isolation."""
        rule = self._rules.get(rule_code)
        if not rule:
            return None
        return rule.evaluate(context)

    def evaluate(
        self,
        transaction: dict[str, Any],
        sender_account: dict[str, Any] | None = None,
        recent_transactions: list[dict[str, Any]] | None = None,
        linked_devices_count: int = 1,
        linked_ips_count: int = 1,
        active_rule_codes: set[str] | list[str] | None = None,
    ) -> EvaluationResult:
        """Evaluate rules against the given transaction context.

        Args:
            transaction: Transaction dictionary (amount, channel, timestamp, location, etc.)
            sender_account: Sender account state (risk_score, balance, opened_at, etc.)
            recent_transactions: Recent transactions for velocity calculation.
            linked_devices_count: Number of accounts sharing the same device.
            linked_ips_count: Number of accounts sharing the same IP address.
            active_rule_codes: Optional whitelist of rule codes to evaluate. If None, evaluates all.

        Returns:
            EvaluationResult detailing rule matches, aggregate score delta, and highest severity.
        """
        context = RuleContext(
            transaction=transaction,
            sender_account=sender_account or {},
            recent_transactions=recent_transactions or [],
            linked_devices_count=linked_devices_count,
            linked_ips_count=linked_ips_count,
        )

        matches: list[RuleMatchResult] = []
        patterns: set[str] = set()
        total_score_delta = 0

        filter_set = set(active_rule_codes) if active_rule_codes is not None else None

        for rule in self._rules.values():
            if filter_set is not None and rule.rule_code not in filter_set:
                continue

            res = rule.evaluate(context)
            if res.matched:
                matches.append(res)
                patterns.add(res.pattern_name)
                total_score_delta += res.score_contribution

        # Determine highest severity among matches
        highest_severity = "LOW"
        for m in matches:
            if m.severity == "CRITICAL":
                highest_severity = "CRITICAL"
                break
            elif m.severity == "HIGH" and highest_severity != "CRITICAL":
                highest_severity = "HIGH"
            elif m.severity == "MEDIUM" and highest_severity not in ("HIGH", "CRITICAL"):
                highest_severity = "MEDIUM"

        return EvaluationResult(
            total_risk_score_delta=total_score_delta,
            matches=matches,
            flagged_patterns=list(patterns),
            highest_severity=highest_severity,
        )


# Singleton modular engine instance
modular_rule_engine = ModularRuleEngine()
