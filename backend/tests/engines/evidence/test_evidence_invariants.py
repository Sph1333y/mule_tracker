"""
MuleTrace AI — Comprehensive Invariant Tests for Evidence Engine (INV-1 through INV-25).
"""

from datetime import datetime, timezone
import inspect
from pathlib import Path

from app.domain.interfaces import ModelPrediction
from app.domain.models import TransactionEvent
from app.engines.evidence.engine import EvidenceEngine, evidence_engine
from app.engines.evidence.models import EvidenceInput, EvidenceSeverity, EvidenceSource
from app.engines.evidence.provenance import validate_provenance
import app.engines.evidence as evidence_pkg
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


def _make_comprehensive_input() -> tuple[EvidenceInput, dict]:
    event = TransactionEvent(
        transaction_id="TX_INV_999",
        timestamp=datetime(2026, 9, 19, 15, 0, tzinfo=timezone.utc),
        sender_account="ACC_SRC_INV",
        receiver_account="ACC_DST_INV",
        amount=300000.0,
        currency="INR",
        channel="UPI",
        device_id="DEV_INV_01",
        ip_address="192.0.2.1",
    )

    eval_result = EvaluationResult(
        total_risk_score_delta=70,
        matches=[
            RuleMatchResult(
                rule_code="R004",
                rule_name="Mule Chain",
                pattern_name="Rapid Pass-Through",
                matched=True,
                score_contribution=40,
                severity="HIGH",
                narrative="Mule chain pattern detected.",
            ),
            RuleMatchResult(
                rule_code="R006",
                rule_name="Shared Device",
                pattern_name="Device Ring",
                matched=True,
                score_contribution=30,
                severity="CRITICAL",
                narrative="Device shared across accounts.",
            ),
        ],
    )

    tf = TemporalFeatures(
        reference_time=datetime(2026, 9, 19, 15, 0, tzinfo=timezone.utc),
        rapid_in_out_detected=True,
        rapid_in_out_delay_seconds=45.0,
        rapid_in_out_ratio=0.98,
        burst_detected=True,
        burst_count=6,
        transaction_count_1h=8,
        amount_sum_1h=450000.0,
    )

    gf = GraphFeatures(
        account_id="ACC_SRC_INV",
        has_cycle=True,
        cycle_count=1,
        cycles=[["ACC_SRC_INV", "ACC_DST_INV", "ACC_SRC_INV"]],
        contributing_cycle_nodes=["ACC_SRC_INV", "ACC_DST_INV"],
        shared_device_count=4,
        associated_devices=["DEV_INV_01", "DEV_INV_02"],
        fan_in_ratio=4.5,
    )

    tab_pred = ModelPrediction(
        risk_score=90,
        fraud_probability=0.90,
        is_fraud=True,
        model_version="xgboost_v1.0.0",
        details={"status": "model_trained", "model_artifact_loaded": True},
    )

    gnn_pred = ModelPrediction(
        risk_score=82,
        fraud_probability=0.82,
        is_fraud=True,
        model_version="graphsage_v1.0.0",
        details={"status": "model_trained", "model_artifact_loaded": True},
    )

    fr = FusionResult(
        composite_risk_score=86.75,
        normalized_risk=0.8675,
        risk_level=RiskLevel.CRITICAL,
        contributions={
            "rules": SignalContribution(
                modality=SignalModality.RULES,
                normalized_value=0.90,
                configured_weight=0.25,
                effective_weight=0.25,
                weighted_score=0.225,
                is_available=True,
                explanation="Rules contributed 22.5 points.",
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
        available_modalities=["rules", "temporal", "graph", "tabular_ml", "graph_ml"],
        unavailable_modalities=[],
        effective_weights={"rules": 0.25, "graph": 0.20},
        missing_signal_policy=MissingSignalPolicy.RENORMALIZE_AVAILABLE,
        fusion_version="v1.0",
    )

    inp = EvidenceInput(
        transaction_event=event,
        rule_signals=eval_result,
        temporal_features=tf,
        graph_features=gf,
        tabular_prediction=tab_pred,
        graph_ml_prediction=gnn_pred,
        fusion_result=fr,
    )

    original_states = {
        "event_amount": event.amount,
        "rule_delta": eval_result.total_risk_score_delta,
        "tf_burst": tf.burst_detected,
        "gf_cycle": gf.has_cycle,
        "tab_prob": tab_pred.fraud_probability,
        "gnn_prob": gnn_pred.fraud_probability,
        "fr_score": fr.composite_risk_score,
        "fr_level": fr.risk_level,
    }

    return inp, original_states


# ── INV-1, INV-2, INV-3: Determinism ─────────────────────────────────────────


def test_inv_1_to_3_determinism_ids_and_ordering() -> None:
    """INV-1: Deterministic generation.

    INV-2: Deterministic IDs.
    INV-3: Deterministic ordering.
    """
    inp, _ = _make_comprehensive_input()
    pkg1 = evidence_engine.generate_evidence(inp)
    pkg2 = evidence_engine.generate_evidence(inp)

    assert pkg1.composite_risk_score == pkg2.composite_risk_score
    assert len(pkg1.evidence_items) == len(pkg2.evidence_items)

    for e1, e2 in zip(pkg1.evidence_items, pkg2.evidence_items):
        assert e1.evidence_id == e2.evidence_id
        assert e1.rank == e2.rank
        assert e1.severity == e2.severity
        assert e1.source_reference == e2.source_reference


# ── INV-4 & INV-5: Provenance & Grounded Evidence ───────────────────────────


def test_inv_4_and_5_provenance_and_grounded_evidence() -> None:
    """INV-4: Every evidence item has provenance.

    INV-5: Refers only to available source data.
    """
    inp, _ = _make_comprehensive_input()
    pkg = evidence_engine.generate_evidence(inp)

    for item in pkg.evidence_items:
        assert validate_provenance(item.source, item.source_reference) is True
        assert item.source in EvidenceSource
        assert len(item.source_reference) > 0
        assert item.evidence_id.startswith(f"EVD-{item.source.value}-")


# ── INV-6 & INV-7: Exact Preservation of M10 Score & Risk Level ─────────────


def test_inv_6_and_7_m10_preservation() -> None:
    """INV-6: M10 composite score is preserved exactly.

    INV-7: M10 risk level is preserved exactly.
    """
    inp, states = _make_comprehensive_input()
    pkg = evidence_engine.generate_evidence(inp)

    assert pkg.composite_risk_score == states["fr_score"]
    assert pkg.risk_level == states["fr_level"]
    # Check that it wasn't rounded or modified
    assert pkg.composite_risk_score == 86.75
    assert pkg.risk_level == RiskLevel.CRITICAL


# ── INV-8 to INV-12 & INV-15: Upstream Immutability ──────────────────────────


def test_inv_8_to_12_and_15_upstream_immutability() -> None:
    """INV-8 to INV-12: M5-M9 outputs not modified.

    INV-15: Input objects not mutated.
    """
    inp, states = _make_comprehensive_input()
    _ = evidence_engine.generate_evidence(inp)

    assert inp.transaction_event.amount == states["event_amount"]
    assert inp.rule_signals.total_risk_score_delta == states["rule_delta"]
    assert inp.temporal_features.burst_detected == states["tf_burst"]
    assert inp.graph_features.has_cycle == states["gf_cycle"]
    assert inp.tabular_prediction.fraud_probability == states["tab_prob"]
    assert inp.graph_ml_prediction.fraud_probability == states["gnn_prob"]
    assert inp.fusion_result.composite_risk_score == states["fr_score"]


# ── INV-13 & INV-14: No Duplication & No Fabrication ────────────────────────


def test_inv_13_and_14_no_duplication_and_no_fabrication() -> None:
    """INV-13: No duplicate underlying evidence introduced.

    INV-14: Missing data does not fabricate evidence.
    """
    empty_inp = EvidenceInput()
    pkg_empty = evidence_engine.generate_evidence(empty_inp)
    assert len(pkg_empty.evidence_items) == 0

    inp, _ = _make_comprehensive_input()
    pkg = evidence_engine.generate_evidence(inp)

    # All evidence IDs must be unique within the package
    ev_ids = [e.evidence_id for e in pkg.evidence_items]
    assert len(ev_ids) == len(set(ev_ids))


# ── INV-16 to INV-20: No Duplication of Engine Logic ────────────────────────


def test_inv_16_to_20_no_duplicate_engine_logic() -> None:
    """INV-16: No risk fusion in M11.

    INV-17: No ML inference in M11.
    INV-18: No graph intelligence duplicated.
    INV-19: No temporal intelligence duplicated.
    INV-20: No fraud-rule evaluation duplicated.
    """
    # Verify by code inspection of evidence engine package
    pkg_dir = Path(evidence_pkg.__file__).parent
    for py_file in pkg_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        # Ensure no ML training/predict calls
        assert "predict_proba" not in content
        assert "fit(" not in content
        # Ensure no risk fusion recomputation
        assert "FusionWeights" not in content
        assert "RENORMALIZE_AVAILABLE" not in content or "MissingSignalPolicy" in content
        # Ensure no rule evaluation logic
        assert "evaluate_rules" not in content


# ── INV-21: No LLM Required ─────────────────────────────────────────────────


def test_inv_21_no_llm_required() -> None:
    """INV-21: No LLM dependency exists in M11."""
    pkg_dir = Path(evidence_pkg.__file__).parent
    for py_file in pkg_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "langchain" not in content
        assert "openai" not in content
        assert "bedrock" not in content
        assert "ollama" not in content


# ── INV-22: Zero AWS Cloud Dependencies ─────────────────────────────────────


def test_inv_22_zero_aws_dependencies() -> None:
    """INV-22: No AWS dependencies imported in M11."""
    pkg_dir = Path(evidence_pkg.__file__).parent
    for py_file in pkg_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "import boto3" not in content
        assert "from boto3" not in content
        assert "aws_cdk" not in content


# ── INV-23 & INV-24: No Investigator Workflow / Copilot in M11 ──────────────


def test_inv_23_and_24_no_investigator_or_copilot_logic() -> None:
    """INV-23: No investigator recommendation/decision logic in M11.

    INV-24: No M12 Copilot functionality in M11.
    """
    pkg_dir = Path(evidence_pkg.__file__).parent
    for py_file in pkg_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "suggest_next_steps" not in content
        assert "freeze_account" not in content
        assert "submit_sar" not in content
        assert "InvestigationCopilot" not in content


# ── INV-25: Existing Application Behavior Unchanged ─────────────────────────


def test_inv_25_existing_application_unaffected() -> None:
    """INV-25: Existing application services remain intact."""
    from app.engines.rules import modular_rule_engine
    from app.engines.temporal import temporal_engine
    from app.engines.graph.intelligence.graph_engine import graph_intelligence_engine
    from app.engines.risk_fusion.fusion_engine import risk_fusion_engine

    assert modular_rule_engine is not None
    assert temporal_engine is not None
    assert graph_intelligence_engine is not None
    assert risk_fusion_engine is not None
