"""
MuleTrace AI — Unit Tests for Input & Output Immutability.
"""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import pytest

from app.domain.interfaces import ModelPrediction
from app.domain.models import TransactionEvent
from app.engines.evidence.engine import EvidenceEngine
from app.engines.evidence.models import EvidenceInput
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.engines.risk_fusion.models import (
    FusionResult,
    MissingSignalPolicy,
    RiskLevel,
)
from app.engines.rules.base import EvaluationResult, RuleMatchResult
from app.engines.temporal.temporal_models import TemporalFeatures


def test_input_objects_remain_unmutated() -> None:
    """Verify all upstream domain objects are completely unchanged after evidence generation."""
    event = TransactionEvent(
        transaction_id="TX_IMMUTABLE_01",
        timestamp=datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc),
        sender_account="ACC_SRC_1",
        receiver_account="ACC_DST_2",
        amount=100000.0,
    )

    eval_result = EvaluationResult(
        total_risk_score_delta=40,
        matches=[
            RuleMatchResult(
                rule_code="R004",
                rule_name="Mule Chain",
                pattern_name="Rapid Pass-Through",
                matched=True,
                score_contribution=40,
                severity="HIGH",
                narrative="Mule chain detected.",
            )
        ],
    )

    tf = TemporalFeatures(
        reference_time=datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc),
        burst_detected=True,
        burst_count=3,
        rapid_in_out_detected=True,
        rapid_in_out_ratio=0.88,
    )

    gf = GraphFeatures(
        account_id="ACC_SRC_1",
        has_cycle=True,
        cycle_count=1,
        cycles=[["ACC_SRC_1", "ACC_DST_2", "ACC_SRC_1"]],
    )

    pred = ModelPrediction(
        risk_score=75,
        fraud_probability=0.75,
        is_fraud=True,
        model_version="xgboost_v1.0.0",
        details={"status": "model_trained", "model_artifact_loaded": True},
    )

    fr = FusionResult(
        composite_risk_score=77.0,
        normalized_risk=0.77,
        risk_level=RiskLevel.HIGH,
        contributions={},
        available_modalities=["rules", "temporal", "graph", "tabular_ml"],
        unavailable_modalities=[],
        effective_weights={},
        missing_signal_policy=MissingSignalPolicy.RENORMALIZE_AVAILABLE,
        fusion_version="v1.0",
    )

    inp = EvidenceInput(
        transaction_event=event,
        rule_signals=eval_result,
        temporal_features=tf,
        graph_features=gf,
        tabular_prediction=pred,
        fusion_result=fr,
    )

    engine = EvidenceEngine()
    pkg = engine.generate_evidence(inp)

    # Assert outputs exist
    assert pkg.total_evidence_count > 0
    assert pkg.composite_risk_score == 77.0
    assert pkg.risk_level == RiskLevel.HIGH

    # Assert input objects were NOT mutated
    assert event.amount == 100000.0
    assert event.sender_account == "ACC_SRC_1"
    assert eval_result.total_risk_score_delta == 40
    assert len(eval_result.matches) == 1
    assert tf.burst_detected is True
    assert tf.rapid_in_out_ratio == 0.88
    assert gf.has_cycle is True
    assert pred.risk_score == 75
    assert pred.fraud_probability == 0.75
    assert fr.composite_risk_score == 77.0


def test_package_and_items_are_frozen() -> None:
    """Verify attempting to mutate EvidencePackage or EvidenceItem raises FrozenInstanceError."""
    engine = EvidenceEngine()
    inp = EvidenceInput(case_id="CAS-FROZEN")
    pkg = engine.generate_evidence(inp)

    with pytest.raises(FrozenInstanceError):
        pkg.composite_risk_score = 100.0  # type: ignore

    with pytest.raises(FrozenInstanceError):
        pkg.case_id = "MUTATED"  # type: ignore
