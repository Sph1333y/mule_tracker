"""
MuleTrace AI — Missing Signals & Model Availability Unit Tests.

Validates the distinction between genuine zero-risk evaluations and offline/missing modalities,
as well as missing-signal re-normalization policies (Milestone 10).
"""

from __future__ import annotations

import pytest

from app.domain.interfaces import ModelPrediction
from app.engines.risk_fusion.fusion_engine import RiskFusionEngine
from app.engines.risk_fusion.models import (
    FusionInput,
    MissingSignalPolicy,
    RiskLevel,
)
from app.engines.risk_fusion.weights import FusionWeights
from app.engines.rules.base import EvaluationResult, RuleMatchResult


def test_renormalize_when_models_are_unavailable():
    """When ML models are un-trained or offline, remaining active signals are re-weighted to 1.0."""
    engine = RiskFusionEngine(missing_policy=MissingSignalPolicy.RENORMALIZE_AVAILABLE)

    # Only rules and temporal are available
    rules = EvaluationResult(total_risk_score_delta=80, matches=[], highest_severity="LOW")
    # M8 Tabular is offline fallback
    tab_fallback = ModelPrediction(
        risk_score=0,
        fraud_probability=0.0,
        is_fraud=False,
        model_version="xgboost_v1.0_fallback",
        details={"status": "model_unavailable", "model_artifact_loaded": False},
    )
    # M9 Graph ML is None (absent)

    inp = FusionInput(
        rule_signals=rules,
        tabular_prediction=tab_fallback,
        graph_ml_prediction=None,
    )

    res = engine.fuse(inp)

    # Only 'rules' is available (normalized=0.80).
    assert res.available_modalities == ["rules"]
    assert "tabular_ml" in res.unavailable_modalities
    assert "graph_ml" in res.unavailable_modalities

    # Effective weight for rules must be scaled to 1.0
    assert res.effective_weights["rules"] == 1.0
    assert res.effective_weights["tabular_ml"] == 0.0
    assert res.effective_weights["graph_ml"] == 0.0

    # Composite risk is 0.80 * 1.0 = 0.80 -> 80.0
    assert res.composite_risk_score == 80.0


def test_genuine_zero_risk_vs_unavailable_difference():
    """A genuine 0.0 ML prediction pulls the score down, while an unavailable model does not."""
    engine = RiskFusionEngine(missing_policy=MissingSignalPolicy.RENORMALIZE_AVAILABLE)

    rules = EvaluationResult(total_risk_score_delta=80, matches=[], highest_severity="LOW")  # 0.80

    # Scenario A: Tabular ML is UNAVAILABLE / OFFLINE
    inp_offline = FusionInput(
        rule_signals=rules,
        tabular_prediction=ModelPrediction(
            risk_score=0,
            fraud_probability=0.0,
            is_fraud=False,
            model_version="xgboost_fallback",
            details={"status": "model_unavailable", "model_artifact_loaded": False},
        ),
    )
    res_offline = engine.fuse(inp_offline)
    # Rules effective weight is 1.0 -> Composite score is 80.0
    assert res_offline.composite_risk_score == 80.0

    # Scenario B: Tabular ML is GENUINELY TRAINED and predicts 0.00 fraud probability
    inp_trained_zero = FusionInput(
        rule_signals=rules,
        tabular_prediction=ModelPrediction(
            risk_score=0,
            fraud_probability=0.0,
            is_fraud=False,
            model_version="xgboost_v1.0",
            details={"model_artifact_loaded": True},  # Active model!
        ),
    )
    res_trained_zero = engine.fuse(inp_trained_zero)
    # Rules weight = 0.25, Tabular weight = 0.25 -> Both available, total available = 0.50
    # Effective weight = 0.50 each
    # Composite = 0.50 * 0.80 (rules) + 0.50 * 0.00 (tabular) = 0.40 -> 40.0
    assert res_trained_zero.composite_risk_score == 40.0
    # Demonstrates clear behavioral difference: genuine low-risk pulls score down; offline does not


def test_zero_contribution_policy():
    """Under ZERO_CONTRIBUTION policy, unavailable signals contribute 0 without scaling up others."""
    weights = FusionWeights(
        rules_weight=0.50,
        temporal_weight=0.10,
        graph_weight=0.10,
        tabular_ml_weight=0.20,
        graph_ml_weight=0.10,
    )
    engine = RiskFusionEngine(weights=weights, missing_policy=MissingSignalPolicy.ZERO_CONTRIBUTION)

    # Only rules (normalized = 1.0) is available
    rules = EvaluationResult(total_risk_score_delta=100, matches=[], highest_severity="LOW")
    inp = FusionInput(rule_signals=rules)

    res = engine.fuse(inp)
    # Effective weight remains the configured 0.50 (no scaling up)
    assert res.effective_weights["rules"] == 0.50
    # Composite score = 0.50 * 1.0 = 0.50 -> 50.0
    assert res.composite_risk_score == 50.0


def test_penalty_baseline_policy():
    """Under PENALTY_BASELINE policy, missing signals contribute neutral 0.20 baseline."""
    weights = FusionWeights(
        rules_weight=0.50,
        temporal_weight=0.10,
        graph_weight=0.10,
        tabular_ml_weight=0.20,
        graph_ml_weight=0.10,
    )
    engine = RiskFusionEngine(weights=weights, missing_policy=MissingSignalPolicy.PENALTY_BASELINE)

    # Rules (1.0) is available (weight 0.50). Other 4 modalities (total weight 0.50) are missing.
    rules = EvaluationResult(total_risk_score_delta=100, matches=[], highest_severity="LOW")
    inp = FusionInput(rule_signals=rules)

    res = engine.fuse(inp)
    # Composite = 0.50 * 1.0 + 0.50 * 0.20 = 0.50 + 0.10 = 0.60 -> 60.0
    assert res.composite_risk_score == 60.0


def test_all_signals_missing_handling():
    """Completely empty input produces safe zero composite risk without throwing exceptions."""
    engine = RiskFusionEngine()
    empty_input = FusionInput()

    res = engine.fuse(empty_input)
    assert res.composite_risk_score == 0.0
    assert res.normalized_risk == 0.0
    assert res.risk_level == RiskLevel.LOW
    assert len(res.available_modalities) == 0
    assert len(res.unavailable_modalities) == 5
