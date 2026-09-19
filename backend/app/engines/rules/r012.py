"""
MuleTrace AI — Rule R012: Night Activity Anomalies.

Flags high-value transactions (>₹50,000) occurring during nocturnal hours (12:00 AM to 05:00 AM).
"""

from __future__ import annotations

from datetime import datetime

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR012NightActivity(BaseRule):
    """R012: Check if high-value transaction occurred between 12:00 AM and 05:00 AM."""

    rule_code: str = "R012"
    rule_name: str = "Night Activity Anomalies"
    pattern_name: str = "Night Activity"
    score_contribution: int = 20
    severity: str = "MEDIUM"
    description: str = "Detects high-value transactions executed during non-standard nocturnal hours (12 AM - 5 AM)."

    NIGHT_START_HOUR: int = 0
    NIGHT_END_HOUR: int = 5
    HIGH_VALUE_THRESHOLD: float = 50000.0

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate anomalous night activity."""
        ts = context.transaction.get("timestamp")
        amount = float(context.transaction.get("amount", 0.0))
        flagged = context.transaction.get("is_night_anomaly", False)

        is_night_hours = False
        if isinstance(ts, datetime):
            is_night_hours = self.NIGHT_START_HOUR <= ts.hour < self.NIGHT_END_HOUR

        matched = bool(flagged) or (is_night_hours and amount >= self.HIGH_VALUE_THRESHOLD)
        narrative = (
            f"Night Activity anomaly detected: high-value transfer (₹{amount:,.2f}) executed between 12 AM and 5 AM."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
