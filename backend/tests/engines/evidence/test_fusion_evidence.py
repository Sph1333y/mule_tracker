"""
MuleTrace AI — Unit Tests for Risk Fusion Evidence Extraction (M10).
"""

from app.engines.evidence.collectors import collect_fusion_evidence
from app.engines.evidence.models import EvidenceCategory, EvidenceSeverity, EvidenceSource
from app.engines.risk_fusion.models import (
    FusionResult,
    MissingSignalPolicy,
    RiskLevel,
    SignalContribution,
    SignalModality,
)


def _create_sample_fusion_result() -> FusionResult:
    contrib_rules = SignalContribution(
        modality=SignalModality.RULES,
        normalized_value=0.85,
        configured_weight=0.25,
        effective_weight=0.2941,
        weighted_score=0.250,
        is_available=True,
        explanation="Rules contributed 25.0 points based on R004 and R006.",
    )
    contrib_graph = SignalContribution(
        modality=SignalModality.GRAPH,
        normalized_value=1.0,
        configured_weight=0.20,
        effective_weight=0.2353,
        weighted_score=0.2353,
        is_available=True,
        explanation="Graph contributed 23.5 points based on circular fund loop.",
    )
    contrib_temporal = SignalContribution(
        modality=SignalModality.TEMPORAL,
        normalized_value=0.20,
        configured_weight=0.15,
        effective_weight=0.1765,
        weighted_score=0.0353,
        is_available=True,
        explanation="Temporal contributed 3.5 points (minor pass-through).",
    )

    return FusionResult(
        composite_risk_score=82.4,
        normalized_risk=0.824,
        risk_level=RiskLevel.HIGH,
        contributions={
            "rules": contrib_rules,
            "graph": contrib_graph,
            "temporal": contrib_temporal,
        },
        available_modalities=["rules", "graph", "temporal"],
        unavailable_modalities=["tabular_ml", "graph_ml"],
        effective_weights={"rules": 0.2941, "graph": 0.2353, "temporal": 0.1765},
        missing_signal_policy=MissingSignalPolicy.RENORMALIZE_AVAILABLE,
        metadata={"transaction_id": "TX_TEST_101"},
        fusion_version="v1.0",
    )


def test_collect_fusion_evidence_composite_and_contributions() -> None:
    """Verify fusion result generates composite summary and modality breakdowns."""
    fr = _create_sample_fusion_result()
    items = collect_fusion_evidence(fr)

    # 1 composite assessment + 2 major contributors (rules: 25.0 pts, graph: 23.5 pts; temporal < 15 pts)
    assert len(items) == 3

    refs = [i.source_reference for i in items]
    assert "RISK_FUSION:v1.0" in refs
    assert "RISK_FUSION:contribution_rules" in refs
    assert "RISK_FUSION:contribution_graph" in refs
    assert "RISK_FUSION:contribution_temporal" not in refs  # below 15 point threshold

    composite_item = next(i for i in items if i.source_reference == "RISK_FUSION:v1.0")
    assert composite_item.category == EvidenceCategory.RISK_FUSION_ASSESSMENT
    assert composite_item.severity == EvidenceSeverity.HIGH  # matching M10 RiskLevel.HIGH
    assert composite_item.metrics["composite_risk_score"] == 82.4
    assert composite_item.metrics["risk_level"] == "HIGH"

    rules_item = next(i for i in items if i.source_reference == "RISK_FUSION:contribution_rules")
    assert rules_item.severity == EvidenceSeverity.HIGH  # 25.0 pts >= 20.0
    assert rules_item.metrics["contribution_points"] == 25.0


def test_collect_fusion_evidence_none() -> None:
    """Verify None fusion result returns empty list."""
    assert collect_fusion_evidence(None) == []
