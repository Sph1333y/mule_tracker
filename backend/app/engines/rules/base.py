"""
MuleTrace AI — Rule Engine Base Abstraction.

Defines the common contract for forensic rule evaluation (R001 - R014).
Provides RuleContext, RuleMatchResult, EvaluationResult, and BaseRule.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("app.engines.rules.base")


@dataclass
class RuleContext:
    """Unified context passed to each forensic rule during evaluation.

    Encapsulates the current transaction, sender account profile, historical
    recent transactions, and network linkage metrics.
    """

    transaction: dict[str, Any]
    sender_account: dict[str, Any] = field(default_factory=dict)
    recent_transactions: list[dict[str, Any]] = field(default_factory=list)
    linked_devices_count: int = 1
    linked_ips_count: int = 1


@dataclass
class RuleMatchResult:
    """Result payload from evaluating a single forensic rule."""

    rule_code: str
    rule_name: str
    pattern_name: str
    matched: bool
    score_contribution: int
    severity: str
    narrative: str


@dataclass
class EvaluationResult:
    """Aggregate result from evaluating active rules against a transaction context."""

    total_risk_score_delta: int
    matches: list[RuleMatchResult] = field(default_factory=list)
    flagged_patterns: list[str] = field(default_factory=list)
    highest_severity: str = "LOW"


class BaseRule(ABC):
    """Abstract base class for all forensic detection rules (R001 - R014)."""

    rule_code: str = ""
    rule_name: str = ""
    pattern_name: str = ""
    score_contribution: int = 0
    severity: str = "LOW"
    description: str = ""

    @abstractmethod
    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate the rule against the transaction context.

        Args:
            context: RuleContext containing transaction, account, history, and linkage data.

        Returns:
            RuleMatchResult with trigger state, score delta, and forensic narrative.
        """
        ...

    def _create_result(self, matched: bool, narrative: str = "") -> RuleMatchResult:
        """Helper to create a standardized RuleMatchResult from class attributes."""
        return RuleMatchResult(
            rule_code=self.rule_code,
            rule_name=self.rule_name,
            pattern_name=self.pattern_name,
            matched=matched,
            score_contribution=self.score_contribution if matched else 0,
            severity=self.severity if matched else "LOW",
            narrative=narrative if matched else "",
        )
