"""
MuleTrace AI — Risk Fusion Domain Models & Contracts.

Defines the data structures, modalities, signal representations, and fusion results
for the multi-modal Risk Fusion subsystem (Milestone 10).

Architectural Boundary:
- Cloud-agnostic and framework-neutral (pure Python standard library & domain types).
- Zero dependency on AWS (no boto3, Lambda, Neptune, etc.).
- Consumes M5 (rules), M6 (temporal), M7 (graph), M8 (tabular ML), and M9 (graph ML) outputs
  without altering their internal states or original semantics.
- Immutable output representation via frozen dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.domain.models import TransactionEvent
from app.domain.interfaces import ModelPrediction
from app.engines.rules.base import EvaluationResult, RuleMatchResult
from app.engines.temporal.temporal_models import TemporalFeatures
from app.engines.graph.intelligence.graph_models import GraphFeatures


class SignalModality(str, Enum):
    """Supported detection modalities contributing to composite risk fusion."""

    RULES = "rules"
    TEMPORAL = "temporal"
    GRAPH = "graph"
    TABULAR_ML = "tabular_ml"
    GRAPH_ML = "graph_ml"


class RiskLevel(str, Enum):
    """Categorical risk bands mapped from the continuous composite risk score."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MissingSignalPolicy(str, Enum):
    """Strategy for handling absent or un-trained signal modalities.

    Policies:
        RENORMALIZE_AVAILABLE: Re-scales available modality weights so their sum equals 1.0.
        ZERO_CONTRIBUTION: Missing signals contribute 0.0, retaining original weight allocations.
        PENALTY_BASELINE: Missing signals assume an uninformative neutral baseline (e.g. 0.20).
    """

    RENORMALIZE_AVAILABLE = "renormalize_available"
    ZERO_CONTRIBUTION = "zero_contribution"
    PENALTY_BASELINE = "penalty_baseline"


@dataclass(frozen=True)
class NormalizedSignal:
    """Standardized representation of a single detection modality's signal in [0.0, 1.0].

    Attributes:
        modality: The originating detection modality.
        value: Normalized risk score strictly bounded in [0.0, 1.0].
        is_available: Whether the modality produced an active, valid evaluation.
        status: Diagnostic status ("available", "missing", "model_unavailable", "no_history").
        raw_summary: Summary of raw inputs prior to normalization.
        contributing_factors: Dictionary of specific metrics driving this modality's score.
    """

    modality: SignalModality
    value: float
    is_available: bool
    status: str = "available"
    raw_summary: Optional[str] = None
    contributing_factors: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert normalized signal to JSON-serializable dictionary."""
        return {
            "modality": self.modality.value,
            "value": round(self.value, 4),
            "is_available": self.is_available,
            "status": self.status,
            "raw_summary": self.raw_summary,
            "contributing_factors": self.contributing_factors,
        }


@dataclass
class FusionInput:
    """Unified container encapsulating all independent detection signals for a transaction.

    Accepts outputs produced independently by M5, M6, M7, M8, and M9.
    All inputs are optional to support partial or asynchronous evaluation pipelines.
    """

    event: Optional[TransactionEvent] = None
    rule_signals: Optional[EvaluationResult | list[RuleMatchResult] | dict[str, Any]] = None
    temporal_features: Optional[TemporalFeatures] = None
    graph_features: Optional[GraphFeatures] = None
    tabular_prediction: Optional[ModelPrediction] = None
    graph_ml_prediction: Optional[ModelPrediction] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert fusion inputs to summary dictionary for logging and audit."""
        return {
            "transaction_id": self.event.transaction_id if self.event else None,
            "has_rule_signals": self.rule_signals is not None,
            "has_temporal_features": self.temporal_features is not None,
            "has_graph_features": self.graph_features is not None,
            "has_tabular_prediction": self.tabular_prediction is not None,
            "has_graph_ml_prediction": self.graph_ml_prediction is not None,
        }


@dataclass(frozen=True)
class SignalContribution:
    """Mathematical explainability detail for a single modality's contribution to composite risk.

    Attributes:
        modality: Detection modality.
        normalized_value: The signal's normalized value in [0.0, 1.0].
        configured_weight: The static weight assigned in FusionWeights.
        effective_weight: The weight after applying missing-signal re-normalization.
        weighted_score: effective_weight * normalized_value (contribution to composite risk).
        is_available: Whether this signal was available.
        explanation: Human-readable narrative detailing the math behind the contribution.
    """

    modality: SignalModality
    normalized_value: float
    configured_weight: float
    effective_weight: float
    weighted_score: float
    is_available: bool
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "modality": self.modality.value,
            "normalized_value": round(self.normalized_value, 4),
            "configured_weight": round(self.configured_weight, 4),
            "effective_weight": round(self.effective_weight, 4),
            "weighted_score": round(self.weighted_score, 4),
            "is_available": self.is_available,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class FusionResult:
    """Deterministic composite risk assessment generated by the Risk Fusion Engine.

    Attributes:
        composite_risk_score: Normalized composite score scaled to [0.0, 100.0].
        normalized_risk: Raw composite risk in [0.0, 1.0].
        risk_level: Categorical risk tier (LOW, MEDIUM, HIGH, CRITICAL).
        contributions: Breakdown of each modality's contribution.
        available_modalities: List of modalities that were actively available.
        unavailable_modalities: List of modalities that were missing or un-trained.
        effective_weights: Actual weights used in the fusion calculation.
        missing_signal_policy: Policy applied for handling absent signals.
        metadata: Diagnostic and audit metadata (e.g. timestamps, source IDs).
        fusion_version: Subsystem version identifier.
    """

    composite_risk_score: float
    normalized_risk: float
    risk_level: RiskLevel
    contributions: dict[str, SignalContribution]
    available_modalities: list[str]
    unavailable_modalities: list[str]
    effective_weights: dict[str, float]
    missing_signal_policy: MissingSignalPolicy
    metadata: dict[str, Any] = field(default_factory=dict)
    fusion_version: str = "v1.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert complete fusion result into a clean, JSON-serializable dictionary."""
        return {
            "composite_risk_score": round(self.composite_risk_score, 2),
            "normalized_risk": round(self.normalized_risk, 4),
            "risk_level": self.risk_level.value,
            "available_modalities": self.available_modalities,
            "unavailable_modalities": self.unavailable_modalities,
            "effective_weights": {k: round(v, 4) for k, v in self.effective_weights.items()},
            "missing_signal_policy": self.missing_signal_policy.value,
            "contributions": {k: v.to_dict() for k, v in self.contributions.items()},
            "metadata": self.metadata,
            "fusion_version": self.fusion_version,
        }
