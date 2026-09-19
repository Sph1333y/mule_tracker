"""
MuleTrace AI — Rule R013: Shared Beneficiary Convergence.

Flags multiple unrelated accounts (>5) transferring funds into the same destination beneficiary.
"""

from __future__ import annotations

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR013SharedBeneficiary(BaseRule):
    """R013: Check if destination beneficiary is shared by >=5 unrelated accounts."""

    rule_code: str = "R013"
    rule_name: str = "Shared Beneficiary Convergence"
    pattern_name: str = "Shared Beneficiary"
    score_contribution: int = 30
    severity: str = "HIGH"
    description: str = "Detects multiple unrelated accounts transferring to the identical beneficiary account."

    MIN_LINKED_ACCOUNTS_THRESHOLD: int = 5

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate shared beneficiary convergence."""
        count = int(context.transaction.get("beneficiary_linked_accounts_count", 1))
        flagged = context.transaction.get("is_shared_beneficiary", False)

        matched = bool(flagged) or (count >= self.MIN_LINKED_ACCOUNTS_THRESHOLD)
        narrative = (
            f"Shared Beneficiary detected: beneficiary account shared by {count} unrelated accounts."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
