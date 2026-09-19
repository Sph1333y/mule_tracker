"""
MuleTrace AI — Deterministic Evidence Engine Package.

Provides a unified, cloud-agnostic, deterministic evidence subsystem (Milestone 11)
that consumes detection outputs across M1-M10 and synthesizes structured, traceable,
deduplicated EvidencePackage instances without altering upstream risk scores.
"""

from __future__ import annotations

from app.engines.evidence.collectors import (
    collect_fusion_evidence,
    collect_graph_evidence,
    collect_ml_evidence,
    collect_rule_evidence,
    collect_temporal_evidence,
    collect_transaction_evidence,
)
from app.engines.evidence.deduplication import deduplicate_evidence_items
from app.engines.evidence.engine import EvidenceEngine, evidence_engine
from app.engines.evidence.models import (
    EvidenceCategory,
    EvidenceInput,
    EvidenceItem,
    EvidencePackage,
    EvidenceSeverity,
    EvidenceSource,
    SourceCoverageStatus,
)
from app.engines.evidence.provenance import (
    generate_case_id,
    generate_evidence_id,
    validate_provenance,
)
from app.engines.evidence.ranking import rank_evidence_items
from app.engines.evidence.renderer import render_evidence_summary

__all__ = [
    # Models & Enums
    "EvidenceCategory",
    "EvidenceInput",
    "EvidenceItem",
    "EvidencePackage",
    "EvidenceSeverity",
    "EvidenceSource",
    "SourceCoverageStatus",
    # Engine & Facade
    "EvidenceEngine",
    "evidence_engine",
    # Collectors
    "collect_fusion_evidence",
    "collect_graph_evidence",
    "collect_ml_evidence",
    "collect_rule_evidence",
    "collect_temporal_evidence",
    "collect_transaction_evidence",
    # Provenance, Deduplication & Ranking
    "generate_case_id",
    "generate_evidence_id",
    "validate_provenance",
    "deduplicate_evidence_items",
    "rank_evidence_items",
    "render_evidence_summary",
]
