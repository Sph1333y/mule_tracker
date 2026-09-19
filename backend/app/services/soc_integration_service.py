"""
MuleTrace AI — SOC Integration Service.

Coordinates the end-to-end intelligence pipeline for the Security Operations Center (SOC):
Transaction -> M1 Canonical -> M5 Rules -> M6 Temporal -> M7 Graph -> M8 Tabular ML
-> M9 Graph ML -> M10 Risk Fusion -> M11 Evidence Engine -> M12 Investigation Copilot -> M13 SOC.

Strict Invariant Guarantees:
- Consumes M10 FusionResult directly (zero recalculation of risk score or level).
- Consumes M11 EvidencePackage directly (zero evidence fabrication or ID manipulation).
- Consumes M12 DeterministicInvestigationCopilot directly (zero external LLM / AI dependencies).
- Failure-isolated: any subsystem error degrades gracefully without breaking case workflows.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.domain.models import TransactionEvent
from app.domain.transaction_mapper import TransactionMapper
from app.engines.ai import DeterministicInvestigationCopilot, InvestigationContext
from app.engines.evidence import EvidenceInput, evidence_engine
from app.engines.graph.intelligence import graph_intelligence_engine
from app.engines.ml.graph import graphsage_model_service
from app.engines.ml.tabular import xgboost_model_service
from app.engines.risk_fusion import FusionInput, risk_fusion_engine
from app.engines.rules import modular_rule_engine
from app.engines.temporal import temporal_engine
from app.schemas.investigation import CaseDetailRead, InvestigationIntelligenceData

logger = logging.getLogger("app.services.soc_integration_service")

# Canonical Case Definitions known to SOC
CANONICAL_CASES: dict[str, dict[str, Any]] = {
    "CAS-2025-0045": {
        "case_number": "CAS-2025-0045",
        "title": "Mule Ring Operation — Western Region",
        "priority": "CRITICAL",
        "case_status": "IN_PROGRESS",
        "assigned_investigator_id": "INV-882",
        "alerts_count": 8,
        "focal_subject_id": "XXXX1002",
        "total_volume": "₹48.7L",
        "linked_accounts": ["XXXX1001", "XXXX1002", "XXXX1003", "XXXX1004", "XXXX1005"],
    },
    "CAS-2025-0046": {
        "case_number": "CAS-2025-0046",
        "title": "Fan-In Collector Network — Andheri Hub",
        "priority": "HIGH",
        "case_status": "IN_PROGRESS",
        "assigned_investigator_id": "INV-445",
        "alerts_count": 5,
        "focal_subject_id": "XXXX1002",
        "total_volume": "₹25.8L",
        "linked_accounts": ["XXXX1002", "XXXX1009", "XXXX1010", "XXXX1011"],
    },
    "CAS-2025-0047": {
        "case_number": "CAS-2025-0047",
        "title": "Cross-Channel Layering — South Zone",
        "priority": "HIGH",
        "case_status": "OPEN",
        "assigned_investigator_id": "INV-331",
        "alerts_count": 3,
        "focal_subject_id": "XXXX1012",
        "total_volume": "₹18.4L",
        "linked_accounts": ["XXXX1012", "XXXX1013", "XXXX1014"],
    },
    "CAS-2025-0048": {
        "case_number": "CAS-2025-0048",
        "title": "Shared Device Fraud Cluster — Delhi NCR",
        "priority": "MEDIUM",
        "case_status": "IN_PROGRESS",
        "assigned_investigator_id": "INV-882",
        "alerts_count": 4,
        "focal_subject_id": "XXXX1015",
        "total_volume": "₹12.1L",
        "linked_accounts": ["XXXX1015", "XXXX1016"],
    },
    "CAS-2025-0049": {
        "case_number": "CAS-2025-0049",
        "title": "Dormant Account Activation Series",
        "priority": "LOW",
        "case_status": "CLOSED",
        "assigned_investigator_id": "INV-112",
        "alerts_count": 2,
        "focal_subject_id": "XXXX1017",
        "total_volume": "₹3.5L",
        "linked_accounts": ["XXXX1017"],
    },
}


class SOCIntegrationService:
    """Orchestrates multi-modal intelligence retrieval and synthesis for SOC investigators."""

    def __init__(self) -> None:
        self.copilot = DeterministicInvestigationCopilot()

    def get_case_detail(self, case_number: str) -> Optional[CaseDetailRead]:
        """Fetch investigation case details by case number."""
        case_dict = CANONICAL_CASES.get(case_number)
        if not case_dict:
            return None
        return CaseDetailRead(**case_dict)

    def list_canonical_cases(self) -> list[dict[str, Any]]:
        """List all canonical cases formatted for investigations list endpoint."""
        return [
            {
                "case_number": c["case_number"],
                "title": c["title"],
                "priority": c["priority"],
                "case_status": c["case_status"],
                "assigned_investigator_id": c["assigned_investigator_id"],
                "alerts_count": c["alerts_count"],
            }
            for c in CANONICAL_CASES.values()
        ]

    def _build_canonical_case_transactions(
        self, case_number: str
    ) -> tuple[TransactionEvent, list[TransactionEvent]]:
        """Construct deterministic canonical transactions representing case evidence."""
        base_time = datetime(2025, 7, 24, 13, 10, 0, tzinfo=timezone.utc)

        if case_number == "CAS-2025-0045":
            # Multi-hop rapid pass-through mule chain
            tx1 = TransactionEvent(
                transaction_id="TX-2025-0045-A",
                sender_account="XXXX1001",
                receiver_account="XXXX1002",
                amount=450000.0,
                currency="INR",
                channel="UPI",
                timestamp=base_time,
                device_id="DEV-9988",
                ip_address="192.168.1.100",
                location_city="Mumbai",
                narration="Transfer from contact",
            )
            tx2 = TransactionEvent(
                transaction_id="TX-2025-0045-B",
                sender_account="XXXX1002",
                receiver_account="XXXX1003",
                amount=445000.0,
                currency="INR",
                channel="IMPS",
                timestamp=datetime(2025, 7, 24, 13, 11, 30, tzinfo=timezone.utc),
                device_id="DEV-9988",
                ip_address="192.168.1.100",
                location_city="Mumbai",
                narration="Urgent settlement",
            )
            tx3 = TransactionEvent(
                transaction_id="TX-2025-0045-C",
                sender_account="XXXX1004",
                receiver_account="XXXX1002",
                amount=480000.0,
                currency="INR",
                channel="UPI",
                timestamp=datetime(2025, 7, 24, 14, 0, 0, tzinfo=timezone.utc),
                device_id="DEV-9988",
                ip_address="192.168.1.100",
                location_city="Mumbai",
                narration="Funds pool",
            )
            tx4 = TransactionEvent(
                transaction_id="TX-2025-0045-D",
                sender_account="XXXX1002",
                receiver_account="XXXX1005",
                amount=475000.0,
                currency="INR",
                channel="IMPS",
                timestamp=datetime(2025, 7, 24, 14, 1, 15, tzinfo=timezone.utc),
                device_id="DEV-9988",
                ip_address="192.168.1.100",
                location_city="Mumbai",
                narration="Final distribution",
            )
            return tx2, [tx1, tx2, tx3, tx4]

        elif case_number == "CAS-2025-0046":
            # Fan-in collector pattern
            tx1 = TransactionEvent(
                transaction_id="TX-2025-0046-A",
                sender_account="XXXX1009",
                receiver_account="XXXX1002",
                amount=180000.0,
                currency="INR",
                channel="UPI",
                timestamp=base_time,
                device_id="DEV-5544",
                ip_address="192.168.2.50",
                location_city="Andheri",
            )
            tx2 = TransactionEvent(
                transaction_id="TX-2025-0046-B",
                sender_account="XXXX1010",
                receiver_account="XXXX1002",
                amount=195000.0,
                currency="INR",
                channel="UPI",
                timestamp=datetime(2025, 7, 24, 13, 20, 0, tzinfo=timezone.utc),
                device_id="DEV-5544",
                ip_address="192.168.2.50",
                location_city="Andheri",
            )
            return tx2, [tx1, tx2]

        # Generic baseline transaction for any other case
        focal_subj = CANONICAL_CASES.get(case_number, {}).get("focal_subject_id", "ACCT-DEFAULT")
        tx = TransactionEvent(
            transaction_id=f"TX-{case_number}-01",
            sender_account=focal_subj,
            receiver_account="BENEFICIARY-001",
            amount=50000.0,
            currency="INR",
            channel="UPI",
            timestamp=base_time,
            location_city="Mumbai",
        )
        return tx, [tx]

    async def get_case_intelligence(
        self,
        case_number: str,
        subject_id: Optional[str] = None,
        transaction_event: Optional[TransactionEvent] = None,
        history: Optional[list[TransactionEvent]] = None,
    ) -> InvestigationIntelligenceData:
        """Execute the complete M1-M12 intelligence pipeline for an investigation case.

        Failure Isolation Guarantee:
        If any step throws an unexpected error, a clean degraded response is returned
        without breaking the existing application or returning a 500 error.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            # 1. Resolve Case Context
            case_info = CANONICAL_CASES.get(case_number)
            focal_subject = subject_id or (case_info.get("focal_subject_id") if case_info else "SUBJECT_UNKNOWN")

            if transaction_event is not None:
                primary_event = transaction_event
                history_events = history if history is not None else [primary_event]
            else:
                primary_event, history_events = self._build_canonical_case_transactions(case_number)

            # 2. M5 Modular Rules Evaluation
            rule_signals = modular_rule_engine.evaluate(
                transaction=TransactionMapper.to_legacy_dict(primary_event),
                sender_account={"account_number": primary_event.sender_account},
                recent_transactions=[TransactionMapper.to_legacy_dict(e) for e in history_events],
                linked_devices_count=3 if primary_event.device_id else 1,
                linked_ips_count=2 if primary_event.ip_address else 1,
            )

            # 3. M6 Temporal Intelligence
            temporal_features = temporal_engine.evaluate(
                events=history_events,
                focal_account=focal_subject,
            )

            # 4. M7 Graph Intelligence
            try:
                graph_features = await graph_intelligence_engine.extract_features(focal_subject)
            except Exception as exc:
                logger.warning("M7 graph intelligence extraction error: %s", exc)
                graph_features = None

            # 5. M8 Tabular ML Inference
            try:
                tabular_prediction = xgboost_model_service.predict_risk(
                    event=primary_event,
                    temporal_features=temporal_features,
                    graph_features=graph_features,
                )
            except Exception as exc:
                logger.warning("M8 tabular ML inference error: %s", exc)
                tabular_prediction = None

            # 6. M9 Graph ML Inference
            try:
                graph_ml_prediction = graphsage_model_service.predict_risk(
                    event=primary_event,
                    temporal_features=temporal_features,
                    graph_features=graph_features,
                )
            except Exception as exc:
                logger.warning("M9 graph ML inference error: %s", exc)
                graph_ml_prediction = None

            # 7. M10 Risk Fusion (Source of Truth for Risk)
            fusion_input = FusionInput(
                event=primary_event,
                rule_signals=rule_signals,
                temporal_features=temporal_features,
                graph_features=graph_features,
                tabular_prediction=tabular_prediction,
                graph_ml_prediction=graph_ml_prediction,
            )
            fusion_result = risk_fusion_engine.fuse(fusion_input)

            # 8. M11 Evidence Engine (Source of Truth for Evidence)
            evidence_input = EvidenceInput(
                case_id=case_number,
                subject_id=focal_subject,
                transaction_event=primary_event,
                rule_signals=rule_signals,
                temporal_features=temporal_features,
                graph_features=graph_features,
                tabular_prediction=tabular_prediction,
                graph_ml_prediction=graph_ml_prediction,
                fusion_result=fusion_result,
            )
            evidence_package = evidence_engine.generate_evidence(evidence_input)

            # 9. M12 Deterministic Investigation Copilot Synthesis
            copilot_ctx = InvestigationContext(
                case_id=case_number,
                subject_id=focal_subject,
                transaction_id=primary_event.transaction_id,
                evidence_package=evidence_package,
                fusion_result=fusion_result,
            )
            copilot_response = await self.copilot.investigate(copilot_ctx)
            copilot_dict = copilot_response.to_dict()

            # 10. Assemble M13 Intelligence Payload
            # Risk Contributions (M10)
            contributions = [
                {
                    "modality": c.modality.value,
                    "normalized_value": round(c.normalized_value, 4),
                    "configured_weight": round(c.configured_weight, 4),
                    "effective_weight": round(c.effective_weight, 4),
                    "weighted_score": round(c.weighted_score, 4),
                    "is_available": c.is_available,
                    "explanation": c.explanation,
                }
                for c in fusion_result.contributions.values()
            ]

            # Evidence Items (M11)
            evidence_items_data = [item.to_dict() for item in evidence_package.evidence_items]

            return InvestigationIntelligenceData(
                case_id=case_number,
                subject_id=focal_subject,
                transaction_id=primary_event.transaction_id,
                composite_risk_score=round(float(fusion_result.composite_risk_score), 2),
                risk_level=fusion_result.risk_level.value,
                risk_contributions=contributions,
                total_evidence_count=evidence_package.total_evidence_count,
                severity_counts=evidence_package.severity_counts,
                evidence_items=evidence_items_data,
                evidence_summary=evidence_package.evidence_summary,
                risk_summary=copilot_response.risk_summary,
                investigation_summary=copilot_response.investigation_summary,
                key_findings=copilot_dict["key_findings"],
                suggested_next_steps=copilot_dict["suggested_next_steps"],
                evidence_references=copilot_dict["evidence_references"],
                follow_up_questions=copilot_dict["follow_up_questions"],
                limitations=copilot_dict["limitations"],
                generated_at=now_iso,
                is_degraded=False,
            )

        except Exception as exc:
            logger.exception("SOC intelligence pipeline failed for case '%s': %s", case_number, exc)
            return InvestigationIntelligenceData(
                case_id=case_number,
                subject_id=subject_id or "UNKNOWN",
                transaction_id=None,
                composite_risk_score=0.0,
                risk_level="UNKNOWN",
                risk_contributions=[],
                total_evidence_count=0,
                severity_counts={"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
                evidence_items=[],
                evidence_summary=f"Intelligence enrichment unavailable: {str(exc)}",
                risk_summary="Risk assessment degraded due to isolated processing limitation.",
                investigation_summary="Investigation copilot synthesis unavailable.",
                key_findings=[],
                suggested_next_steps=[],
                evidence_references=[],
                follow_up_questions=[],
                limitations=[f"Pipeline exception: {str(exc)}"],
                generated_at=now_iso,
                is_degraded=True,
            )


# Default singleton instance
soc_integration_service = SOCIntegrationService()
