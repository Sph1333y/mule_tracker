"""
MuleTrace AI — Deterministic Investigation Copilot Domain Models & Contracts.

Defines the immutable data structures, findings, actions, investigation contexts,
and response models for Milestone 12 (Deterministic Investigation Copilot).

Architectural Boundary:
- Cloud-agnostic and framework-neutral (pure Python standard library & domain types).
- Zero LLM dependency (no OpenAI, Gemini, Bedrock, Ollama, Claude, etc.).
- Zero external network dependency.
- Consumes M10 (FusionResult) and M11 (EvidencePackage) strictly read-only.
- Preserves M10 composite risk score and risk level exactly without alteration.
- Preserves M11 evidence IDs and references without fabrication or alteration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.engines.evidence.models import (
    EvidenceCategory,
    EvidenceItem,
    EvidencePackage,
    EvidenceSeverity,
    EvidenceSource,
)
from app.engines.risk_fusion.models import FusionResult, RiskLevel


class ActionPriority(str, Enum):
    """Priority level for recommended investigative review actions."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ActionType(str, Enum):
    """Categorical classification of investigative actions."""

    INVESTIGATIVE_REVIEW = "INVESTIGATIVE_REVIEW"
    COUNTERPARTY_VERIFICATION = "COUNTERPARTY_VERIFICATION"
    TOPOLOGY_ANALYSIS = "TOPOLOGY_ANALYSIS"
    TEMPORAL_AUDIT = "TEMPORAL_AUDIT"
    DEVICE_VERIFICATION = "DEVICE_VERIFICATION"
    MODEL_ANOMALY_REVIEW = "MODEL_ANOMALY_REVIEW"
    GENERAL_AUDIT = "GENERAL_AUDIT"


@dataclass(frozen=True)
class InvestigationContext:
    """Unified, immutable context for initiating a deterministic investigation.

    Attributes:
        case_id: Optional case tracking identifier.
        subject_id: Focal subject (account or entity) identifier.
        transaction_id: Primary transaction identifier under review.
        fusion_result: Upstream M10 Risk Fusion output (source of truth for risk).
        evidence_package: Upstream M11 Evidence Package (source of truth for evidence).
        investigator_query: Optional analyst query or review prompt.
        metadata: Diagnostic and audit metadata.
    """

    case_id: Optional[str] = None
    subject_id: Optional[str] = None
    transaction_id: Optional[str] = None
    fusion_result: Optional[FusionResult] = None
    evidence_package: Optional[EvidencePackage] = None
    investigator_query: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert investigation context into a serializable dictionary."""
        return {
            "case_id": self.case_id,
            "subject_id": self.subject_id,
            "transaction_id": self.transaction_id,
            "has_fusion_result": self.fusion_result is not None,
            "has_evidence_package": self.evidence_package is not None,
            "investigator_query": self.investigator_query,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class KeyFinding:
    """A factual, evidence-backed finding rendered deterministically from M11 evidence.

    Attributes:
        finding: Human-readable factual statement of the observed pattern.
        evidence_ids: Identifiers of the originating M11 EvidenceItems.
        severity: Severity tier inherited from M11 evidence.
        category: Forensic category inherited from M11 evidence.
        source: Analytical subsystem origin inherited from M11 evidence.
        metrics: Concrete numeric/boolean metrics supporting this finding.
    """

    finding: str
    evidence_ids: tuple[str, ...]
    severity: str
    category: str
    source: str
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert finding into a JSON-serializable dictionary."""
        return {
            "finding": self.finding,
            "evidence_ids": list(self.evidence_ids),
            "severity": self.severity,
            "category": self.category,
            "source": self.source,
            "metrics": self.metrics,
        }


@dataclass(frozen=True)
class SuggestedAction:
    """A deterministic, non-regulatory investigative action recommendation.

    Attributes:
        action_id: Stable identifier for the action (e.g. 'ACT-DEV-001').
        title: Concise title of the investigative step.
        description: Specific instruction for the investigator (non-punitive review).
        priority: Prioritization tier (CRITICAL, HIGH, MEDIUM, LOW).
        action_type: Category of investigation step.
        related_evidence_ids: Identifiers of supporting M11 evidence items.
    """

    action_id: str
    title: str
    description: str
    priority: ActionPriority
    action_type: ActionType
    related_evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert suggested action into a JSON-serializable dictionary."""
        return {
            "action_id": self.action_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "action_type": self.action_type.value,
            "related_evidence_ids": list(self.related_evidence_ids),
        }


@dataclass(frozen=True)
class InvestigationCopilotResponse:
    """Comprehensive, deterministic investigation response produced by M12 Copilot.

    Guarantees:
    - Zero LLM generation or probabilistic hallucination.
    - Exact preservation of M10 composite risk score and risk level.
    - 100% validity of referenced evidence IDs against M11 EvidencePackage.
    - Strictly non-punitive, evidence-based recommendations.

    Attributes:
        case_id: Case identifier if present.
        subject_id: Subject identifier if present.
        transaction_id: Transaction identifier if present.
        composite_risk_score: Preserved exactly from M10 ([0.0, 100.0]).
        risk_level: Preserved exactly from M10 (LOW, MEDIUM, HIGH, CRITICAL).
        risk_summary: Deterministic synthesis of risk score and modality contributions.
        investigation_summary: Structured executive narrative explaining detected anomalies.
        key_findings: Deterministically ranked factual findings with M11 evidence links.
        evidence_references: Ordered tuple of all valid M11 evidence IDs referenced.
        suggested_next_steps: Deterministic investigative actions for compliance review.
        follow_up_questions: Targeted investigative questions derived from evidence.
        limitations: Explicit diagnostic boundaries and coverage audit notes.
        generation_metadata: Execution metadata confirming deterministic generation.
    """

    case_id: Optional[str]
    subject_id: Optional[str]
    transaction_id: Optional[str]
    composite_risk_score: float
    risk_level: str
    risk_summary: str
    investigation_summary: str
    key_findings: tuple[KeyFinding, ...]
    evidence_references: tuple[str, ...]
    suggested_next_steps: tuple[SuggestedAction, ...]
    follow_up_questions: tuple[str, ...]
    limitations: tuple[str, ...]
    generation_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert copilot response into a clean JSON-serializable dictionary."""
        return {
            "case_id": self.case_id,
            "subject_id": self.subject_id,
            "transaction_id": self.transaction_id,
            "composite_risk_score": round(self.composite_risk_score, 2),
            "risk_level": self.risk_level,
            "risk_summary": self.risk_summary,
            "investigation_summary": self.investigation_summary,
            "key_findings": [kf.to_dict() for kf in self.key_findings],
            "evidence_references": list(self.evidence_references),
            "suggested_next_steps": [action.to_dict() for action in self.suggested_next_steps],
            "follow_up_questions": list(self.follow_up_questions),
            "limitations": list(self.limitations),
            "generation_metadata": self.generation_metadata,
        }
