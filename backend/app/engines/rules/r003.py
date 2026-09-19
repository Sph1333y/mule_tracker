"""
MuleTrace AI — Rule R003: Fan-Out Dispersion.

Flags distributor accounts scattering funds to >10 unique receivers within 24 hours.
"""

from __future__ import annotations

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR003FanOut(BaseRule):
    """R003: Check if 1 distributor sent to >10 unique receivers in 24 hours."""

    rule_code: str = "R003"
    rule_name: str = "Fan-Out Dispersion"
    pattern_name: str = "Fan Out"
    score_contribution: int = 30
    severity: str = "HIGH"
    description: str = "Detects 1 distributor dispersing funds to >10 unique receiver accounts within 24 hours."

    UNIQUE_RECEIVERS_THRESHOLD: int = 10

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate fan-out dispersion against sender account."""
        sender_id = context.transaction.get("sender_account_id")
        if not sender_id:
            return self._create_result(matched=False, narrative="")

        receivers = {
            tx.get("receiver_account_id")
            for tx in context.recent_transactions
            if tx.get("sender_account_id") == sender_id
        }
        matched = len(receivers) >= self.UNIQUE_RECEIVERS_THRESHOLD
        narrative = (
            f"Fan-Out Distributor detected: funds scattered to {len(receivers)} receivers."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
