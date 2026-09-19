"""
MuleTrace AI — Risk Fusion Engine End-to-End Unit Tests.

Validates multi-modal synthesis, mathematical accuracy of contributions, determinism,
and risk tier classification (Milestone 10).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import pytest

from app.domain.models import TransactionEvent
from app.domain.interfaces import ModelPrediction
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.engines.risk_fusion.fusion_engine import RiskFusionEngine, risk_fusion_engine
from app.engines.risk_fusion.models import (
    FusionInput,
    FusionResult,
    RiskLevel,
)
from app.engines.risk_fusion.thresholds import RiskThresholds
from app.engines.risk_fusion.weights import FusionWeights
from app.engines.rules.base import EvaluationResult, RuleMatchResult
from app.engines.temporal.temporal_models import TemporalFeatures


def _sample_event() -> TransactionEvent:
    return TransactionEvent(
        transaction_id="TXN_FUSION_001",
        sender_account="ACC_SRC_100",
        receiver_account="ACC_DST_200",
        amount=50000.0,
        timestamp=datetime(2026, 9, 19, 12, 0, 0),
        transaction_type="TRANSFER",
        channel="ONLINE",
    )


def test_full_multimodal_fusion_math():
    """Validates weighted composite risk calculation when all 5 modalities are active."""
    engine = RiskFusionEngine()  # Uses DEFAULT_FUSION_WEIGHTS (0.25, 0.15, 0.20, 0.25, 0.15)

    # 1. Rules: total delta 60 -> 0.60
    rules = EvaluationResult(
        total_risk_score_delta=60,
        matches=[RuleMatchResult("R001", "Vel", "VEL", True, 60, "LOW", "ok")],
        highest_severity="LOW",
    )

    # 2. Temporal: burst + rapid -> ~0.70
    temporal = TemporalFeatures(
        reference_time=datetime(2026, 9, 19, 12, 0, 0),
        burst_detected=True,  # 0.35
        rapid_in_out_detected=True,
        rapid_in_out_ratio=1.0,  # 0.35
    )  # value = 0.70

    # 3. Graph: cycle -> ~0.35
    graph = GraphFeatures(
        account_id="ACC_SRC_100",
        has_cycle=True,  # 0.35
    )  # value = 0.35

    # 4. Tabular ML: 0.80
    tab_pred = ModelPrediction(
        risk_score=80,
        fraud_probability=0.80,
        is_fraud=True,
        model_version="xgboost_v1.0",
        details={"model_artifact_loaded": True},
    )

    # 5. Graph ML: 0.60
    graph_pred = ModelPrediction(
        risk_score=60,
        fraud_probability=0.60,
        is_fraud=True,
        model_version="graphsage_v1.0",
        details={"model_artifact_loaded": True},
    )

    fusion_input = FusionInput(
        event=_sample_event(),
        rule_signals=rules,
        temporal_features=temporal,
        graph_features=graph,
        tabular_prediction=tab_pred,
        graph_ml_prediction=graph_pred,
    )

    result = engine.fuse(fusion_input)

    assert isinstance(result, FusionResult)
    assert len(result.available_modalities) == 5
    assert len(result.unavailable_modalities) == 0

    # Expected Composite Math:
    # 0.25 * 0.60 (rules)       = 0.1500
    # 0.15 * 0.70 (temporal)    = 0.1050
    # 0.20 * 0.35 (graph)       = 0.0700
    # 0.25 * 0.80 (tabular)     = 0.2000
    # 0.15 * 0.60 (graph_ml)    = 0.0900
    # Total Expected = 0.15 + 0.105 + 0.07 + 0.20 + 0.09 = 0.6150
    # Composite Score = 61.50 -> MEDIUM (30 <= s < 65)

    assert result.normalized_risk == pytest.approx(0.6150, abs=1e-3)
    assert result.composite_risk_score == pytest.approx(61.50, abs=0.1)
    assert result.risk_level == RiskLevel.MEDIUM

    # Verify sum of individual contributions matches composite risk
    total_contrib = sum(c.weighted_score for c in result.contributions.values())
    assert total_contrib == pytest.approx(result.normalized_risk, abs=1e-4)


def test_high_risk_critical_scenario():
    """Severe indicators across all signals escalate composite score into CRITICAL band."""
    engine = RiskFusionEngine()

    # Critical rules triggered
    rules = EvaluationResult(
        total_risk_score_delta=90,
        matches=[RuleMatchResult("R014", "Cycle", "CYCLE", True, 90, "CRITICAL", "critical flow")],
        highest_severity="CRITICAL",
    )
    # Violent temporal burst & pass-through
    temporal = TemporalFeatures(
        reference_time=datetime(2026, 9, 19, 12, 0, 0),
        burst_detected=True,
        rapid_in_out_detected=True,
        rapid_in_out_ratio=0.99,
        transaction_count_1h=20,
    )
    # Graph syndicate with shared devices and circular cycle
    graph = GraphFeatures(
        account_id="ACC_SRC_100",
        has_cycle=True,
        shared_device_count=5,
        shared_ip_count=4,
    )
    # High probability ML predictions
    tab_pred = ModelPrediction(95, 0.95, True, "v1", {"model_artifact_loaded": True})
    graph_pred = ModelPrediction(92, 0.92, True, "v1", {"model_artifact_loaded": True})

    res = engine.fuse(FusionInput(
        event=_sample_event(),
        rule_signals=rules,
        temporal_features=temporal,
        graph_features=graph,
        tabular_prediction=tab_pred,
        graph_ml_prediction=graph_pred,
    ))

    assert res.composite_risk_score >= 85.0
    assert res.risk_level == RiskLevel.CRITICAL


def test_low_risk_calm_scenario():
    """Clean transaction with zero rule violations and calm metrics evaluates to LOW."""
    engine = RiskFusionEngine()

    rules = EvaluationResult(total_risk_score_delta=0, matches=[], highest_severity="LOW")
    temporal = TemporalFeatures(reference_time=datetime(2026, 9, 19, 12, 0, 0))
    graph = GraphFeatures(account_id="ACC_SRC_100")
    tab_pred = ModelPrediction(5, 0.05, False, "v1", {"model_artifact_loaded": True})
    graph_pred = ModelPrediction(2, 0.02, False, "v1", {"model_artifact_loaded": True})

    res = engine.fuse(FusionInput(
        event=_sample_event(),
        rule_signals=rules,
        temporal_features=temporal,
        graph_features=graph,
        tabular_prediction=tab_pred,
        graph_ml_prediction=graph_pred,
    ))

    assert res.composite_risk_score < 10.0
    assert res.risk_level == RiskLevel.LOW


def test_fusion_determinism_across_multiple_runs():
    """Identical input evaluated 10 consecutive times produces identical numerical results."""
    engine = risk_fusion_engine

    inp = FusionInput(
        event=_sample_event(),
        rule_signals=EvaluationResult(total_risk_score_delta=40, matches=[], highest_severity="MEDIUM"),
        tabular_prediction=ModelPrediction(60, 0.60, True, "v1", {"model_artifact_loaded": True}),
    )

    baseline = engine.fuse(inp)
    for _ in range(10):
        run = engine.fuse(inp)
        assert run.composite_risk_score == baseline.composite_risk_score
        assert run.normalized_risk == baseline.normalized_risk
        assert run.risk_level == baseline.risk_level
        assert run.effective_weights == baseline.effective_weights


def test_custom_weights_and_thresholds():
    """Engine respects custom injected weight distributions and classification tiers."""
    # Prioritize rules heavily (80%)
    custom_weights = FusionWeights(
        rules_weight=0.80,
        temporal_weight=0.05,
        graph_weight=0.05,
        tabular_ml_weight=0.05,
        graph_ml_weight=0.05,
    )
    custom_thresholds = RiskThresholds(low_max=20.0, medium_max=50.0, high_max=75.0)

    engine = RiskFusionEngine(weights=custom_weights, thresholds=custom_thresholds)

    # 1 rule match delta 70 -> rules normalized = 0.70
    inp = FusionInput(
        rule_signals=EvaluationResult(total_risk_score_delta=70, matches=[], highest_severity="LOW"),
    )
    res = engine.fuse(inp)

    # Missing signals renormalized: rules is only available signal -> effective_weight = 1.0
    assert res.effective_weights["rules"] == 1.0
    assert res.composite_risk_score == 70.0
    # Under custom thresholds (high_max=75, medium_max=50), 70.0 is HIGH
    assert res.risk_level == RiskLevel.HIGH
