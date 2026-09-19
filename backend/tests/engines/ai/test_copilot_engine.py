"""
MuleTrace AI — Unit Tests for DeterministicInvestigationCopilot Engine & Domain Port.
"""

import pytest

from app.domain.interfaces import InvestigationCopilot
from app.engines.ai.copilot import DeterministicInvestigationCopilot
from app.engines.ai.models import InvestigationContext
from app.engines.evidence.models import (
    EvidenceCategory,
    EvidenceItem,
    EvidencePackage,
    EvidenceSeverity,
    EvidenceSource,
)
from app.engines.risk_fusion.models import (
    FusionResult,
    MissingSignalPolicy,
    RiskLevel,
    SignalContribution,
    SignalModality,
)


@pytest.fixture
def copilot() -> DeterministicInvestigationCopilot:
    return DeterministicInvestigationCopilot()


@pytest.fixture
def sample_evidence_package() -> EvidencePackage:
    item1 = EvidenceItem(
        evidence_id="EVD-RULE-001",
        category=EvidenceCategory.RULE_VIOLATION,
        title="High Value Anomaly",
        description="Transaction amount deviates from customer history",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.RULE,
        source_reference="RULE:R001",
    )
    item2 = EvidenceItem(
        evidence_id="EVD-TEMP-002",
        category=EvidenceCategory.TEMPORAL_ANOMALY,
        title="Rapid Pass-Through",
        description="95% of incoming funds transferred within 90s",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.TEMPORAL,
        source_reference="TEMPORAL:pass_through_ratio",
    )
    return EvidencePackage(
        case_id="CAS-EVD-99",
        subject_id="ACC-FOCAL-99",
        transaction_id="TX-99",
        composite_risk_score=88.4,
        risk_level=RiskLevel.HIGH,
        evidence_items=(item1, item2),
        evidence_summary="High value anomaly and rapid pass-through",
        source_coverage={},
        total_evidence_count=2,
        severity_counts={"HIGH": 2},
    )


@pytest.fixture
def sample_fusion_result() -> FusionResult:
    contrib = SignalContribution(
        modality=SignalModality.RULES,
        normalized_value=0.88,
        configured_weight=0.30,
        effective_weight=0.30,
        weighted_score=0.264,
        is_available=True,
        explanation="Rule score 88.0",
    )
    return FusionResult(
        composite_risk_score=88.4,
        normalized_risk=0.884,
        risk_level=RiskLevel.HIGH,
        contributions={"rules": contrib},
        available_modalities=["rules"],
        unavailable_modalities=["graph_ml"],
        effective_weights={"rules": 0.30},
        missing_signal_policy=MissingSignalPolicy.RENORMALIZE_AVAILABLE,
    )


def test_copilot_is_instance_of_domain_port(copilot):
    assert isinstance(copilot, InvestigationCopilot)


@pytest.mark.asyncio
async def test_domain_port_generate_narrative(copilot, sample_evidence_package):
    narrative = await copilot.generate_narrative(sample_evidence_package.to_dict())
    assert isinstance(narrative, str)
    assert "88.40/100.0" in narrative
    assert "ACC-FOCAL-99" in narrative
    assert "HIGH" in narrative


@pytest.mark.asyncio
async def test_domain_port_suggest_next_steps(copilot, sample_evidence_package):
    steps = await copilot.suggest_next_steps(sample_evidence_package.to_dict())
    assert isinstance(steps, list)
    assert len(steps) > 0
    assert any("Audit rapid pass-through" in s for s in steps)


@pytest.mark.asyncio
async def test_full_investigate_pipeline(copilot, sample_evidence_package, sample_fusion_result):
    ctx = InvestigationContext(
        case_id="CAS-EVD-99",
        subject_id="ACC-FOCAL-99",
        transaction_id="TX-99",
        fusion_result=sample_fusion_result,
        evidence_package=sample_evidence_package,
    )

    response = await copilot.investigate(ctx)

    # Risk score preservation
    assert response.composite_risk_score == 88.4
    assert response.risk_level == "HIGH"

    # Evidence preservation
    assert response.evidence_references == ("EVD-RULE-001", "EVD-TEMP-002")
    assert len(response.key_findings) == 2

    # Verify findings reference actual evidence items
    for kf in response.key_findings:
        for eid in kf.evidence_ids:
            assert eid in response.evidence_references

    # Zero LLM guarantee
    assert response.generation_metadata["llm_used"] is False
    assert response.generation_metadata["deterministic"] is True


def test_copilot_coercion_handles_invalid_data(copilot):
    # Ensure invalid or empty input does not crash copilot
    pkg, score, level, sub = copilot._coerce_evidence_input(None)
    assert pkg is None
    assert score == 0.0
    assert level == "LOW"

    # Malformed dictionary
    pkg, score, level, sub = copilot._coerce_evidence_input({"unknown_field": 123})
    assert pkg is not None
    assert score == 0.0
    assert level == "LOW"
