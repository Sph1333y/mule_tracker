"""
MuleTrace AI — Forensic Detection Rule Engine Package.

Provides modular, decoupled fraud rules (R001 - R014), rule registry,
and backward-compatible evaluation engine facade.
"""

from __future__ import annotations

from app.engines.rules.base import (
    BaseRule,
    EvaluationResult,
    RuleContext,
    RuleMatchResult,
)
from app.engines.rules.engine import (
    DEFAULT_RULE_CLASSES,
    ModularRuleEngine,
    modular_rule_engine,
)
from app.engines.rules.r001 import RuleR001HighVelocity
from app.engines.rules.r002 import RuleR002FanIn
from app.engines.rules.r003 import RuleR003FanOut
from app.engines.rules.r004 import RuleR004MuleChain
from app.engines.rules.r005 import RuleR005Smurfing
from app.engines.rules.r006 import RuleR006SharedDevice
from app.engines.rules.r007 import RuleR007DormantActivation
from app.engines.rules.r008 import RuleR008NewAccountAbuse
from app.engines.rules.r009 import RuleR009CrossChannel
from app.engines.rules.r010 import RuleR010SharedIP
from app.engines.rules.r011 import RuleR011ImpossibleTravel
from app.engines.rules.r012 import RuleR012NightActivity
from app.engines.rules.r013 import RuleR013SharedBeneficiary
from app.engines.rules.r014 import RuleR014CircularFlow
from app.engines.rules.rule_engine import RuleEngine, rule_engine

__all__ = [
    # Base Abstractions
    "BaseRule",
    "RuleContext",
    "RuleMatchResult",
    "EvaluationResult",
    # Modular Engine & Registry
    "DEFAULT_RULE_CLASSES",
    "ModularRuleEngine",
    "modular_rule_engine",
    # Backward Compatibility Layer
    "RuleEngine",
    "rule_engine",
    # Forensic Rules
    "RuleR001HighVelocity",
    "RuleR002FanIn",
    "RuleR003FanOut",
    "RuleR004MuleChain",
    "RuleR005Smurfing",
    "RuleR006SharedDevice",
    "RuleR007DormantActivation",
    "RuleR008NewAccountAbuse",
    "RuleR009CrossChannel",
    "RuleR010SharedIP",
    "RuleR011ImpossibleTravel",
    "RuleR012NightActivity",
    "RuleR013SharedBeneficiary",
    "RuleR014CircularFlow",
]
