"""
MuleTrace AI — Deterministic Evidence Engine.

Orchestrates multi-modal evidence collection, deduplication, ranking, and packaging
while strictly preserving M10 risk scores and risk levels without recalculation.

Architectural Boundary:
- Strictly additive: consumes outputs from M1-M10 without mutating them.
- Deterministic: identical inputs produce identical EvidencePackage instances.
- Zero recalculation of M10 composite risk or risk level.
- Zero LLM dependency.
- Zero AWS cloud dependency.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.domain.interfaces import ModelPrediction
from app.domain.models import TransactionEvent
from app.engines.evidence.collectors import (
    collect_fusion_evidence,
    collect_graph_evidence,
    collect_ml_evidence,
    collect_rule_evidence,
    collect_temporal_evidence,
    collect_transaction_evidence,
)
from app.engines.evidence.deduplication import deduplicate_evidence_items
from app.engines.evidence.models import (
    EvidenceInput,
    EvidenceItem,
    EvidencePackage,
    EvidenceSeverity,
    SourceCoverageStatus,
)
from app.engines.evidence.provenance import generate_case_id
from app.engines.evidence.ranking import rank_evidence_items
from app.engines.evidence.renderer import render_evidence_summary
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.engines.risk_fusion.models import FusionResult, RiskLevel
from app.engines.rules.base import EvaluationResult, RuleMatchResult
from app.engines.temporal.temporal_models import TemporalFeatures

logger = logging.getLogger("app.engines.evidence.engine")


class EvidenceEngine:
    """Core coordinator for generating deterministic forensic evidence packages."""

    def __init__(self, engine_version: str = "v1.0") -> None:
        self.engine_version = engine_version

    def generate_evidence(self, input_data: EvidenceInput) -> EvidencePackage:
        """Construct a complete, deterministic EvidencePackage from an EvidenceInput.

        Execution Pipeline:
        1. Resolve case_id and subject_id deterministically.
        2. Audit source coverage (AVAILABLE, UNAVAILABLE, MISSING).
        3. Collect raw evidence items across all analytical sources.
        4. Deduplicate items deterministically.
        5. Rank items using multi-factor priority policy.
        6. Preserve M10 composite risk score and risk level exactly.
        7. Render deterministic factual case summary.
        8. Return immutable EvidencePackage.
        """
        event = input_data.transaction_event
        tx_id = event.transaction_id if event else None

        # 1. Resolve IDs deterministically
        subject_id = input_data.subject_id
        if not subject_id:
            subject_id = event.sender_account if event and event.sender_account else (tx_id or "SUBJECT_UNKNOWN")

        case_id = input_data.case_id
        if not case_id:
            case_id = generate_case_id(transaction_id=tx_id, subject_id=subject_id)

        # 2. Source Coverage Audit
        source_coverage = self._compute_source_coverage(input_data)

        # 3. Collect Raw Evidence Items
        raw_items: list[EvidenceItem] = []

        # A. Rule Evidence (M5)
        raw_items.extend(collect_rule_evidence(input_data.rule_signals, event=event))

        # B. Temporal Evidence (M6)
        raw_items.extend(collect_temporal_evidence(input_data.temporal_features, event=event))

        # C. Graph Evidence (M7)
        raw_items.extend(collect_graph_evidence(input_data.graph_features, event=event))

        # D. ML Predictions (M8 & M9)
        raw_items.extend(
            collect_ml_evidence(
                input_data.tabular_prediction,
                input_data.graph_ml_prediction,
                event=event,
            )
        )

        # E. Risk Fusion (M10)
        raw_items.extend(collect_fusion_evidence(input_data.fusion_result, event=event))

        # F. Transaction Context (M1)
        raw_items.extend(collect_transaction_evidence(event))

        # 4. Deduplicate deterministically
        deduped_items = deduplicate_evidence_items(raw_items)

        # 5. Rank deterministically
        ranked_items = rank_evidence_items(deduped_items)

        # 6. Preserve M10 Composite Risk and Tier EXACTLY
        if input_data.fusion_result is not None:
            composite_risk_score = float(input_data.fusion_result.composite_risk_score)
            risk_level = input_data.fusion_result.risk_level
        else:
            composite_risk_score = 0.0
            risk_level = RiskLevel.LOW

        # 7. Calculate severity counts
        severity_counts = {
            "CRITICAL": sum(1 for e in ranked_items if e.severity == EvidenceSeverity.CRITICAL),
            "HIGH": sum(1 for e in ranked_items if e.severity == EvidenceSeverity.HIGH),
            "MEDIUM": sum(1 for e in ranked_items if e.severity == EvidenceSeverity.MEDIUM),
            "LOW": sum(1 for e in ranked_items if e.severity == EvidenceSeverity.LOW),
            "INFO": sum(1 for e in ranked_items if e.severity == EvidenceSeverity.INFO),
        }

        # 8. Render deterministic summary
        evidence_summary = render_evidence_summary(
            case_id=case_id,
            subject_id=subject_id,
            composite_risk_score=composite_risk_score,
            risk_level=risk_level,
            evidence_items=ranked_items,
            source_coverage=source_coverage,
        )

        return EvidencePackage(
            case_id=case_id,
            subject_id=subject_id,
            transaction_id=tx_id,
            composite_risk_score=composite_risk_score,
            risk_level=risk_level,
            evidence_items=tuple(ranked_items),
            evidence_summary=evidence_summary,
            source_coverage=source_coverage,
            total_evidence_count=len(ranked_items),
            severity_counts=severity_counts,
            metadata={
                "engine": "EvidenceEngine",
                "version": self.engine_version,
                "input_metadata": input_data.metadata,
            },
            engine_version=self.engine_version,
        )

    def create_evidence_package(
        self,
        transaction_event: Optional[TransactionEvent] = None,
        rule_signals: Optional[EvaluationResult | list[RuleMatchResult] | dict[str, Any]] = None,
        temporal_features: Optional[TemporalFeatures] = None,
        graph_features: Optional[GraphFeatures] = None,
        tabular_prediction: Optional[ModelPrediction] = None,
        graph_ml_prediction: Optional[ModelPrediction] = None,
        fusion_result: Optional[FusionResult] = None,
        case_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EvidencePackage:
        """Convenience factory method accepting arguments directly."""
        evidence_input = EvidenceInput(
            transaction_event=transaction_event,
            rule_signals=rule_signals,
            temporal_features=temporal_features,
            graph_features=graph_features,
            tabular_prediction=tabular_prediction,
            graph_ml_prediction=graph_ml_prediction,
            fusion_result=fusion_result,
            case_id=case_id,
            subject_id=subject_id,
            metadata=metadata or {},
        )
        return self.generate_evidence(evidence_input)

    def _compute_source_coverage(
        self, input_data: EvidenceInput
    ) -> dict[str, SourceCoverageStatus]:
        """Compute availability status for each analytical source."""
        coverage: dict[str, SourceCoverageStatus] = {}

        # 1. Rules
        coverage["RULE"] = (
            SourceCoverageStatus.AVAILABLE
            if input_data.rule_signals is not None
            else SourceCoverageStatus.MISSING
        )

        # 2. Temporal
        coverage["TEMPORAL"] = (
            SourceCoverageStatus.AVAILABLE
            if input_data.temporal_features is not None
            else SourceCoverageStatus.MISSING
        )

        # 3. Graph
        coverage["GRAPH"] = (
            SourceCoverageStatus.AVAILABLE
            if input_data.graph_features is not None
            else SourceCoverageStatus.MISSING
        )

        # 4. Tabular ML
        if input_data.tabular_prediction is None:
            coverage["TABULAR_ML"] = SourceCoverageStatus.MISSING
        else:
            det = input_data.tabular_prediction.details or {}
            is_unavail = (
                det.get("status") == "model_unavailable"
                or "_fallback" in str(input_data.tabular_prediction.model_version)
                or det.get("model_artifact_loaded") is False
            )
            coverage["TABULAR_ML"] = (
                SourceCoverageStatus.UNAVAILABLE if is_unavail else SourceCoverageStatus.AVAILABLE
            )

        # 5. Graph ML
        if input_data.graph_ml_prediction is None:
            coverage["GRAPH_ML"] = SourceCoverageStatus.MISSING
        else:
            det = input_data.graph_ml_prediction.details or {}
            is_unavail = (
                det.get("status") == "model_unavailable"
                or "_fallback" in str(input_data.graph_ml_prediction.model_version)
                or det.get("model_artifact_loaded") is False
            )
            coverage["GRAPH_ML"] = (
                SourceCoverageStatus.UNAVAILABLE if is_unavail else SourceCoverageStatus.AVAILABLE
            )

        # 6. Risk Fusion
        coverage["RISK_FUSION"] = (
            SourceCoverageStatus.AVAILABLE
            if input_data.fusion_result is not None
            else SourceCoverageStatus.MISSING
        )

        # 7. Transaction
        coverage["TRANSACTION"] = (
            SourceCoverageStatus.AVAILABLE
            if input_data.transaction_event is not None
            else SourceCoverageStatus.MISSING
        )

        return coverage


# Global singleton instance
evidence_engine = EvidenceEngine()
