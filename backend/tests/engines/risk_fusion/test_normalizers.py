"""
MuleTrace AI — Modality Signal Normalizers Unit Tests.

Validates deterministic conversion of M5, M6, M7, M8, and M9 outputs into [0.0, 1.0] (Milestone 10).
"""

from __future__ import annotations

from datetime import datetime
import pytest

from app.domain.interfaces import ModelPrediction
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.engines.risk_fusion.models import SignalModality
from app.engines.risk_fusion.normalizers import signal_normalizer
from app.engines.rules.base import EvaluationResult, RuleMatchResult
from app.engines.temporal.temporal_models import TemporalFeatures


# ── M5 Rules Normalization Tests ─────────────────────────────────────────────


def test_normalize_rules_none_handling():
    """Missing rules returns is_available=False without error."""
    sig = signal_normalizer.normalize_rules(None)
    assert sig.modality == SignalModality.RULES
    assert sig.is_available is False
    assert sig.value == 0.0
    assert sig.status == "missing"


def test_normalize_rules_zero_matches():
    """Genuinely evaluated rules with zero matches produces is_available=True and value=0.0."""
    res = EvaluationResult(
        total_risk_score_delta=0,
        matches=[],
        flagged_patterns=[],
        highest_severity="LOW",
    )
    sig = signal_normalizer.normalize_rules(res)
    assert sig.is_available is True
    assert sig.value == 0.0
    assert sig.contributing_factors["matched_rule_count"] == 0


def test_normalize_rules_delta_and_severity_floors():
    """Rule normalization applies delta scaling and severity floor overrides."""
    # Score delta 20 with LOW severity -> 0.20
    res_low = EvaluationResult(
        total_risk_score_delta=20,
        matches=[RuleMatchResult("R001", "Vel", "VEL", True, 20, "LOW", "ok")],
        highest_severity="LOW",
    )
    sig_low = signal_normalizer.normalize_rules(res_low)
    assert sig_low.value == 0.20

    # Score delta 20 with HIGH severity -> boosted to 0.65 floor
    res_high = EvaluationResult(
        total_risk_score_delta=20,
        matches=[RuleMatchResult("R004", "Chain", "CHAIN", True, 20, "HIGH", "ok")],
        highest_severity="HIGH",
    )
    sig_high = signal_normalizer.normalize_rules(res_high)
    assert sig_high.value == 0.65

    # Score delta 20 with CRITICAL severity -> boosted to 0.85 floor
    res_crit = EvaluationResult(
        total_risk_score_delta=20,
        matches=[RuleMatchResult("R014", "Cycle", "CYCLE", True, 20, "CRITICAL", "ok")],
        highest_severity="CRITICAL",
    )
    sig_crit = signal_normalizer.normalize_rules(res_crit)
    assert sig_crit.value == 0.85

    # Score delta 150 -> capped at 1.00
    res_max = EvaluationResult(
        total_risk_score_delta=150,
        highest_severity="CRITICAL",
    )
    assert signal_normalizer.normalize_rules(res_max).value == 1.00


# ── M6 Temporal Normalization Tests ──────────────────────────────────────────


def test_normalize_temporal_none_handling():
    """Missing temporal features returns is_available=False."""
    sig = signal_normalizer.normalize_temporal(None)
    assert sig.modality == SignalModality.TEMPORAL
    assert sig.is_available is False
    assert sig.status == "missing"


def test_normalize_temporal_calm_and_extreme():
    """Calm profile produces ~0.0, burst + rapid pass-through produces high risk bounded by 1.0."""
    ref = datetime(2026, 9, 19, 12, 0, 0)

    # Calm account
    calm = TemporalFeatures(reference_time=ref)
    sig_calm = signal_normalizer.normalize_temporal(calm)
    assert sig_calm.is_available is True
    assert sig_calm.value == 0.0

    # High-velocity burst and rapid pass-through
    furious = TemporalFeatures(
        reference_time=ref,
        burst_detected=True,
        rapid_in_out_detected=True,
        rapid_in_out_ratio=0.98,
        transaction_count_1h=25,
        temporal_concentration=0.95,
    )
    sig_furious = signal_normalizer.normalize_temporal(furious)
    assert sig_furious.is_available is True
    # 0.35 (burst) + 0.35 * 0.98 + 0.15 * 1.0 + 0.15 * 0.95 = 0.35 + 0.343 + 0.15 + 0.1425 = 0.9855
    assert 0.95 <= sig_furious.value <= 1.0
    assert sig_furious.value <= 1.0


