"""
MuleTrace AI — Investigation and SOC Integration Schemas.

Pydantic schemas for investigation case details, intelligence enrichment,
multi-modal risk contributions, structured evidence, and copilot findings (Milestone 13).
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ModalityContributionRead(BaseModel):
    """Explainability detail for a single modality's contribution to composite risk."""

    modality: str = Field(..., description="Modality name (rules, temporal, graph, tabular_ml, graph_ml)")
    normalized_value: float = Field(..., ge=0.0, le=1.0, description="Normalized signal value in [0.0, 1.0]")
    configured_weight: float = Field(..., ge=0.0, le=1.0, description="Static configured weight")
    effective_weight: float = Field(..., ge=0.0, le=1.0, description="Effective weight after re-normalization")
    weighted_score: float = Field(..., description="Weighted contribution to composite risk score")
    is_available: bool = Field(..., description="Whether modality signal was present")
    explanation: str = Field(default="", description="Mathematical narrative of contribution")


class EvidenceItemRead(BaseModel):
    """Structured evidence item consumed from M11 Evidence Engine."""

    evidence_id: str = Field(..., description="Unique deterministic evidence reference string")
    category: str = Field(..., description="Analytical category enum string")
    title: str = Field(..., description="Concise title of the evidence")
    description: str = Field(..., description="Factual evidence description")
    severity: str = Field(..., description="Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)")
    source: str = Field(..., description="Originating detection modality")
    source_reference: Optional[str] = Field(default=None, description="Rule code or model reference")
    transaction_ids: list[str] = Field(default_factory=list, description="Associated transaction IDs")
    account_ids: list[str] = Field(default_factory=list, description="Associated account IDs")
    device_ids: list[str] = Field(default_factory=list, description="Associated device IDs")
    ip_addresses: list[str] = Field(default_factory=list, description="Associated IP addresses")
    timestamps: list[str] = Field(default_factory=list, description="Associated timestamps")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Underlying metric key-value pairs")


class KeyFindingRead(BaseModel):
    """Forensic finding synthesized from M12 Copilot."""

    finding: str = Field(..., description="Human-readable factual statement of the observed pattern")
    evidence_ids: list[str] = Field(default_factory=list, description="Linked M11 evidence IDs")
    severity: str = Field(..., description="Severity tier inherited from M11 evidence")
    category: str = Field(..., description="Forensic category inherited from M11 evidence")
    source: str = Field(..., description="Analytical subsystem origin inherited from M11 evidence")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Concrete numeric/boolean metrics")


class SuggestedActionRead(BaseModel):
    """Actionable investigative recommendation synthesized from M12 Copilot."""

    action_id: str = Field(..., description="Stable identifier for the action (e.g. 'ACT-DEV-001')")
    title: str = Field(..., description="Concise title of the investigative step")
    description: str = Field(..., description="Specific non-punitive review instruction")
    priority: str = Field(..., description="Prioritization tier (CRITICAL, HIGH, MEDIUM, LOW)")
    action_type: str = Field(..., description="Category of investigation step")
    related_evidence_ids: list[str] = Field(default_factory=list, description="Identifiers of supporting evidence")


class InvestigationIntelligenceData(BaseModel):
    """Complete multi-modal intelligence package linking M10, M11, and M12."""

    case_id: str = Field(..., description="Investigation case identifier")
    subject_id: str = Field(..., description="Focal account or entity identifier")
    transaction_id: Optional[str] = Field(default=None, description="Primary transaction reference")
    composite_risk_score: float = Field(..., ge=0.0, le=100.0, description="M10 composite risk score (0-100)")
    risk_level: str = Field(..., description="M10 categorical risk level (LOW, MEDIUM, HIGH, CRITICAL)")
    risk_contributions: list[ModalityContributionRead] = Field(default_factory=list, description="M10 modality signal contributions")
    total_evidence_count: int = Field(default=0, description="Total number of M11 evidence items")
    severity_counts: dict[str, int] = Field(default_factory=dict, description="Counts by severity tier")
    evidence_items: list[EvidenceItemRead] = Field(default_factory=list, description="Ranked M11 evidence items")
    evidence_summary: str = Field(default="", description="Factual M11 evidence package summary")
    risk_summary: str = Field(default="", description="M12 deterministic risk posture summary")
    investigation_summary: str = Field(default="", description="M12 deterministic narrative synthesis")
    key_findings: list[KeyFindingRead] = Field(default_factory=list, description="M12 grounded key findings")
    suggested_next_steps: list[SuggestedActionRead] = Field(default_factory=list, description="M12 prioritized investigative actions")
    evidence_references: list[str] = Field(default_factory=list, description="M12 referenced evidence IDs")
    follow_up_questions: list[str] = Field(default_factory=list, description="M12 structured follow-up questions")
    limitations: list[str] = Field(default_factory=list, description="Data coverage and audit limitations")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp")
    is_degraded: bool = Field(default=False, description="Whether this response fell back due to partial service degradation")


class CaseDetailRead(BaseModel):
    """Detailed metadata for an investigation case."""

    case_number: str = Field(..., description="Unique case number (e.g. CAS-2025-0045)")
    title: str = Field(..., description="Case title")
    priority: str = Field(..., description="Priority (LOW, MEDIUM, HIGH, CRITICAL)")
    case_status: str = Field(..., description="Status (OPEN, IN_PROGRESS, CLOSED_CONFIRMED, etc.)")
    assigned_investigator_id: Optional[str] = Field(default=None, description="Assigned investigator ID")
    alerts_count: int = Field(default=0, description="Number of linked alerts")
    focal_subject_id: Optional[str] = Field(default=None, description="Primary focal account/subject")
    total_volume: Optional[str] = Field(default=None, description="Combined financial volume")
    linked_accounts: list[str] = Field(default_factory=list, description="List of linked account numbers")


class InvestigationEnrichRequest(BaseModel):
    """Payload for on-demand intelligence enrichment."""

    case_id: Optional[str] = Field(default=None, description="Case identifier")
    subject_id: Optional[str] = Field(default=None, description="Focal subject / account identifier")
    transaction_event: Optional[dict[str, Any]] = Field(default=None, description="Optional raw transaction event dictionary")
    history: Optional[list[dict[str, Any]]] = Field(default=None, description="Optional historical transaction events")
