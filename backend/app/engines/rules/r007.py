"""
MuleTrace AI — Rule R007: Dormant Account Reactivation.

Flags sudden activity or transfers originating from accounts dormant for >90 days.
"""

from __future__ import annotations

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR007DormantActivation(BaseRule):
    """R007: Check if account was dormant >90 days before sudden activity."""

    rule_code: str = "R007"
    rule_name: str = "Dormant Account Reactivation"
    pattern_name: str = "Dormant Reactivation"
    score_contribution: int = 30
    severity: str = "HIGH"
    description: str = "Detects sudden high-velocity activity on an account with zero transactions over preceding 90 days."

    DORMANT_DAYS_THRESHOLD: int = 90

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate dormant account reactivation."""
        is_dormant = context.sender_account.get("is_dormant", False)
        dormant_days = context.sender_account.get("dormant_days", 0)

        matched = bool(is_dormant) or (dormant_days > self.DORMANT_DAYS_THRESHOLD)
        narrative = (
            f"Dormant Account Reactivation detected: sudden activity on account dormant >{self.DORMANT_DAYS_THRESHOLD} days."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
