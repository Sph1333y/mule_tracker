"""
MuleTrace AI — Rule R008: New Account Abuse.

Flags high transaction frequency (>15 txns) on accounts created <7 days ago.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR008NewAccountAbuse(BaseRule):
    """R008: Check if account created <7 days ago exhibits high transaction volume (>15 txns)."""

    rule_code: str = "R008"
    rule_name: str = "New Account Abuse"
    pattern_name: str = "New Account Abuse"
    score_contribution: int = 25
    severity: str = "HIGH"
    description: str = "Detects unusually high transaction frequency (>15 txns) on accounts created <7 days ago."

    ACCOUNT_AGE_DAYS_THRESHOLD: int = 7
    TRANSACTION_COUNT_THRESHOLD: int = 15

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate new account abuse velocity."""
        account_age = context.sender_account.get("account_age_days")
        if account_age is None and context.sender_account.get("opened_at"):
            opened = context.sender_account["opened_at"]
            if isinstance(opened, datetime):
                account_age = (datetime.now(timezone.utc) - opened).days

        tx_count = len(context.recent_transactions)
        matched = (
            account_age is not None
            and account_age < self.ACCOUNT_AGE_DAYS_THRESHOLD
            and tx_count > self.TRANSACTION_COUNT_THRESHOLD
        )
        narrative = (
            f"New Account Abuse detected: {tx_count} transactions on account created {account_age} days ago (<7 days)."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
