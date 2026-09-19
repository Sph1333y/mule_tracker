"""
MuleTrace AI — Unit Tests for Evidence Models & Contracts.
"""

import pytest
from dataclasses import FrozenInstanceError

from app.engines.evidence.models import (
    EvidenceCategory,
    EvidenceInput,
    EvidenceItem,
    EvidencePackage,
    EvidenceSeverity,
    EvidenceSource,
    SourceCoverageStatus,
)
from app.engines.risk_fusion.models import RiskLevel


def test_evidence_enums() -> None:
    """Verify all evidence enums contain expected categorical values."""
    assert EvidenceSource.RULE.value == "RULE"
    assert EvidenceSource.TEMPORAL.value == "TEMPORAL"
    assert EvidenceSource.GRAPH.value == "GRAPH"
    assert EvidenceSource.TABULAR_ML.value == "TABULAR_ML"
    assert EvidenceSource.GRAPH_ML.value == "GRAPH_ML"
    assert EvidenceSource.RISK_FUSION.value == "RISK_FUSION"
    assert EvidenceSource.TRANSACTION.value == "TRANSACTION"

    assert EvidenceSeverity.CRITICAL.value == "CRITICAL"
    assert EvidenceSeverity.HIGH.value == "HIGH"
    assert EvidenceSeverity.MEDIUM.value == "MEDIUM"
    assert EvidenceSeverity.LOW.value == "LOW"
    assert EvidenceSeverity.INFO.value == "INFO"

    assert SourceCoverageStatus.AVAILABLE.value == "AVAILABLE"
    assert SourceCoverageStatus.UNAVAILABLE.value == "UNAVAILABLE"
    assert SourceCoverageStatus.MISSING.value == "MISSING"


def test_evidence_item_creation_and_immutability() -> None:
    """Verify EvidenceItem instantiates cleanly and is frozen/immutable."""
    item = EvidenceItem(
        evidence_id="EVD-RULE-R004-TEST1234",
        category=EvidenceCategory.RULE_VIOLATION,
        title="Rule R004 Triggered",
        description="Mule chain detected",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.RULE,
        source_reference="RULE:R004",
        transaction_ids=("TX101", "TX102"),
        account_ids=("ACC_01", "ACC_02"),
        metrics={"score": 40},
        rank=1,
    )

    assert item.evidence_id == "EVD-RULE-R004-TEST1234"
    assert item.severity == EvidenceSeverity.HIGH
    assert item.rank == 1

    # Verify immutability
    with pytest.raises(FrozenInstanceError):
        item.rank = 2  # type: ignore

    # Verify dictionary serialization
    d = item.to_dict()
    assert d["evidence_id"] == "EVD-RULE-R004-TEST1234"
    assert d["severity"] == "HIGH"
    assert d["source"] == "RULE"
    assert d["transaction_ids"] == ["TX101", "TX102"]


def test_evidence_input_creation() -> None:
    """Verify EvidenceInput handles optional inputs and summary representation."""
    inp = EvidenceInput(case_id="CAS-001", subject_id="ACC-999")
    assert inp.case_id == "CAS-001"
    assert inp.subject_id == "ACC-999"
    assert inp.transaction_event is None

    # Immutability check
    with pytest.raises(FrozenInstanceError):
        inp.case_id = "CAS-002"  # type: ignore

    summary = inp.to_dict()
    assert summary["has_transaction_event"] is False
    assert summary["has_fusion_result"] is False


def test_evidence_package_creation_and_immutability() -> None:
    """Verify EvidencePackage is immutable and serializes properly."""
    pkg = EvidencePackage(
        case_id="CAS-100",
        subject_id="ACC-001",
        transaction_id="TX-555",
        composite_risk_score=78.5,
        risk_level=RiskLevel.HIGH,
        evidence_items=(),
        evidence_summary="Case summary test.",
        source_coverage={"RULE": SourceCoverageStatus.AVAILABLE},
        total_evidence_count=0,
        severity_counts={"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
    )

    assert pkg.case_id == "CAS-100"
    assert pkg.composite_risk_score == 78.5
    assert pkg.risk_level == RiskLevel.HIGH

    with pytest.raises(FrozenInstanceError):
        pkg.composite_risk_score = 99.0  # type: ignore

    d = pkg.to_dict()
    assert d["composite_risk_score"] == 78.5
    assert d["risk_level"] == "HIGH"
    assert d["source_coverage"]["RULE"] == "AVAILABLE"
