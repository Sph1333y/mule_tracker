"""
MuleTrace AI — Unit Tests for Missing Data Handling.
"""

from app.domain.interfaces import ModelPrediction
from app.engines.evidence.engine import EvidenceEngine
from app.engines.evidence.models import EvidenceInput, SourceCoverageStatus
from app.engines.risk_fusion.models import RiskLevel
from app.engines.rules.base import EvaluationResult, RuleMatchResult


def test_all_sources_missing() -> None:
    """Verify engine handles empty inputs gracefully without exceptions or hallucinations."""
    engine = EvidenceEngine()
    empty_input = EvidenceInput()

    pkg = engine.generate_evidence(empty_input)

    assert pkg.total_evidence_count == 0
    assert len(pkg.evidence_items) == 0
    assert pkg.composite_risk_score == 0.0
    assert pkg.risk_level == RiskLevel.LOW
    assert "No suspicious forensic evidence items were detected" in pkg.evidence_summary

    # All sources should be flagged MISSING
    for src in ["RULE", "TEMPORAL", "GRAPH", "TABULAR_ML", "GRAPH_ML", "RISK_FUSION", "TRANSACTION"]:
        assert pkg.source_coverage[src] == SourceCoverageStatus.MISSING


def test_partial_sources_coverage() -> None:
    """Verify coverage flags accurately distinguish between available and missing modalities."""
    engine = EvidenceEngine()
    eval_res = EvaluationResult(
        total_risk_score_delta=30,
        matches=[
            RuleMatchResult(
                rule_code="R001",
                rule_name="Velocity",
                pattern_name="Spike",
                matched=True,
                score_contribution=30,
                severity="MEDIUM",
                narrative="Velocity alert.",
            )
        ],
    )

    partial_input = EvidenceInput(
        rule_signals=eval_res,
        subject_id="ACC_TARGET",
    )

    pkg = engine.generate_evidence(partial_input)

    assert pkg.total_evidence_count == 1
    assert pkg.source_coverage["RULE"] == SourceCoverageStatus.AVAILABLE
    assert pkg.source_coverage["TEMPORAL"] == SourceCoverageStatus.MISSING
    assert pkg.source_coverage["GRAPH"] == SourceCoverageStatus.MISSING
    assert pkg.source_coverage["TABULAR_ML"] == SourceCoverageStatus.MISSING
    assert pkg.source_coverage["GRAPH_ML"] == SourceCoverageStatus.MISSING


def test_unavailable_model_distinguished_from_clean() -> None:
    """Verify offline or un-trained ML models are categorized as UNAVAILABLE."""
    engine = EvidenceEngine()
    unavail_pred = ModelPrediction(
        risk_score=0,
        fraud_probability=0.0,
        is_fraud=False,
        model_version="xgboost_v1.0.0_fallback",
        details={"status": "model_unavailable", "model_artifact_loaded": False},
    )

    inp = EvidenceInput(tabular_prediction=unavail_pred)
    pkg = engine.generate_evidence(inp)

    assert pkg.source_coverage["TABULAR_ML"] == SourceCoverageStatus.UNAVAILABLE
    assert pkg.total_evidence_count == 0  # no fake evidence created for unavailable model
