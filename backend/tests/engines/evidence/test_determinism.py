"""
MuleTrace AI — Unit Tests for Evidence Determinism.
"""

from datetime import datetime, timezone

from app.domain.interfaces import ModelPrediction
from app.domain.models import TransactionEvent
from app.engines.evidence.engine import EvidenceEngine
from app.engines.evidence.models import EvidenceInput
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.engines.risk_fusion.models import (
    FusionResult,
    MissingSignalPolicy,
    RiskLevel,
    SignalContribution,
    SignalModality,
)
from app.engines.rules.base import EvaluationResult, RuleMatchResult
from app.engines.temporal.temporal_models import TemporalFeatures


def _build_rich_input() -> EvidenceInput:
    event = TransactionEvent(
        transaction_id="TX_DET_1001",
        timestamp=datetime(2026, 9, 19, 14, 30, tzinfo=timezone.utc),
        sender_account="ACC_ALPHA",
        receiver_account="ACC_BETA",
        amount=250000.0,
        currency="INR",
        channel="IMPS",
        device_id="DEV_ALPHA_99",
        ip_address="203.0.113.42",
    )

    eval_result = EvaluationResult(
        total_risk_score_delta=65,
        matches=[
            RuleMatchResult(
                rule_code="R004",
                rule_name="Mule Chain",
                pattern_name="Rapid Pass-Through",
                matched=True,
                score_contribution=40,
                severity="HIGH",
                narrative="Rapid pass-through within 3 minutes.",
            ),
            RuleMatchResult(
                rule_code="R006",
                rule_name="Shared Device",
                pattern_name="Device Ring",
                matched=True,
                score_contribution=25,
                severity="HIGH",
                narrative="Device fingerprint linked to 3 accounts.",
            ),
        ],
    )

    tf = TemporalFeatures(
        reference_time=datetime(2026, 9, 19, 14, 30, tzinfo=timezone.utc),
        burst_detected=True,
        burst_count=5,
        burst_transaction_ids=["TX_B1", "TX_B2"],
        rapid_in_out_detected=True,
        rapid_in_out_delay_seconds=95.0,
        rapid_in_out_ratio=0.92,
    )

    gf = GraphFeatures(
        account_id="ACC_ALPHA",
        has_cycle=True,
        cycle_count=1,
        cycles=[["ACC_ALPHA", "ACC_BETA", "ACC_GAMMA", "ACC_ALPHA"]],
        contributing_cycle_nodes=["ACC_ALPHA", "ACC_BETA", "ACC_GAMMA"],
        shared_device_count=3,
        associated_devices=["DEV_ALPHA_99", "DEV_BETA_88", "DEV_GAMMA_77"],
    )

    tab_pred = ModelPrediction(
        risk_score=85,
        fraud_probability=0.85,
        is_fraud=True,
        model_version="xgboost_v1.0.0",
        details={"status": "model_trained", "model_artifact_loaded": True},
    )

    fr = FusionResult(
        composite_risk_score=88.5,
        normalized_risk=0.885,
        risk_level=RiskLevel.CRITICAL,
        contributions={
            "rules": SignalContribution(
                modality=SignalModality.RULES,
                normalized_value=0.85,
                configured_weight=0.25,
                effective_weight=0.25,
                weighted_score=0.2125,
                is_available=True,
                explanation="Rules contributed 21.25 points.",
            ),
            "graph": SignalContribution(
                modality=SignalModality.GRAPH,
                normalized_value=1.0,
                configured_weight=0.20,
                effective_weight=0.20,
                weighted_score=0.20,
                is_available=True,
                explanation="Graph contributed 20.0 points.",
            ),
        },
        available_modalities=["rules", "temporal", "graph", "tabular_ml"],
        unavailable_modalities=["graph_ml"],
        effective_weights={"rules": 0.25, "graph": 0.20},
        missing_signal_policy=MissingSignalPolicy.RENORMALIZE_AVAILABLE,
        fusion_version="v1.0",
    )

    return EvidenceInput(
        transaction_event=event,
        rule_signals=eval_result,
        temporal_features=tf,
        graph_features=gf,
        tabular_prediction=tab_pred,
        fusion_result=fr,
    )


def test_evidence_generation_is_100_percent_deterministic() -> None:
    """Verify multiple executions on identical input yield byte-for-byte identical output."""
    engine = EvidenceEngine()
    inp = _build_rich_input()

    pkg1 = engine.generate_evidence(inp)
    pkg2 = engine.generate_evidence(inp)

    # 1. Exact preservation of M10 composite risk and risk level
    assert pkg1.composite_risk_score == 88.5
    assert pkg2.composite_risk_score == 88.5
    assert pkg1.risk_level == RiskLevel.CRITICAL
    assert pkg2.risk_level == RiskLevel.CRITICAL

    # 2. Total count equality
    assert pkg1.total_evidence_count == pkg2.total_evidence_count
    assert pkg1.total_evidence_count > 0

    # 3. Identical evidence IDs in exact same ranked order
    ids1 = [e.evidence_id for e in pkg1.evidence_items]
    ids2 = [e.evidence_id for e in pkg2.evidence_items]
    assert ids1 == ids2

    # 4. Identical ranks and severities
    ranks1 = [(e.rank, e.severity.value, e.source.value) for e in pkg1.evidence_items]
    ranks2 = [(e.rank, e.severity.value, e.source.value) for e in pkg2.evidence_items]
    assert ranks1 == ranks2

    # 5. Identical summary text
    assert pkg1.evidence_summary == pkg2.evidence_summary

    # 6. Identical dictionary serialization
    assert pkg1.to_dict() == pkg2.to_dict()
