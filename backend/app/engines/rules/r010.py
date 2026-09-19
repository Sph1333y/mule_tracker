"""
MuleTrace AI — Rule R010: Shared IP Address Clustering.

Flags >5 accounts transacting from the same non-institutional public IP address.
"""

from __future__ import annotations

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR010SharedIP(BaseRule):
    """R010: Check if >5 accounts transacted from the same public IP address."""

    rule_code: str = "R010"
    rule_name: str = "Shared IP Address Clustering"
    pattern_name: str = "Shared IP"
    score_contribution: int = 30
    severity: str = "HIGH"
    description: str = "Detects >5 distinct customer accounts transacting from the same public IP address."

    MAX_ACCOUNTS_PER_IP_THRESHOLD: int = 5

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate shared IP clustering."""
        matched = context.linked_ips_count > self.MAX_ACCOUNTS_PER_IP_THRESHOLD
        narrative = (
            f"Shared IP pattern detected: public IP address linked to {context.linked_ips_count} accounts."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
