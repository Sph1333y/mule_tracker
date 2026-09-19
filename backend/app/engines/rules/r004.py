"""
MuleTrace AI — Rule R004: Mule Chain Rapid Pass-Through.

Flags rapid pass-through layering where >90% of funds received are forwarded within 15 minutes.
"""

from __future__ import annotations

from datetime import timedelta

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR004MuleChain(BaseRule):
    """R004: Check if >90% of incoming amount was transferred out within 15 minutes."""

    rule_code: str = "R004"
    rule_name: str = "Mule Chain Rapid Pass-Through"
    pattern_name: str = "Mule Chain"
    score_contribution: int = 40
    severity: str = "CRITICAL"
    description: str = "Detects >90% of received funds transferred out to a subsequent node within 15 minutes."

    WINDOW_MINUTES: int = 15
    PASS_THROUGH_RATIO_THRESHOLD: float = 0.90

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate rapid pass-through mule chain velocity."""
        amount = context.transaction.get("amount", 0.0)
        timestamp = context.transaction.get("timestamp")
        if not timestamp or amount <= 0:
            return self._create_result(matched=False, narrative="")

        cutoff = timestamp - timedelta(minutes=self.WINDOW_MINUTES)
        incoming_sum = sum(
            t.get("amount", 0.0)
            for t in context.recent_transactions
            if t.get("timestamp") and cutoff <= t["timestamp"] <= timestamp
        )

        matched = incoming_sum > 0 and (amount / incoming_sum) >= self.PASS_THROUGH_RATIO_THRESHOLD
        narrative = (
            f"Mule Chain Pass-Through detected: >90% of funds (₹{amount:,.2f}) forwarded within 15 minutes."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
