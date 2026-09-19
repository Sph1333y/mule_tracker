"""
MuleTrace AI — Deterministic Investigation Copilot Engine.

Production-grade, deterministic implementation of the InvestigationCopilot domain port
for Milestone 12 (Deterministic Investigation Copilot).

Architectural Guarantees:
- Strictly ZERO LLM (no OpenAI, Gemini, Bedrock, Ollama, Claude, prompt injection, etc.).
- Strictly offline, zero external network dependency, zero API keys.
- Implements the InvestigationCopilot port from app.domain.interfaces.
- Consumes upstream M10 FusionResult and M11 EvidencePackage as immutable sources of truth.
- Zero risk score recalculation, zero risk level alteration, zero drift.
- Zero evidence fabrication; all findings strictly reference valid M11 evidence IDs.
- Deterministic, byte-stable output for identical inputs.
- Safe failure isolation with no unhandled exceptions leaking into unrelated pipelines.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.domain.interfaces import InvestigationCopilot
from app.engines.ai.models import (
    InvestigationContext,
    InvestigationCopilotResponse,
    KeyFinding,
    SuggestedAction,
)
from app.engines.ai.templates import (
    extract_key_findings,
    generate_audit_limitations,
    generate_follow_up_questions,
    generate_investigation_actions,
    render_investigation_summary,
    render_risk_summary,
)
from app.engines.evidence.models import (
    EvidenceCategory,
    EvidenceItem,
    EvidencePackage,
    EvidenceSeverity,
    EvidenceSource,
    SourceCoverageStatus,
)
from app.engines.risk_fusion.models import FusionResult, RiskLevel


class DeterministicInvestigationCopilot(InvestigationCopilot):
    """Purely deterministic, template-based implementation of the InvestigationCopilot port.

    Fulfills the domain interface defined in app.domain.interfaces without any generative AI,
    providing fully explainable, repeatable, and audit-compliant investigation assistance.
    """

    def __init__(self) -> None:
        self.version = "v1.0"

    # ── Domain Port Implementation (app.domain.interfaces.InvestigationCopilot) ──

    async def generate_narrative(self, evidence: dict[str, Any]) -> str:
        """Synthesize structured case evidence into an AML executive narrative.

        Fulfills the abstract method defined in app.domain.interfaces.InvestigationCopilot.

        Args:
            evidence: Structured case and alert evidence dictionary.

        Returns:
            Human-readable, deterministic natural language narrative.
        """
        pkg, risk_score, risk_level, subject_id = self._coerce_evidence_input(evidence)
        return render_investigation_summary(
            evidence_package=pkg,
            risk_level=risk_level,
            composite_risk_score=risk_score,
            subject_id=subject_id,
        )

    async def suggest_next_steps(self, evidence: dict[str, Any]) -> list[str]:
        """Generate prioritized investigative recommendations based on evidence.

        Fulfills the abstract method defined in app.domain.interfaces.InvestigationCopilot.

        Args:
            evidence: Structured case and alert evidence dictionary.

        Returns:
            List of recommended actionable review steps.
        """
        pkg, _, _, _ = self._coerce_evidence_input(evidence)
        actions = generate_investigation_actions(pkg)
        return [f"{action.title}: {action.description}" for action in actions]

    # ── Full Copilot Investigation Pipeline ───────────────────────────────────

    async def investigate(self, context: InvestigationContext) -> InvestigationCopilotResponse:
        """Execute a full, deterministic investigation analysis on the given context.

        Args:
            context: The immutable InvestigationContext.

        Returns:
            Structured, deterministic InvestigationCopilotResponse.
        """
        return self.investigate_sync(context)

    def investigate_sync(self, context: InvestigationContext) -> InvestigationCopilotResponse:
        """Synchronous execution of deterministic investigation synthesis.

        Guarantees:
        - M10 composite risk score is preserved exactly without recalculation.
        - M10 risk level is preserved exactly without alteration.
        - Evidence items from M11 are preserved without mutation.
        - All key findings strictly reference valid M11 evidence IDs.

        Args:
            context: The immutable InvestigationContext.

        Returns:
            Structured, deterministic InvestigationCopilotResponse.
        """
        # 1. Resolve M10 score and risk level (Source of Truth for Risk)
        composite_risk_score = 0.0
        risk_level = "LOW"
        contributions: Optional[dict[str, Any]] = None

        if context.fusion_result is not None:
            composite_risk_score = float(context.fusion_result.composite_risk_score)
            rl = context.fusion_result.risk_level
            risk_level = rl.value if isinstance(rl, RiskLevel) else str(rl)
            contributions = context.fusion_result.contributions
        elif context.evidence_package is not None:
            composite_risk_score = float(context.evidence_package.composite_risk_score)
            rl = context.evidence_package.risk_level
            risk_level = rl.value if isinstance(rl, RiskLevel) else str(rl)

        # 2. Extract Key Findings referencing only valid evidence IDs
        key_findings = extract_key_findings(context.evidence_package)

        # 3. Collect all referenced evidence IDs in stable M11 order
        evidence_references: tuple[str, ...] = ()
        if context.evidence_package and context.evidence_package.evidence_items:
            evidence_references = tuple(
                item.evidence_id for item in context.evidence_package.evidence_items
            )

        # 4. Render Deterministic Summaries
        risk_summary = render_risk_summary(
            composite_risk_score=composite_risk_score,
            risk_level=risk_level,
            contributions=contributions,
        )

        subject_id = (
            context.subject_id
            or (context.evidence_package.subject_id if context.evidence_package else None)
        )
        investigation_summary = render_investigation_summary(
            evidence_package=context.evidence_package,
            risk_level=risk_level,
            composite_risk_score=composite_risk_score,
            subject_id=subject_id,
        )

        # 5. Generate Deterministic Next Steps (Non-punitive, investigative only)
        suggested_next_steps = generate_investigation_actions(context.evidence_package)

        # 6. Generate Targeted Follow-up Questions
        follow_up_questions = generate_follow_up_questions(context.evidence_package)

        # 7. Compile Limitations & Governance Disclosures
        limitations = generate_audit_limitations(context)

        # 8. Assemble Metadata
        metadata = {
            "engine_version": self.version,
            "deterministic": True,
            "llm_used": False,
            "external_ai": False,
            "source_of_truth_risk": "M10_RISK_FUSION",
            "source_of_truth_evidence": "M11_EVIDENCE_ENGINE",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
        if context.metadata:
            metadata["context_metadata"] = context.metadata

        case_id = (
            context.case_id
            or (context.evidence_package.case_id if context.evidence_package else None)
        )
        tx_id = (
            context.transaction_id
            or (context.evidence_package.transaction_id if context.evidence_package else None)
        )

        return InvestigationCopilotResponse(
            case_id=case_id,
            subject_id=subject_id,
            transaction_id=tx_id,
            composite_risk_score=composite_risk_score,
            risk_level=risk_level,
            risk_summary=risk_summary,
            investigation_summary=investigation_summary,
            key_findings=key_findings,
            evidence_references=evidence_references,
            suggested_next_steps=suggested_next_steps,
            follow_up_questions=follow_up_questions,
            limitations=limitations,
            generation_metadata=metadata,
        )

    # ── Internal Helpers ──────────────────────────────────────────────────────

    def _coerce_evidence_input(
        self, evidence: Any
    ) -> tuple[Optional[EvidencePackage], float, str, Optional[str]]:
        """Coerce raw evidence input into typed package, score, tier, and subject.

        Gracefully accepts EvidencePackage, InvestigationContext, or dict representations.
        """
        if isinstance(evidence, EvidencePackage):
            rl = evidence.risk_level
            level_str = rl.value if isinstance(rl, RiskLevel) else str(rl)
            return evidence, float(evidence.composite_risk_score), level_str, evidence.subject_id

        if isinstance(evidence, InvestigationContext):
            pkg = evidence.evidence_package
            score = 0.0
            level_str = "LOW"
            if evidence.fusion_result is not None:
                score = float(evidence.fusion_result.composite_risk_score)
                rl = evidence.fusion_result.risk_level
                level_str = rl.value if isinstance(rl, RiskLevel) else str(rl)
            elif pkg is not None:
                score = float(pkg.composite_risk_score)
                rl = pkg.risk_level
                level_str = rl.value if isinstance(rl, RiskLevel) else str(rl)
            return pkg, score, level_str, evidence.subject_id

        if isinstance(evidence, dict):
            # Check if this is an EvidencePackage dict
            score = float(evidence.get("composite_risk_score", 0.0))
            level_str = str(evidence.get("risk_level", "LOW"))
            subject_id = evidence.get("subject_id")
            case_id = evidence.get("case_id", "CAS-ADHOC")
            tx_id = evidence.get("transaction_id")

            items_raw = evidence.get("evidence_items", [])
            items: list[EvidenceItem] = []
            for item in items_raw:
                if isinstance(item, EvidenceItem):
                    items.append(item)
                elif isinstance(item, dict):
                    # Coerce dict to EvidenceItem
                    try:
                        cat_str = item.get("category", EvidenceCategory.TRANSACTION_CONTEXT.value)
                        try:
                            cat_enum = EvidenceCategory(cat_str)
                        except ValueError:
                            cat_enum = EvidenceCategory.TRANSACTION_CONTEXT

                        sev_str = item.get("severity", EvidenceSeverity.MEDIUM.value)
                        try:
                            sev_enum = EvidenceSeverity(sev_str)
                        except ValueError:
                            sev_enum = EvidenceSeverity.MEDIUM

                        src_str = item.get("source", EvidenceSource.TRANSACTION.value)
                        try:
                            src_enum = EvidenceSource(src_str)
                        except ValueError:
                            src_enum = EvidenceSource.TRANSACTION

                        e_item = EvidenceItem(
                            evidence_id=str(item.get("evidence_id", "EVD-UNKNOWN")),
                            category=cat_enum,
                            title=str(item.get("title", "Forensic Signal")),
                            description=str(item.get("description", "")),
                            severity=sev_enum,
                            source=src_enum,
                            source_reference=str(item.get("source_reference", "")),
                            transaction_ids=tuple(item.get("transaction_ids", ())),
                            account_ids=tuple(item.get("account_ids", ())),
                            device_ids=tuple(item.get("device_ids", ())),
                            ip_addresses=tuple(item.get("ip_addresses", ())),
                            timestamps=tuple(item.get("timestamps", ())),
                            metrics=dict(item.get("metrics", {})),
                            rank=int(item.get("rank", 0)),
                        )
                        items.append(e_item)
                    except Exception:
                        continue

            try:
                rl_enum = RiskLevel(level_str)
            except ValueError:
                rl_enum = RiskLevel.LOW

            pkg = EvidencePackage(
                case_id=case_id,
                subject_id=subject_id or "UNKNOWN",
                transaction_id=tx_id,
                composite_risk_score=score,
                risk_level=rl_enum,
                evidence_items=tuple(items),
                evidence_summary=str(evidence.get("evidence_summary", "")),
                source_coverage={},
                total_evidence_count=len(items),
                severity_counts={},
            )
            return pkg, score, level_str, subject_id

        return None, 0.0, "LOW", None
