"""
MuleTrace AI — Deterministic Evidence Summary Renderer.

Synthesizes structured forensic evidence items into factual, non-speculative
executive case narratives without using LLMs.

Architectural Boundary:
- Zero LLM dependency: purely template and rule-based deterministic string rendering.
- Grounded strictly in verified evidence items and upstream metrics.
- Uses factual, non-defamatory compliance language.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from app.engines.evidence.models import (
    EvidenceItem,
    EvidenceSeverity,
    SourceCoverageStatus,
)
from app.engines.risk_fusion.models import RiskLevel


def render_evidence_summary(
    case_id: str,
    subject_id: str,
    composite_risk_score: float,
    risk_level: RiskLevel | str,
    evidence_items: Sequence[EvidenceItem],
    source_coverage: Mapping[str, SourceCoverageStatus],
) -> str:
    """Generate a deterministic, factual summary narrative from structured evidence.

    Example Output:
        "Case CASE-TX101 for subject ACC-992 evaluated with composite risk score 82.50/100 (HIGH).
         Total evidence items: 4 (1 CRITICAL, 2 HIGH, 1 MEDIUM).
         Key Forensic Findings:
         1. [CRITICAL] Circular Fund Routing Loop: Identified 1 circular fund loop(s)...
         2. [HIGH] Rapid In/Out Fund Pass-Through: Funds rapidly routed through account within 45.0s...
         3. [HIGH] Forensic Rule R004 Triggered: Mule Chain / Rapid Pass-Through...
         Coverage: RULE (AVAILABLE), TEMPORAL (AVAILABLE), GRAPH (AVAILABLE), TABULAR_ML (AVAILABLE), GRAPH_ML (UNAVAILABLE)."
    """
    tier_str = risk_level.value if isinstance(risk_level, RiskLevel) else str(risk_level)
    total_count = len(evidence_items)

    # Count by severity
    counts: dict[str, int] = {
        "CRITICAL": sum(1 for e in evidence_items if e.severity == EvidenceSeverity.CRITICAL),
        "HIGH": sum(1 for e in evidence_items if e.severity == EvidenceSeverity.HIGH),
        "MEDIUM": sum(1 for e in evidence_items if e.severity == EvidenceSeverity.MEDIUM),
        "LOW": sum(1 for e in evidence_items if e.severity == EvidenceSeverity.LOW),
        "INFO": sum(1 for e in evidence_items if e.severity == EvidenceSeverity.INFO),
    }

    header = (
        f"Case {case_id} for subject {subject_id} evaluated with composite risk score "
        f"{composite_risk_score:.2f}/100 ({tier_str})."
    )

    if total_count == 0:
        breakdown = "No suspicious forensic evidence items were detected across active analytical sources."
        findings = ""
    else:
        sev_parts = []
        if counts["CRITICAL"] > 0:
            sev_parts.append(f"{counts['CRITICAL']} CRITICAL")
        if counts["HIGH"] > 0:
            sev_parts.append(f"{counts['HIGH']} HIGH")
        if counts["MEDIUM"] > 0:
            sev_parts.append(f"{counts['MEDIUM']} MEDIUM")
        if counts["LOW"] > 0:
            sev_parts.append(f"{counts['LOW']} LOW")
        if counts["INFO"] > 0:
            sev_parts.append(f"{counts['INFO']} INFO")

        breakdown = f"Total evidence items: {total_count} ({', '.join(sev_parts)})."

        top_items = evidence_items[:4]
        findings_lines = ["Key Forensic Findings:"]
        for item in top_items:
            findings_lines.append(f"- [{item.severity.value}] {item.title}: {item.description}")
        findings = "\n".join(findings_lines)

    # Sorted deterministic coverage string
    coverage_parts = [
        f"{k} ({v.value if isinstance(v, SourceCoverageStatus) else str(v)})"
        for k, v in sorted(source_coverage.items())
    ]
    cov_str = f"Analytical Coverage: {', '.join(coverage_parts)}."

    sections = [header, breakdown]
    if findings:
        sections.append(findings)
    sections.append(cov_str)

    return "\n\n".join(sections)
