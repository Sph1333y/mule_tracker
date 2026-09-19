"""
MuleTrace AI — Unit Tests for Milestone 12 Copilot Models & Immutability.
"""

import pytest
from dataclasses import FrozenInstanceError

from app.engines.ai.models import (
    ActionPriority,
    ActionType,
    InvestigationContext,
    InvestigationCopilotResponse,
    KeyFinding,
    SuggestedAction,
)
from app.engines.evidence.models import (
    EvidenceCategory,
    EvidenceItem,
    EvidencePackage,
    EvidenceSeverity,
    EvidenceSource,
)
from app.engines.risk_fusion.models import FusionResult, RiskLevel, MissingSignalPolicy


def test_investigation_context_creation_and_immutability():
    ctx = InvestigationContext(
        case_id="CAS-TEST-001",
        subject_id="ACC-TEST-01",
        transaction_id="TX-TEST-01",
        investigator_query="Review device linkages",
        metadata={"priority": "URGENT"},
    )
    assert ctx.case_id == "CAS-TEST-001"
    assert ctx.subject_id == "ACC-TEST-01"
    assert ctx.transaction_id == "TX-TEST-01"
    assert ctx.investigator_query == "Review device linkages"
    assert ctx.metadata["priority"] == "URGENT"

    # Verify frozen immutability
    with pytest.raises(FrozenInstanceError):
        ctx.case_id = "CAS-MUTATED"  # type: ignore

    d = ctx.to_dict()
    assert d["case_id"] == "CAS-TEST-001"
    assert d["has_fusion_result"] is False
    assert d["has_evidence_package"] is False


def test_key_finding_creation_and_serialization():
    kf = KeyFinding(
        finding="Rapid pass-through: 92% of funds depleted within 120s",
        evidence_ids=("EVD-001",),
        severity="HIGH",
        category="TEMPORAL_ANOMALY",
        source="TEMPORAL",
        metrics={"ratio": 0.92, "delay_seconds": 120},
    )
    assert kf.finding.startswith("Rapid pass-through")
    assert kf.evidence_ids == ("EVD-001",)
    assert kf.severity == "HIGH"

    # Immutability
    with pytest.raises(FrozenInstanceError):
        kf.finding = "Altered"  # type: ignore

    d = kf.to_dict()
    assert d["finding"] == kf.finding
    assert d["evidence_ids"] == ["EVD-001"]
    assert d["metrics"]["ratio"] == 0.92


def test_suggested_action_creation_and_serialization():
    action = SuggestedAction(
        action_id="ACT-DEV-001",
        title="Review shared device cluster",
        description="Inspect all accounts linked to the device fingerprint.",
        priority=ActionPriority.HIGH,
        action_type=ActionType.DEVICE_VERIFICATION,
        related_evidence_ids=("EVD-DEV-01", "EVD-DEV-02"),
    )
    assert action.action_id == "ACT-DEV-001"
    assert action.priority == ActionPriority.HIGH
    assert action.action_type == ActionType.DEVICE_VERIFICATION
    assert len(action.related_evidence_ids) == 2

    # Immutability
    with pytest.raises(FrozenInstanceError):
        action.priority = ActionPriority.LOW  # type: ignore

    d = action.to_dict()
    assert d["action_id"] == "ACT-DEV-001"
    assert d["priority"] == "HIGH"
    assert d["action_type"] == "DEVICE_VERIFICATION"
    assert d["related_evidence_ids"] == ["EVD-DEV-01", "EVD-DEV-02"]


def test_investigation_copilot_response_validation():
    kf = KeyFinding(
        finding="Cycle detected: A -> B -> C -> A",
        evidence_ids=("EVD-CYC-01",),
        severity="CRITICAL",
        category="CIRCULAR_ROUTING",
        source="RULE",
    )
    act = SuggestedAction(
        action_id="ACT-CYC-001",
        title="Trace circular fund routing cycle",
        description="Examine intermediary accounts in circular loop.",
        priority=ActionPriority.CRITICAL,
        action_type=ActionType.TOPOLOGY_ANALYSIS,
        related_evidence_ids=("EVD-CYC-01",),
    )
    resp = InvestigationCopilotResponse(
        case_id="CAS-01",
        subject_id="ACC-01",
        transaction_id="TX-01",
        composite_risk_score=94.5,
        risk_level="CRITICAL",
        risk_summary="Subject has CRITICAL risk posture.",
        investigation_summary="Critical circular routing detected across 3 accounts.",
        key_findings=(kf,),
        evidence_references=("EVD-CYC-01",),
        suggested_next_steps=(act,),
        follow_up_questions=("What counterparties participate in the cycle?",),
        limitations=("Generated deterministically without LLM.",),
        generation_metadata={"llm_used": False},
    )

    assert resp.composite_risk_score == 94.5
    assert resp.risk_level == "CRITICAL"
    assert len(resp.key_findings) == 1
    assert resp.evidence_references == ("EVD-CYC-01",)

    # Immutability
    with pytest.raises(FrozenInstanceError):
        resp.composite_risk_score = 50.0  # type: ignore

    d = resp.to_dict()
    assert d["composite_risk_score"] == 94.5
    assert d["risk_level"] == "CRITICAL"
    assert len(d["key_findings"]) == 1
    assert len(d["suggested_next_steps"]) == 1
    assert d["generation_metadata"]["llm_used"] is False
