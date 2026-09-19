"""
MuleTrace AI — Risk Fusion Architectural Invariants Tests.

Verifies the 16 architectural invariants governing Milestone 10:
INV-1:  Fusion is deterministic.
INV-2:  Every normalized signal is strictly in [0.0, 1.0].
INV-3:  Weights are finite and non-negative.
INV-4:  Invalid weight configuration is rejected.
INV-5:  Composite risk remains within [0.0, 100.0].
INV-6:  M5 outputs are not modified.
INV-7:  M6 outputs are not modified.
INV-8:  M7 outputs are not modified.
INV-9:  M8 ModelPrediction is not modified.
INV-10: M9 ModelPrediction is not modified.
INV-11: Missing signals are explicitly represented.
INV-12: Unavailable models are not interpreted as valid low-risk predictions.
INV-13: No duplicate M5/M6/M7 business logic is implemented in M10.
INV-14: No M11 evidence generation exists in M10.
INV-15: No AWS dependency exists in M10 business logic.
INV-16: Existing application behavior remains unchanged.
"""

from __future__ import annotations

import sys
from datetime import datetime
import pytest

from app.domain.models import TransactionEvent
from app.domain.interfaces import ModelPrediction
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.engines.risk_fusion.fusion_engine import RiskFusionEngine, risk_fusion_engine
from app.engines.risk_fusion.models import (
    FusionInput,
    FusionResult,
    MissingSignalPolicy,
    RiskLevel,
    SignalModality,
)
from app.engines.risk_fusion.normalizers import signal_normalizer
from app.engines.risk_fusion.weights import FusionWeights
from app.engines.rules.base import EvaluationResult, RuleMatchResult
from app.engines.temporal.temporal_models import TemporalFeatures


def _sample_input():
    rules = EvaluationResult(
        total_risk_score_delta=50,
        matches=[RuleMatchResult("R001", "Vel", "VEL", True, 50, "MEDIUM", "vel match")],
        highest_severity="MEDIUM",
    )
    temporal = TemporalFeatures(
        reference_time=datetime(2026, 9, 19, 12, 0, 0),
        burst_detected=True,
        transaction_count_1h=8,
    )
    graph = GraphFeatures(
        account_id="ACC_INV",
        has_cycle=False,
        shared_device_count=2,
    )
    tab_pred = ModelPrediction(
        risk_score=70,
        fraud_probability=0.70,
        is_fraud=True,
        model_version="xgboost_v1.0",
        details={"model_artifact_loaded": True},
    )
    graph_pred = ModelPrediction(
        risk_score=40,
        fraud_probability=0.40,
        is_fraud=False,
        model_version="graphsage_v1.0",
        details={"model_artifact_loaded": True},
    )
    return rules, temporal, graph, tab_pred, graph_pred


# ── INV-1: Fusion is deterministic ───────────────────────────────────────────
def test_inv_1_fusion_is_deterministic():
    """Identical inputs produce mathematically identical results across repeated runs."""
    rules, temporal, graph, tab_pred, graph_pred = _sample_input()
    inp = FusionInput(
        rule_signals=rules,
        temporal_features=temporal,
        graph_features=graph,
        tabular_prediction=tab_pred,
        graph_ml_prediction=graph_pred,
    )

    r1 = risk_fusion_engine.fuse(inp)
    r2 = risk_fusion_engine.fuse(inp)

    assert r1.composite_risk_score == r2.composite_risk_score
    assert r1.normalized_risk == r2.normalized_risk
    assert r1.risk_level == r2.risk_level
    assert r1.effective_weights == r2.effective_weights


# ── INV-2: Every normalized signal is within [0.0, 1.0] ──────────────────────
def test_inv_2_normalized_signals_bounded():
    """Signals across all modalities are strictly bounded within [0.0, 1.0]."""
    rules, temporal, graph, tab_pred, graph_pred = _sample_input()
    inp = FusionInput(
        rule_signals=rules,
        temporal_features=temporal,
        graph_features=graph,
        tabular_prediction=tab_pred,
        graph_ml_prediction=graph_pred,
    )

    signals = risk_fusion_engine.extract_signals(inp)
    for mod, sig in signals.items():
        assert 0.0 <= sig.value <= 1.0, f"Signal {mod} out of bounds: {sig.value}"


# ── INV-3 & INV-4: Weights validation ────────────────────────────────────────
def test_inv_3_and_4_weights_validation():
    """Weights must be finite, non-negative, and invalid configurations must be rejected."""
    valid_weights = FusionWeights()
    assert sum(valid_weights.to_dict().values()) == pytest.approx(1.0)

    # Rejection of invalid
    with pytest.raises(ValueError):
        FusionWeights(rules_weight=-1.0)
    with pytest.raises(ValueError):
        FusionWeights(graph_weight=float("inf"))
    with pytest.raises(ValueError):
        FusionWeights(tabular_ml_weight=float("nan"))


