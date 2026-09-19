"""
MuleTrace AI — Rule R011: Impossible Travel Velocity.

Flags successive transactions between distinct locations with implied physical transit speed >500 km/h.
"""

from __future__ import annotations

from app.engines.rules.base import BaseRule, RuleContext, RuleMatchResult


class RuleR011ImpossibleTravel(BaseRule):
    """R011: Check if implied transit speed between successive transactions exceeds 500 km/h."""

    rule_code: str = "R011"
    rule_name: str = "Impossible Travel Velocity"
    pattern_name: str = "Impossible Travel"
    score_contribution: int = 35
    severity: str = "HIGH"
    description: str = "Detects successive transactions with physical transit velocity exceeding 500 km/h."

    SPEED_THRESHOLD_KMH: float = 500.0

    def evaluate(self, context: RuleContext) -> RuleMatchResult:
        """Evaluate impossible geospatial velocity."""
        flagged = context.transaction.get("impossible_travel", False)
        speed = float(context.transaction.get("travel_speed_kmh", 0.0))

        matched = bool(flagged) or (speed > self.SPEED_THRESHOLD_KMH)
        narrative = (
            "Impossible Travel detected: physical transit speed between transactions exceeds 500 km/h."
            if matched
            else ""
        )
        return self._create_result(matched=matched, narrative=narrative)
