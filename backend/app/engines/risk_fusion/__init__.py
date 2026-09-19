"""
MuleTrace AI — Risk Fusion Engine Package.

Provides multi-modal risk signal synthesis, configurable weighting, missing signal
handling, and deterministic risk tier classification (Milestone 10).
"""

from __future__ import annotations

from app.engines.risk_fusion.models import (
    FusionInput,
    FusionResult,
    MissingSignalPolicy,
    NormalizedSignal,
    RiskLevel,
    SignalContribution,
    SignalModality,
)
from app.engines.risk_fusion.normalizers import SignalNormalizer, signal_normalizer
from app.engines.risk_fusion.thresholds import DEFAULT_RISK_THRESHOLDS, RiskThresholds
from app.engines.risk_fusion.weights import DEFAULT_FUSION_WEIGHTS, FusionWeights
from app.engines.risk_fusion.fusion_engine import (
    RiskFusionEngine,
    risk_fusion_engine,
)

__all__ = [
    "DEFAULT_FUSION_WEIGHTS",
    "DEFAULT_RISK_THRESHOLDS",
    "FusionInput",
    "FusionResult",
    "FusionWeights",
    "MissingSignalPolicy",
    "NormalizedSignal",
    "RiskFusionEngine",
    "RiskLevel",
    "RiskThresholds",
    "SignalContribution",
    "SignalModality",
    "SignalNormalizer",
    "risk_fusion_engine",
    "signal_normalizer",
]
