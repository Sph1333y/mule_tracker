"""
MuleTrace AI — Rule R014: Circular Flow / Wash Laundering.

Flags circular transaction topologies where funds traverse intermediate accounts and return to the originator.
"""

from __future__ import annotations

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR014CircularFlow(BaseRule):
    """R014: Check if transaction is part of a circular flow returning to the originating account."""

    rule_code: str = "R014"
    rule_name: str = "Circular Flow / Wash Laundering"
    pattern_name: str = "Circular Flow"
    score_contribution: int = 40
    severity: str = "CRITICAL"
    description: str = "Detects directed cycles where transferred funds return to the originator within intermediate hops."

    MAX_HOPS_THRESHOLD: int = 5

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate circular flow topology indicators."""
        flagged = context.transaction.get("has_circular_flow", False) or context.transaction.get(
            "circular_flow_detected", False
        )
        sender_id = context.transaction.get("sender_account_id")
        receiver_id = context.transaction.get("receiver_account_id")

        cycle_path = context.transaction.get("cycle_path") or []
        is_in_path = sender_id and (sender_id in cycle_path or (sender_id == receiver_id))

        matched = bool(flagged) or bool(is_in_path)
        narrative = (
            "Circular Flow detected: funds traverse intermediate accounts and return to originator."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