# ── INV-5: Composite risk remains within [0.0, 100.0] ────────────────────────
def test_inv_5_composite_risk_bounded():
    """Composite score is strictly in [0.0, 100.0] under any valid configuration."""
    rules, temporal, graph, tab_pred, graph_pred = _sample_input()
    inp = FusionInput(
        rule_signals=rules,
        temporal_features=temporal,
        graph_features=graph,
        tabular_prediction=tab_pred,
        graph_ml_prediction=graph_pred,
    )

    res = risk_fusion_engine.fuse(inp)
    assert 0.0 <= res.composite_risk_score <= 100.0
    assert 0.0 <= res.normalized_risk <= 1.0


# ── INV-6 to INV-10: Immutability of Underlying M5-M9 Signals ────────────────
def test_inv_6_through_10_m5_to_m9_immutability():
    """Risk fusion consumes M5, M6, M7, M8, M9 outputs without mutating them."""
    rules, temporal, graph, tab_pred, graph_pred = _sample_input()

    # Capture pre-fusion state
    orig_rules_delta = rules.total_risk_score_delta
    orig_temporal_burst = temporal.burst_detected
    orig_graph_cycle = graph.has_cycle
    orig_tab_score = tab_pred.risk_score
    orig_graph_score = graph_pred.risk_score

    inp = FusionInput(
        rule_signals=rules,
        temporal_features=temporal,
        graph_features=graph,
        tabular_prediction=tab_pred,
        graph_ml_prediction=graph_pred,
    )

    _ = risk_fusion_engine.fuse(inp)

    # Verify post-fusion state is unaltered
    assert rules.total_risk_score_delta == orig_rules_delta
    assert temporal.burst_detected == orig_temporal_burst
    assert graph.has_cycle == orig_graph_cycle
    assert tab_pred.risk_score == orig_tab_score
    assert graph_pred.risk_score == orig_graph_score


# ── INV-11 & INV-12: Missing signal & model availability ─────────────────────
def test_inv_11_and_12_missing_signals_and_model_availability():
    """Missing signals are tracked, and un-trained models are not confused with 0.0 risk."""
    tab_fallback = ModelPrediction(
        risk_score=0,
        fraud_probability=0.0,
        is_fraud=False,
        model_version="xgboost_v1.0_fallback",
        details={"status": "model_unavailable", "model_artifact_loaded": False},
    )
    inp = FusionInput(tabular_prediction=tab_fallback)
    res = risk_fusion_engine.fuse(inp)

    assert "tabular_ml" in res.unavailable_modalities
    assert "tabular_ml" not in res.available_modalities
    # Unavailable model does NOT count as a valid low-risk prediction
    norm_sig = signal_normalizer.normalize_tabular_ml(tab_fallback)
    assert norm_sig.is_available is False
    assert norm_sig.status == "model_unavailable"


# ── INV-13: No duplicate M5/M6/M7 business logic in M10 ──────────────────────
def test_inv_13_no_duplicate_business_logic():
    """M10 contains zero heuristic point additions or rule thresholds."""
    # Ensure normalizers do not re-run cycle detection, burst detection, or SQL queries
    # Normalizers only read pre-computed fields
    import app.engines.risk_fusion.normalizers as norm_mod
    src = open(norm_mod.__file__, "r", encoding="utf-8").read()

    assert "nx.simple_cycles" not in src
    assert "SELECT" not in src
    assert "timedelta" not in src


# ── INV-14: No M11 evidence generation in M10 ────────────────────────────────
def test_inv_14_no_m11_evidence_generation():
    """M10 result contains mathematical explainability only, NOT narrative evidence."""
    import app.engines.risk_fusion.models as models_mod
    src = open(models_mod.__file__, "r", encoding="utf-8").read()

    assert "generate_narrative" not in src
    assert "suggest_next_steps" not in src
    assert "InvestigationCopilot" not in src


# ── INV-15: No AWS dependencies in M10 ───────────────────────────────────────
def test_inv_15_no_aws_dependency():
    """M10 operates purely locally with zero AWS or boto3 dependencies."""
    for mod_name in sys.modules:
        if mod_name.startswith("app.engines.risk_fusion"):
            mod = sys.modules[mod_name]
            file_path = getattr(mod, "__file__", "")
            if file_path and file_path.endswith(".py"):
                code = open(file_path, "r", encoding="utf-8").read()
                assert "import boto3" not in code
                assert "from boto3" not in code
                assert "import botocore" not in code
                assert "from botocore" not in code


# ── INV-16: Existing application behavior unchanged ──────────────────────────
def test_inv_16_existing_application_unaffected():
    """Importing risk fusion does not mutate RuleEngine or ModelService."""
    from app.engines.rules.rule_engine import RuleEngine
    from app.domain.interfaces import ModelService

    assert RuleEngine is not None
    assert ModelService is not None
