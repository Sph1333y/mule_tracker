"""
MuleTrace AI — Rule R001: High Velocity Transactions.

Flags accounts with high transaction frequency (>20 transactions within a 1-hour window).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR001HighVelocity(BaseRule):
    """R001: Check if >20 transactions occurred in the last hour."""

    rule_code: str = "R001"
    rule_name: str = "High Velocity Transactions"
    pattern_name: str = "High Velocity"
    score_contribution: int = 25
    severity: str = "HIGH"
    description: str = "Detects >20 transactions from an account within a 1-hour rolling window."

    TIME_WINDOW_HOURS: int = 1
    TRANSACTION_THRESHOLD: int = 20

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate high transaction velocity over the past hour."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.TIME_WINDOW_HOURS)
        count = sum(
            1
            for tx in context.recent_transactions
            if tx.get("timestamp") and tx["timestamp"] >= cutoff
        )
        matched = count >= self.TRANSACTION_THRESHOLD
        narrative = (
            f"High velocity detected: {count} transactions executed in the past hour."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