# ── M7 Graph Normalization Tests ─────────────────────────────────────────────


def test_normalize_graph_none_handling():
    """Missing graph features returns is_available=False."""
    sig = signal_normalizer.normalize_graph(None)
    assert sig.modality == SignalModality.GRAPH
    assert sig.is_available is False
    assert sig.status == "missing"


def test_normalize_graph_topological_syndicates():
    """Cycles and shared entity clusters scale deterministically into [0.0, 1.0]."""
    # Isolated account
    calm_graph = GraphFeatures(account_id="ACC_SAFE")
    sig_calm = signal_normalizer.normalize_graph(calm_graph)
    assert sig_calm.is_available is True
    assert sig_calm.value == 0.0

    # Mule ring with circular cycle and shared hardware
    ring = GraphFeatures(
        account_id="ACC_MULE_RING",
        has_cycle=True,
        shared_device_count=4,
        shared_ip_count=3,
        fan_in_ratio=0.90,
        neighborhood_density=0.80,
    )
    sig_ring = signal_normalizer.normalize_graph(ring)
    assert sig_ring.is_available is True
    # 0.35 (cycle) + 0.35 * 1.0 (shared) + 0.15 * 0.90 + 0.15 * 0.80 = 0.35 + 0.35 + 0.135 + 0.12 = 0.955
    assert 0.90 <= sig_ring.value <= 1.0
    assert sig_ring.value <= 1.0


# ── M8 & M9 ML Prediction Normalization Tests ────────────────────────────────


def test_normalize_tabular_ml_trained_vs_unavailable():
    """Distinguishes genuine trained inference from offline / fallback status."""
    # None
    assert signal_normalizer.normalize_tabular_ml(None).is_available is False

    # Unavailable / fallback model
    fallback_pred = ModelPrediction(
        risk_score=0,
        fraud_probability=0.0,
        is_fraud=False,
        model_version="xgboost_v1.0_fallback",
        details={"status": "model_unavailable", "model_artifact_loaded": False},
    )
    sig_fallback = signal_normalizer.normalize_tabular_ml(fallback_pred)
    assert sig_fallback.is_available is False
    assert sig_fallback.status == "model_unavailable"

    # Genuine trained prediction
    active_pred = ModelPrediction(
        risk_score=78,
        fraud_probability=0.7845,
        is_fraud=True,
        model_version="xgboost_v1.0",
        details={"model_artifact_loaded": True},
    )
    sig_active = signal_normalizer.normalize_tabular_ml(active_pred)
    assert sig_active.is_available is True
    assert sig_active.value == 0.7845
    assert sig_active.status == "available"


def test_normalize_graph_ml_trained_vs_unavailable():
    """Distinguishes genuine GraphSAGE inference from un-trained fallback status."""
    # None
    assert signal_normalizer.normalize_graph_ml(None).is_available is False

    # Un-trained GraphSAGE fallback
    fallback_pred = ModelPrediction(
        risk_score=0,
        fraud_probability=0.0,
        is_fraud=False,
        model_version="graphsage_v1.0_fallback",
        details={"status": "model_unavailable", "model_artifact_loaded": False},
    )
    sig_fallback = signal_normalizer.normalize_graph_ml(fallback_pred)
    assert sig_fallback.is_available is False
    assert sig_fallback.status == "model_unavailable"

    # Active trained GraphSAGE prediction
    active_pred = ModelPrediction(
        risk_score=89,
        fraud_probability=0.8912,
        is_fraud=True,
        model_version="graphsage_v1.0",
        details={"model_artifact_loaded": True, "embedding_dim": 16},
    )
    sig_active = signal_normalizer.normalize_graph_ml(active_pred)
    assert sig_active.is_available is True
    assert sig_active.value == 0.8912
    assert sig_active.status == "available"
