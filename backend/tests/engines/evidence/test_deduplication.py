"""
MuleTrace AI — Unit Tests for Evidence Deduplication.
"""

from app.engines.evidence.deduplication import deduplicate_evidence_items
from app.engines.evidence.models import (
    EvidenceCategory,
    EvidenceItem,
    EvidenceSeverity,
    EvidenceSource,
)


def test_deduplicate_identical_items() -> None:
    """Verify duplicate items sharing identical keys are collapsed into one."""
    item1 = EvidenceItem(
        evidence_id="EVD-RULE-R004-1",
        category=EvidenceCategory.RULE_VIOLATION,
        title="Mule Chain",
        description="Fast pass-through",
        severity=EvidenceSeverity.MEDIUM,
        source=EvidenceSource.RULE,
        source_reference="RULE:R004",
        transaction_ids=("TX101",),
        account_ids=("ACC1",),
        metrics={"score": 40},
    )
    # Duplicate with higher severity and extra transaction ID
    item2 = EvidenceItem(
        evidence_id="EVD-RULE-R004-2",
        category=EvidenceCategory.RULE_VIOLATION,
        title="Mule Chain",
        description="Fast pass-through",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.RULE,
        source_reference="RULE:R004",
        transaction_ids=("TX101", "TX102"),
        account_ids=("ACC1",),
        metrics={"score": 40, "extra": "data"},
    )

    deduped = deduplicate_evidence_items([item1, item2])
    assert len(deduped) == 1
    res = deduped[0]

    # Merged item keeps higher severity
    assert res.severity == EvidenceSeverity.HIGH
    # Merged item unions transactions
    assert "TX101" in res.transaction_ids
    assert "TX102" in res.transaction_ids
    # Merged item combines metrics
    assert res.metrics["score"] == 40
    assert res.metrics["extra"] == "data"


def test_distinct_items_preserved() -> None:
    """Verify genuinely distinct evidence items are preserved in order."""
    item1 = EvidenceItem(
        evidence_id="EVD-RULE-R001",
        category=EvidenceCategory.RULE_VIOLATION,
        title="Velocity",
        description="",
        severity=EvidenceSeverity.LOW,
        source=EvidenceSource.RULE,
        source_reference="RULE:R001",
    )
    item2 = EvidenceItem(
        evidence_id="EVD-RULE-R002",
        category=EvidenceCategory.RULE_VIOLATION,
        title="Fan In",
        description="",
        severity=EvidenceSeverity.MEDIUM,
        source=EvidenceSource.RULE,
        source_reference="RULE:R002",
    )

    deduped = deduplicate_evidence_items([item1, item2])
    assert len(deduped) == 2
    assert deduped[0].evidence_id == "EVD-RULE-R001"
    assert deduped[1].evidence_id == "EVD-RULE-R002"
