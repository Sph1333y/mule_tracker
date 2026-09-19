"""
MuleTrace AI — Rule R005: Smurfing / Structuring.

Flags transactions structured between ₹48,000 and ₹49,999 to evade reporting thresholds.
"""

from __future__ import annotations

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR005Smurfing(BaseRule):
    """R005: Check if transaction amount is structured between ₹48,000 and ₹49,999 to bypass reporting."""

    rule_code: str = "R005"
    rule_name: str = "Smurfing / Structuring"
    pattern_name: str = "Smurfing"
    score_contribution: int = 35
    severity: str = "HIGH"
    description: str = "Detects structured transactions between ₹48,000 and ₹49,999 to evade statutory CTR thresholds."

    MIN_AMOUNT: float = 48000.0
    MAX_AMOUNT: float = 49999.0

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate smurfing / structuring threshold evasion."""
        amount = context.transaction.get("amount", 0.0)
        matched = self.MIN_AMOUNT <= amount <= self.MAX_AMOUNT
        narrative = (
            f"Smurfing / Structuring detected: transfer of ₹{amount:,.2f} just under reporting threshold."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
