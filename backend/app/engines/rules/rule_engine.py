"""
MuleTrace AI — Rule Engine (Compatibility Layer).

Preserves the existing public interface of RuleEngine while delegating execution
to the new modular, decoupled rule engine architecture (R001 - R014).
Ensures 100% backward compatibility for existing services, tests, and APIs.
"""

from __future__ import annotations

import logging
from typing import Any

from app.engines.rules.base import (
    EvaluationResult,
    RuleContext,
    RuleMatchResult,
)
from app.engines.rules.engine import ModularRuleEngine, modular_rule_engine
from app.engines.rules.r001 import RuleR001HighVelocity
from app.engines.rules.r002 import RuleR002FanIn
from app.engines.rules.r003 import RuleR003FanOut
from app.engines.rules.r004 import RuleR004MuleChain
from app.engines.rules.r005 import RuleR005Smurfing
from app.engines.rules.r006 import RuleR006SharedDevice

logger = logging.getLogger("app.engines.rules.rule_engine")

# Re-export for backward compatibility
__all__ = [
    "RuleMatchResult",
    "EvaluationResult",
    "RuleEngine",
    "rule_engine",
]


class RuleEngine:
    """Backward-compatible facade delegating to the modular rule engine (R001 - R014)."""

    def __init__(self, engine: ModularRuleEngine | None = None) -> None:
        self._modular_engine = engine or modular_rule_engine
        # Cached rule instances for legacy direct helper methods
        self._r1 = RuleR001HighVelocity()
        self._r2 = RuleR002FanIn()
        self._r3 = RuleR003FanOut()
        self._r4 = RuleR004MuleChain()
        self._r5 = RuleR005Smurfing()
        self._r6 = RuleR006SharedDevice()

    def evaluate(
        self,
        transaction: dict[str, Any],
        sender_account: dict[str, Any] | None = None,
        recent_transactions: list[dict[str, Any]] | None = None,
        linked_devices_count: int = 1,
        linked_ips_count: int = 1,
        active_rule_codes: set[str] | list[str] | None = None,
    ) -> EvaluationResult:
        """Evaluate rules against the given transaction context.

        Delegates to the modular rule engine while preserving identical signature,
        return type, and behavior.
        """
        return self._modular_engine.evaluate(
            transaction=transaction,
            sender_account=sender_account or {},
            recent_transactions=recent_transactions or [],
            linked_devices_count=linked_devices_count,
            linked_ips_count=linked_ips_count,
            active_rule_codes=active_rule_codes,
        )

    def _check_high_velocity(self, recent_txns: list[dict[str, Any]]) -> RuleMatchResult:
        """Legacy helper: R001 velocity evaluation."""
        ctx = RuleContext(transaction={}, recent_transactions=recent_txns)
        return self._r1.evaluate(ctx)

    def _check_fan_in(self, recent_txns: list[dict[str, Any]], receiver_id: Any) -> RuleMatchResult:
        """Legacy helper: R002 fan-in evaluation."""
        ctx = RuleContext(transaction={"receiver_account_id": receiver_id}, recent_transactions=recent_txns)
        return self._r2.evaluate(ctx)

    def _check_fan_out(self, recent_txns: list[dict[str, Any]], sender_id: Any) -> RuleMatchResult:
        """Legacy helper: R003 fan-out evaluation."""
        ctx = RuleContext(transaction={"sender_account_id": sender_id}, recent_transactions=recent_txns)
        return self._r3.evaluate(ctx)

    def _check_mule_chain(self, tx: dict[str, Any], recent_txns: list[dict[str, Any]]) -> RuleMatchResult:
        """Legacy helper: R004 mule chain rapid pass-through evaluation."""
        ctx = RuleContext(transaction=tx, recent_transactions=recent_txns)
        return self._r4.evaluate(ctx)

    def _check_smurfing(self, tx: dict[str, Any]) -> RuleMatchResult:
        """Legacy helper: R005 smurfing / structuring evaluation."""
        ctx = RuleContext(transaction=tx)
        return self._r5.evaluate(ctx)

    def _check_shared_device(self, linked_count: int) -> RuleMatchResult:
        """Legacy helper: R006 shared hardware device evaluation."""
        ctx = RuleContext(transaction={}, linked_devices_count=linked_count)
        return self._r6.evaluate(ctx)


# Singleton instance for backward compatibility
rule_engine = RuleEngine()
