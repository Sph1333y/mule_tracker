"""
MuleTrace AI — Deterministic Evidence Engine Models & Contracts.

Defines immutable data structures, enums, evidence items, and evidence packages
for Milestone 11 (Deterministic Evidence Engine).

Architectural Boundary:
- Cloud-agnostic and framework-neutral (pure Python standard library & domain types).
- Zero dependency on AWS (no boto3, Lambda, Neptune, etc.).
- Zero LLM dependency.
- Consumes M1-M10 outputs read-only and produces structured, traceable evidence.
- Preserves M10 composite risk score and risk level exactly without alteration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.domain.interfaces import ModelPrediction
from app.domain.models import TransactionEvent
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.engines.risk_fusion.models import FusionResult, RiskLevel
from app.engines.rules.base import EvaluationResult, RuleMatchResult
from app.engines.temporal.temporal_models import TemporalFeatures


class EvidenceSource(str, Enum):
    """Originating analytical subsystem providing the evidence."""

    RULE = "RULE"
    TEMPORAL = "TEMPORAL"
    GRAPH = "GRAPH"
    TABULAR_ML = "TABULAR_ML"
    GRAPH_ML = "GRAPH_ML"
    RISK_FUSION = "RISK_FUSION"
    TRANSACTION = "TRANSACTION"


class EvidenceCategory(str, Enum):
    """Forensic categorization of suspicious activity evidence."""

    RULE_VIOLATION = "RULE_VIOLATION"
    TEMPORAL_ANOMALY = "TEMPORAL_ANOMALY"
    TOPOLOGICAL_PATTERN = "TOPOLOGICAL_PATTERN"
    SHARED_INFRASTRUCTURE = "SHARED_INFRASTRUCTURE"
    CIRCULAR_ROUTING = "CIRCULAR_ROUTING"
    MODEL_PREDICTION = "MODEL_PREDICTION"
    RISK_FUSION_ASSESSMENT = "RISK_FUSION_ASSESSMENT"
    TRANSACTION_CONTEXT = "TRANSACTION_CONTEXT"


class EvidenceSeverity(str, Enum):
    """Deterministic severity classification of an evidence item."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SourceCoverageStatus(str, Enum):
    """Availability status of a detection source during evidence collection."""

    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    MISSING = "MISSING"


@dataclass(frozen=True)
class EvidenceItem:
    """A single granular, deterministic piece of forensic evidence.

    Attributes:
        evidence_id: Stable, deterministic identifier (e.g. 'EVD-RULE-R004-a1b2c3d4').
        category: Analytical classification of the evidence.
        title: Concise human-readable title.
        description: Factual, non-speculative narrative of the detected anomaly.
        severity: Evidence severity (INFO, LOW, MEDIUM, HIGH, CRITICAL).
        source: Originating analytical engine.
        source_reference: Machine-readable specific reference (e.g. 'RULE:R004').
        transaction_ids: Associated transaction identifiers.
        account_ids: Associated account identifiers.
        device_ids: Associated device fingerprints.
        ip_addresses: Associated IP address strings.
        timestamps: Associated event timestamps (ISO-8601).
        metrics: Concrete numeric/boolean metrics extracted from the source.
        rank: Priority ranking (1 = most critical/relevant).
    """

    evidence_id: str
    category: EvidenceCategory
    title: str
    description: str
    severity: EvidenceSeverity
    source: EvidenceSource
    source_reference: str
    transaction_ids: tuple[str, ...] = ()
    account_ids: tuple[str, ...] = ()
    device_ids: tuple[str, ...] = ()
    ip_addresses: tuple[str, ...] = ()
    timestamps: tuple[str, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert evidence item into a clean JSON-serializable dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "source": self.source.value,
            "source_reference": self.source_reference,
            "transaction_ids": list(self.transaction_ids),
            "account_ids": list(self.account_ids),
            "device_ids": list(self.device_ids),
            "ip_addresses": list(self.ip_addresses),
            "timestamps": list(self.timestamps),
            "metrics": self.metrics,
            "rank": self.rank,
        }


@dataclass(frozen=True)
class EvidenceInput:
    """Unified, immutable container of all upstream intelligence outputs for M11.

    All detection signals are optional to support partial or staggered pipelines.
    M11 consumes these objects strictly read-only without modifying them.
    """

    transaction_event: Optional[TransactionEvent] = None
    rule_signals: Optional[EvaluationResult | list[RuleMatchResult] | dict[str, Any]] = None
    temporal_features: Optional[TemporalFeatures] = None
    graph_features: Optional[GraphFeatures] = None
    tabular_prediction: Optional[ModelPrediction] = None
    graph_ml_prediction: Optional[ModelPrediction] = None
    fusion_result: Optional[FusionResult] = None
    case_id: Optional[str] = None
    subject_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert input presence summary to dictionary."""
        return {
            "has_transaction_event": self.transaction_event is not None,
            "has_rule_signals": self.rule_signals is not None,
            "has_temporal_features": self.temporal_features is not None,
            "has_graph_features": self.graph_features is not None,
            "has_tabular_prediction": self.tabular_prediction is not None,
            "has_graph_ml_prediction": self.graph_ml_prediction is not None,
            "has_fusion_result": self.fusion_result is not None,
            "case_id": self.case_id,
            "subject_id": self.subject_id,
        }


@dataclass(frozen=True)
class EvidencePackage:
    """Comprehensive, deterministic evidence package explaining a transaction's risk.

    Guarantees exact preservation of the M10 composite risk score and risk level.

    Attributes:
        case_id: Unique case identifier.
        subject_id: Focal subject (account or transaction) ID.
        transaction_id: Primary transaction reference if applicable.
        composite_risk_score: Preserved exactly from M10 ([0.0, 100.0]).
        risk_level: Preserved exactly from M10 (LOW, MEDIUM, HIGH, CRITICAL).
        evidence_items: Deterministically ranked and deduplicated evidence items.
        evidence_summary: Deterministic factual case narrative.
        source_coverage: Diagnostic coverage status per analytical source.
        total_evidence_count: Total number of evidence items.
        severity_counts: Breakdown of evidence counts by severity tier.
        metadata: Diagnostic and execution metadata.
        engine_version: Engine version identifier ('v1.0').
    """

    case_id: str
    subject_id: str
    transaction_id: Optional[str]
    composite_risk_score: float
    risk_level: RiskLevel
    evidence_items: tuple[EvidenceItem, ...]
    evidence_summary: str
    source_coverage: dict[str, SourceCoverageStatus]
    total_evidence_count: int
    severity_counts: dict[str, int]
    metadata: dict[str, Any] = field(default_factory=dict)
    engine_version: str = "v1.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert entire evidence package into a JSON-serializable dictionary."""
        return {
            "case_id": self.case_id,
            "subject_id": self.subject_id,
            "transaction_id": self.transaction_id,
            "composite_risk_score": round(self.composite_risk_score, 2),
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else str(self.risk_level),
            "evidence_items": [item.to_dict() for item in self.evidence_items],
            "evidence_summary": self.evidence_summary,
            "source_coverage": {k: v.value for k, v in self.source_coverage.items()},
            "total_evidence_count": self.total_evidence_count,
            "severity_counts": self.severity_counts,
            "metadata": self.metadata,
            "engine_version": self.engine_version,
        }
