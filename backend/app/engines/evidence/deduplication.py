"""
MuleTrace AI — Evidence Deduplication.

Provides deterministic deduplication routines to eliminate redundant evidence
while preserving entity references, metrics, and highest observed severity.

Architectural Boundary:
- Purely deterministic: never relies on process-randomized hashes or unordered sets.
- Stable across repeated executions.
"""

from __future__ import annotations

from typing import Sequence

from app.engines.evidence.models import EvidenceItem, EvidenceSeverity


_SEVERITY_ORDER: dict[EvidenceSeverity, int] = {
    EvidenceSeverity.INFO: 0,
    EvidenceSeverity.LOW: 1,
    EvidenceSeverity.MEDIUM: 2,
    EvidenceSeverity.HIGH: 3,
    EvidenceSeverity.CRITICAL: 4,
}


def _higher_severity(sev_a: EvidenceSeverity, sev_b: EvidenceSeverity) -> EvidenceSeverity:
    """Return the more severe of two EvidenceSeverity enum values."""
    order_a = _SEVERITY_ORDER.get(sev_a, 0)
    order_b = _SEVERITY_ORDER.get(sev_b, 0)
    return sev_a if order_a >= order_b else sev_b


def deduplicate_evidence_items(
    items: Sequence[EvidenceItem],
) -> list[EvidenceItem]:
    """Deduplicate a sequence of EvidenceItems deterministically.

    Identifies duplicates sharing the same:
        (source, source_reference, category, sorted_accounts)

    When duplicates are encountered:
    1. Highest severity is selected.
    2. Distinct entity references (txns, accounts, devices, IPs, timestamps) are unioned and sorted.
    3. Metrics dictionaries are merged.
    4. Stable ordering of the first occurrence is preserved.
    """
    seen: dict[str, EvidenceItem] = {}
    insertion_keys: list[str] = []

    for item in items:
        # Build stable deduplication key
        sorted_accts = ",".join(sorted(item.account_ids))
        if sorted_accts:
            dedup_key = f"{item.source.value}:{item.source_reference}:{item.category.value}:{sorted_accts}"
        else:
            sorted_txs = ",".join(sorted(item.transaction_ids))
            dedup_key = f"{item.source.value}:{item.source_reference}:{item.category.value}:{sorted_txs}"

        if dedup_key not in seen:
            seen[dedup_key] = item
            insertion_keys.append(dedup_key)
        else:
            existing = seen[dedup_key]
            # Merge with higher severity
            item_is_higher = _SEVERITY_ORDER.get(item.severity, 0) > _SEVERITY_ORDER.get(existing.severity, 0)
            merged_sev = item.severity if item_is_higher else existing.severity
            merged_title = item.title if item_is_higher else existing.title
            merged_desc = item.description if item_is_higher else existing.description

            # Union and sort references
            merged_txns = tuple(sorted(set(existing.transaction_ids) | set(item.transaction_ids)))
            merged_accts = tuple(sorted(set(existing.account_ids) | set(item.account_ids)))
            merged_devs = tuple(sorted(set(existing.device_ids) | set(item.device_ids)))
            merged_ips = tuple(sorted(set(existing.ip_addresses) | set(item.ip_addresses)))
            merged_ts = tuple(sorted(set(existing.timestamps) | set(item.timestamps)))

            # Merge metrics
            merged_metrics = dict(existing.metrics)
            merged_metrics.update(item.metrics)

            seen[dedup_key] = EvidenceItem(
                evidence_id=existing.evidence_id,
                category=existing.category,
                title=merged_title,
                description=merged_desc,
                severity=merged_sev,
                source=existing.source,
                source_reference=existing.source_reference,
                transaction_ids=merged_txns,
                account_ids=merged_accts,
                device_ids=merged_devs,
                ip_addresses=merged_ips,
                timestamps=merged_ts,
                metrics=merged_metrics,
                rank=existing.rank,
            )

    return [seen[k] for k in insertion_keys]
