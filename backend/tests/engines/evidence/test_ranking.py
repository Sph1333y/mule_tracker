"""
MuleTrace AI — Unit Tests for Evidence Ranking Policy.
"""

from app.engines.evidence.models import (
    EvidenceCategory,
    EvidenceItem,
    EvidenceSeverity,
    EvidenceSource,
)
from app.engines.evidence.ranking import rank_evidence_items


def test_ranking_severity_precedence() -> None:
    """Verify that higher severity items are always ranked above lower severity items."""
    item_med = EvidenceItem(
        evidence_id="EVD-01",
        category=EvidenceCategory.RULE_VIOLATION,
        title="Medium Item",
        description="",
        severity=EvidenceSeverity.MEDIUM,
        source=EvidenceSource.RULE,
        source_reference="RULE:R001",
    )
    item_crit = EvidenceItem(
        evidence_id="EVD-02",
        category=EvidenceCategory.TOPOLOGICAL_PATTERN,
        title="Critical Item",
        description="",
        severity=EvidenceSeverity.CRITICAL,
        source=EvidenceSource.GRAPH,
        source_reference="GRAPH:cycle",
    )
    item_high = EvidenceItem(
        evidence_id="EVD-03",
        category=EvidenceCategory.TEMPORAL_ANOMALY,
        title="High Item",
        description="",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.TEMPORAL,
        source_reference="TEMPORAL:burst",
    )

    ranked = rank_evidence_items([item_med, item_crit, item_high])

    assert len(ranked) == 3
    assert ranked[0].severity == EvidenceSeverity.CRITICAL
    assert ranked[0].rank == 1
    assert ranked[0].evidence_id == "EVD-02"

    assert ranked[1].severity == EvidenceSeverity.HIGH
    assert ranked[1].rank == 2
    assert ranked[1].evidence_id == "EVD-03"

    assert ranked[2].severity == EvidenceSeverity.MEDIUM
    assert ranked[2].rank == 3
    assert ranked[2].evidence_id == "EVD-01"


def test_ranking_source_priority_within_same_severity() -> None:
    """Verify that within the same severity tier, source authority determines rank."""
    # RULE (70) > GRAPH (60) > TEMPORAL (50) > ML (40)
    rule_item = EvidenceItem(
        evidence_id="EVD-RULE",
        category=EvidenceCategory.RULE_VIOLATION,
        title="Rule High",
        description="",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.RULE,
        source_reference="RULE:R004",
    )
    graph_item = EvidenceItem(
        evidence_id="EVD-GRAPH",
        category=EvidenceCategory.SHARED_INFRASTRUCTURE,
        title="Graph High",
        description="",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.GRAPH,
        source_reference="GRAPH:shared_device",
    )
    temp_item = EvidenceItem(
        evidence_id="EVD-TEMP",
        category=EvidenceCategory.TEMPORAL_ANOMALY,
        title="Temporal High",
        description="",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.TEMPORAL,
        source_reference="TEMPORAL:rapid_in_out",
    )
    ml_item = EvidenceItem(
        evidence_id="EVD-ML",
        category=EvidenceCategory.MODEL_PREDICTION,
        title="ML High",
        description="",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.TABULAR_ML,
        source_reference="TABULAR_ML:xgb",
    )

    ranked = rank_evidence_items([ml_item, temp_item, graph_item, rule_item])

    assert [r.source for r in ranked] == [
        EvidenceSource.RULE,
        EvidenceSource.GRAPH,
        EvidenceSource.TEMPORAL,
        EvidenceSource.TABULAR_ML,
    ]


def test_ranking_deterministic_tie_breaker() -> None:
    """Verify identical severity and source items are tie-broken deterministically by evidence_id."""
    item_b = EvidenceItem(
        evidence_id="EVD-B",
        category=EvidenceCategory.RULE_VIOLATION,
        title="Rule B",
        description="",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.RULE,
        source_reference="RULE:R002",
    )
    item_a = EvidenceItem(
        evidence_id="EVD-A",
        category=EvidenceCategory.RULE_VIOLATION,
        title="Rule A",
        description="",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.RULE,
        source_reference="RULE:R001",
    )

    ranked = rank_evidence_items([item_b, item_a])
    assert ranked[0].evidence_id == "EVD-A"
    assert ranked[1].evidence_id == "EVD-B"
