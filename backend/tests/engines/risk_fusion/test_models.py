"""
MuleTrace AI — Risk Fusion Domain Models Unit Tests.

Validates data models, immutability, serialization, and structure contracts (Milestone 10).
"""

from __future__ import annotations

import pytest
from app.engines.risk_fusion.models import (
    FusionInput,
    FusionResult,
    MissingSignalPolicy,
    NormalizedSignal,
    RiskLevel,
    SignalContribution,
    SignalModality,
)


def test_signal_modality_enum_values():
    """Confirms all 5 canonical detection modalities are supported."""
    assert SignalModality.RULES.value == "rules"
    assert SignalModality.TEMPORAL.value == "temporal"
    assert SignalModality.GRAPH.value == "graph"
    assert SignalModality.TABULAR_ML.value == "tabular_ml"
    assert SignalModality.GRAPH_ML.value == "graph_ml"


def test_normalized_signal_creation_and_immutability():
    """NormalizedSignal is immutable and properly serializes to dictionary."""
    sig = NormalizedSignal(
        modality=SignalModality.RULES,
        value=0.75,
        is_available=True,
        status="available",
        raw_summary="delta=75",
        contributing_factors={"delta": 75},
    )

    assert sig.modality == SignalModality.RULES
    assert sig.value == 0.75
    assert sig.is_available is True
    assert sig.status == "available"

    # Verify frozen immutability
    with pytest.raises(Exception):
        sig.value = 0.90  # type: ignore

    d = sig.to_dict()
    assert d["modality"] == "rules"
    assert d["value"] == 0.75
    assert d["is_available"] is True


def test_signal_contribution_creation_and_math():
    """SignalContribution accurately records weight allocation and mathematical product."""
    contrib = SignalContribution(
        modality=SignalModality.GRAPH,
        normalized_value=0.80,
        configured_weight=0.20,
        effective_weight=0.25,
        weighted_score=0.20,
        is_available=True,
        explanation="GRAPH: normalized=0.8000, effective_weight=0.2500 -> contribution=0.2000",
    )

    assert contrib.modality == SignalModality.GRAPH
    assert contrib.effective_weight == 0.25
    assert contrib.weighted_score == 0.20

    d = contrib.to_dict()
    assert d["modality"] == "graph"
    assert d["weighted_score"] == 0.20


def test_fusion_input_optionality_and_summary():
    """FusionInput accepts fully empty or partially specified inputs safely."""
    empty_input = FusionInput()
    assert empty_input.event is None
    assert empty_input.rule_signals is None
    assert empty_input.temporal_features is None
    assert empty_input.graph_features is None
    assert empty_input.tabular_prediction is None
    assert empty_input.graph_ml_prediction is None

    summary = empty_input.to_dict()
    assert summary["has_rule_signals"] is False
    assert summary["has_temporal_features"] is False


def test_fusion_result_immutability():
    """FusionResult is a frozen dataclass preserving composite scores and breakdown."""
    res = FusionResult(
        composite_risk_score=68.50,
        normalized_risk=0.6850,
        risk_level=RiskLevel.HIGH,
        contributions={},
        available_modalities=["rules", "temporal"],
        unavailable_modalities=["graph", "tabular_ml", "graph_ml"],
        effective_weights={"rules": 0.625, "temporal": 0.375},
        missing_signal_policy=MissingSignalPolicy.RENORMALIZE_AVAILABLE,
    )

    assert res.composite_risk_score == 68.50
    assert res.risk_level == RiskLevel.HIGH
    assert res.fusion_version == "v1.0"

    with pytest.raises(Exception):
        res.composite_risk_score = 99.0  # type: ignore

    d = res.to_dict()
    assert d["composite_risk_score"] == 68.50
    assert d["risk_level"] == "HIGH"
    assert d["missing_signal_policy"] == "renormalize_available"
