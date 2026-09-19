"""
MuleTrace AI — Rule R002: Fan-In Aggregation.

Flags collector accounts receiving funds from >10 unique remitters within 24 hours.
"""

from __future__ import annotations

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR002FanIn(BaseRule):
    """R002: Check if >10 unique senders transferred to 1 collector account in 24 hours."""

    rule_code: str = "R002"
    rule_name: str = "Fan-In Aggregation"
    pattern_name: str = "Fan In"
    score_contribution: int = 30
    severity: str = "HIGH"
    description: str = "Detects >10 unique senders transferring funds into a single collector account within 24 hours."

    UNIQUE_SENDERS_THRESHOLD: int = 10

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate fan-in aggregation against receiver account."""
        receiver_id = context.transaction.get("receiver_account_id")
        if not receiver_id:
            return self._create_result(matched=False, narrative="")

        senders = {
            tx.get("sender_account_id")
            for tx in context.recent_transactions
            if tx.get("receiver_account_id") == receiver_id
        }
        matched = len(senders) >= self.UNIQUE_SENDERS_THRESHOLD
        narrative = (
            f"Fan-In Collector detected: {len(senders)} unique senders transferred to account."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
