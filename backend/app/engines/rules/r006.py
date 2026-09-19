"""
MuleTrace AI — Rule R006: Shared Hardware Device.

Flags accounts accessed from a hardware device fingerprint shared by >3 accounts.
"""

from __future__ import annotations

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR006SharedDevice(BaseRule):
    """R006: Check if hardware device is shared by >3 accounts."""

    rule_code: str = "R006"
    rule_name: str = "Shared Hardware Device"
    pattern_name: str = "Shared Device"
    score_contribution: int = 35
    severity: str = "HIGH"
    description: str = "Detects hardware device fingerprints shared by more than 3 customer accounts."

    MAX_ACCOUNTS_THRESHOLD: int = 3

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate shared hardware device linkage."""
        matched = context.linked_devices_count > self.MAX_ACCOUNTS_THRESHOLD
        narrative = (
            f"Shared Device pattern detected: hardware fingerprint linked to {context.linked_devices_count} accounts."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
