"""
MuleTrace AI — Rule R009: Cross-Channel Hopping.

Flags rapid payment channel switching (>=3 rails e.g. UPI, NEFT, IMPS, RTGS) within 1 hour.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR009CrossChannel(BaseRule):
    """R009: Check if >=3 payment rails were cycled within 1 hour."""

    rule_code: str = "R009"
    rule_name: str = "Cross-Channel Hopping"
    pattern_name: str = "Cross-Channel Hopping"
    score_contribution: int = 25
    severity: str = "MEDIUM"
    description: str = "Detects rapid cycling across 3 or more distinct payment rails within a 1-hour window."

    CHANNELS_THRESHOLD: int = 3
    TIME_WINDOW_HOURS: int = 1

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate cross-channel hopping across recent transactions."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.TIME_WINDOW_HOURS)
        channels: set[str] = set()

        curr_ch = context.transaction.get("channel")
        if curr_ch:
            channels.add(curr_ch)

        for tx in context.recent_transactions:
            ts = tx.get("timestamp")
            ch = tx.get("channel")
            if ts and ts >= cutoff and ch:
                channels.add(ch)

        matched = len(channels) >= self.CHANNELS_THRESHOLD
        narrative = (
            f"Cross-Channel Hopping detected: cycling across {len(channels)} distinct rails within 1 hour."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
