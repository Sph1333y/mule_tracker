"""
MuleTrace AI — Evidence Ranking.

Provides deterministic multi-factor ranking routines to order evidence items
based on severity, source authority, signal strength, and stable tie-breakers.

Architectural Boundary:
- Purely deterministic: never relies on LLMs, timestamps, or random order.
- Documented, explicit scoring hierarchy.
"""

from __future__ import annotations

from typing import Sequence

from app.engines.evidence.models import (
    EvidenceItem,
    EvidenceSeverity,
    EvidenceSource,
)

# Severity priority weighting (Higher value = higher priority)
_SEVERITY_WEIGHTS: dict[EvidenceSeverity, int] = {
    EvidenceSeverity.CRITICAL: 500,
    EvidenceSeverity.HIGH: 400,
    EvidenceSeverity.MEDIUM: 300,
    EvidenceSeverity.LOW: 200,
    EvidenceSeverity.INFO: 100,
}

# Analytical source authority priority
_SOURCE_PRIORITY: dict[EvidenceSource, int] = {
    EvidenceSource.RULE: 70,
    EvidenceSource.GRAPH: 60,
    EvidenceSource.TEMPORAL: 50,
    EvidenceSource.GRAPH_ML: 40,
    EvidenceSource.TABULAR_ML: 40,
    EvidenceSource.RISK_FUSION: 30,
    EvidenceSource.TRANSACTION: 20,
}


def _extract_signal_strength(item: EvidenceItem) -> float:
    """Extract a numeric signal magnitude from metrics for ranking tie-breaking."""
    metrics = item.metrics
    # 1. Rule score contribution
    if "score_contribution" in metrics:
        return float(metrics["score_contribution"])
    # 2. ML fraud probability (scaled to 100)
    if "fraud_probability" in metrics:
        return float(metrics["fraud_probability"]) * 100.0
    # 3. Fusion contribution points
    if "contribution_points" in metrics:
        return float(metrics["contribution_points"])
    # 4. Cycle count
    if "cycle_count" in metrics:
        return float(metrics["cycle_count"]) * 20.0
    # 5. Shared device count
    if "shared_device_count" in metrics:
        return float(metrics["shared_device_count"]) * 15.0
    # 6. Burst count
    if "burst_count" in metrics:
        return float(metrics["burst_count"]) * 10.0
    # Default fallback
    return 0.0


def rank_evidence_items(
    items: Sequence[EvidenceItem],
) -> list[EvidenceItem]:
    """Rank a sequence of EvidenceItems using an explicit, deterministic multi-factor policy.

    Ranking Criteria (in order of precedence):
    1. Severity Tier: CRITICAL > HIGH > MEDIUM > LOW > INFO.
    2. Source Authority: RULE > GRAPH > TEMPORAL > ML > FUSION > TRANSACTION.
    3. Signal Magnitude: Extracted continuous signal metric strength.
    4. Deterministic Tie-Breaker: Lexicographical order of evidence_id.

    Returns:
        List of EvidenceItem with rank field populated (1 = highest priority).
    """
    def sort_key(item: EvidenceItem) -> tuple[int, int, float, str]:
        sev_wt = _SEVERITY_WEIGHTS.get(item.severity, 0)
        src_wt = _SOURCE_PRIORITY.get(item.source, 0)
        strength = _extract_signal_strength(item)
        # Note: we negate numeric weights for descending sort, while evidence_id is ascending
        return (-sev_wt, -src_wt, -strength, item.evidence_id)

    sorted_items = sorted(items, key=sort_key)

    ranked_items: list[EvidenceItem] = []
    for rank_idx, item in enumerate(sorted_items, start=1):
        ranked_items.append(
            EvidenceItem(
                evidence_id=item.evidence_id,
                category=item.category,
                title=item.title,
                description=item.description,
                severity=item.severity,
                source=item.source,
                source_reference=item.source_reference,
                transaction_ids=item.transaction_ids,
                account_ids=item.account_ids,
                device_ids=item.device_ids,
                ip_addresses=item.ip_addresses,
                timestamps=item.timestamps,
                metrics=item.metrics,
                rank=rank_idx,
            )
        )

    return ranked_items
