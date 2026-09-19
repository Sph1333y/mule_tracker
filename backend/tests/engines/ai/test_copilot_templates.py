"""
MuleTrace AI — Unit Tests for Milestone 12 Copilot Templates & Determinism.
"""

from app.engines.ai.models import ActionPriority, ActionType, InvestigationContext
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
from app.engines.risk_fusion.models import RiskLevel


def _create_sample_evidence_package(items=(), score=85.0, level=RiskLevel.HIGH) -> EvidencePackage:
    return EvidencePackage(
        case_id="CAS-PKG-01",
        subject_id="ACC-FOCAL-01",
        transaction_id="TX-PKG-01",
        composite_risk_score=score,
        risk_level=level,
        evidence_items=tuple(items),
        evidence_summary="Deterministic test summary",
        source_coverage={"GRAPH": SourceCoverageStatus.AVAILABLE, "RULES": SourceCoverageStatus.AVAILABLE},
        total_evidence_count=len(items),
        severity_counts={},
    )


def test_render_risk_summary():
    # Without contributions
    res = render_risk_summary(75.5, "HIGH", None)
    assert "HIGH risk posture" in res
    assert "75.50/100.0" in res

    # With contributions
    contribs = {
        "graph": {"weighted_score": 0.40},
        "temporal": {"weighted_score": 0.25},
        "rules": {"weighted_score": 0.10},
    }
    res_c = render_risk_summary(75.5, "HIGH", contribs)
    assert "Primary detection drivers: graph (0.40), temporal (0.25), rules (0.10)." in res_c


def test_render_investigation_summary_empty():
    pkg = _create_sample_evidence_package(items=(), score=10.0, level=RiskLevel.LOW)
    summary = render_investigation_summary(pkg, "LOW", 10.0, subject_id="ACC-01")
    assert "for subject 'ACC-01'" in summary
    assert "No supporting forensic evidence items were recorded" in summary


def test_render_investigation_summary_with_signals():
    item1 = EvidenceItem(
        evidence_id="EVD-01",
        category=EvidenceCategory.CIRCULAR_ROUTING,
        title="Cycle Detected",
        description="Loop A-B-C-A",
        severity=EvidenceSeverity.CRITICAL,
        source=EvidenceSource.RULE,
        source_reference="RULE:R004",
    )
    item2 = EvidenceItem(
        evidence_id="EVD-02",
        category=EvidenceCategory.SHARED_INFRASTRUCTURE,
        title="Shared Device",
        description="Device shared with 3 accounts",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.GRAPH,
        source_reference="GRAPH:shared_device",
        device_ids=("DEV-01",),
    )
    pkg = _create_sample_evidence_package(items=[item1, item2], score=90.0, level=RiskLevel.CRITICAL)

    summary = render_investigation_summary(pkg, "CRITICAL", 90.0, subject_id="ACC-01")
    assert "90.00/100.0" in summary
    assert "supported by 2 forensic evidence item(s)" in summary
    assert "circular transaction routing" in summary
    assert "shared device or network infrastructure" in summary


def test_extract_key_findings():
    item = EvidenceItem(
        evidence_id="EVD-TEST-01",
        category=EvidenceCategory.TEMPORAL_ANOMALY,
        title="Rapid Outflow",
        description="Outflow within 60s",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.TEMPORAL,
        source_reference="TEMPORAL:rapid_in_out",
        metrics={"delay": 60},
    )
    pkg = _create_sample_evidence_package(items=[item])
    findings = extract_key_findings(pkg)

    assert len(findings) == 1
    assert findings[0].evidence_ids == ("EVD-TEST-01",)
    assert findings[0].severity == "HIGH"
    assert findings[0].category == "TEMPORAL_ANOMALY"
    assert findings[0].source == "TEMPORAL"
    assert findings[0].metrics["delay"] == 60


def test_generate_investigation_actions_all_types():
    items = [
        EvidenceItem(
            evidence_id="EVD-DEV",
            category=EvidenceCategory.SHARED_INFRASTRUCTURE,
            title="Shared Device Ring",
            description="Hardware fingerprint shared",
            severity=EvidenceSeverity.HIGH,
            source=EvidenceSource.GRAPH,
            source_reference="GRAPH:device_clustering",
            device_ids=("DEV-99",),
        ),
        EvidenceItem(
            evidence_id="EVD-NET",
            category=EvidenceCategory.SHARED_INFRASTRUCTURE,
            title="Shared IP Subnet",
            description="IP shared",
            severity=EvidenceSeverity.MEDIUM,
            source=EvidenceSource.GRAPH,
            source_reference="GRAPH:ip_sharing",
            ip_addresses=("10.0.0.1",),
        ),
        EvidenceItem(
            evidence_id="EVD-CYC",
            category=EvidenceCategory.CIRCULAR_ROUTING,
            title="Closed Cycle",
            description="Routing cycle",
            severity=EvidenceSeverity.CRITICAL,
            source=EvidenceSource.RULE,
            source_reference="RULE:R004_CIRCULAR_ROUTING",
        ),
        EvidenceItem(
            evidence_id="EVD-PAS",
            category=EvidenceCategory.TEMPORAL_ANOMALY,
            title="Rapid Pass-Through Ratio",
            description="Inbound funds drained immediately",
            severity=EvidenceSeverity.HIGH,
            source=EvidenceSource.TEMPORAL,
            source_reference="TEMPORAL:pass_through_ratio",
        ),
        EvidenceItem(
            evidence_id="EVD-VEL",
            category=EvidenceCategory.TEMPORAL_ANOMALY,
            title="Transaction Burst Velocity",
            description="15 transactions in 10 minutes",
            severity=EvidenceSeverity.HIGH,
            source=EvidenceSource.TEMPORAL,
            source_reference="TEMPORAL:velocity_burst",
        ),
        EvidenceItem(
            evidence_id="EVD-IN",
            category=EvidenceCategory.TOPOLOGICAL_PATTERN,
            title="Fan-In Aggregation",
            description="Multiple deposits aggregated",
            severity=EvidenceSeverity.MEDIUM,
            source=EvidenceSource.GRAPH,
            source_reference="GRAPH:fan_in_ratio",
        ),
        EvidenceItem(
            evidence_id="EVD-OUT",
            category=EvidenceCategory.TOPOLOGICAL_PATTERN,
            title="Fan-Out Distribution",
            description="Funds dispersed widely",
            severity=EvidenceSeverity.MEDIUM,
            source=EvidenceSource.GRAPH,
            source_reference="GRAPH:fan_out_ratio",
        ),
        EvidenceItem(
            evidence_id="EVD-MOD",
            category=EvidenceCategory.MODEL_PREDICTION,
            title="GraphSAGE Embeddings Anomaly",
            description="Model prediction anomalous",
            severity=EvidenceSeverity.MEDIUM,
            source=EvidenceSource.GRAPH_ML,
            source_reference="GRAPH_ML:prediction",
        ),
    ]

    pkg = _create_sample_evidence_package(items=items)
    actions = generate_investigation_actions(pkg)

    # Validate that critical action (cycle) is first
    assert actions[0].action_id == "ACT-CYC-001"
    assert actions[0].priority == ActionPriority.CRITICAL

    # Ensure no duplicates
    action_ids = [a.action_id for a in actions]
    assert len(action_ids) == len(set(action_ids))

    # Validate action types
    assert "ACT-DEV-001" in action_ids
    assert "ACT-NET-001" in action_ids
    assert "ACT-TEM-001" in action_ids
    assert "ACT-VEL-001" in action_ids
    assert "ACT-TOP-001" in action_ids
    assert "ACT-TOP-002" in action_ids
    assert "ACT-MOD-001" in action_ids

    # Validate non-punitive nature
    for a in actions:
        desc_lower = a.description.lower()
        assert "freeze" not in desc_lower
        assert "block" not in desc_lower
        assert "close account" not in desc_lower
        assert "guilty" not in desc_lower
        assert "criminal" not in desc_lower


def test_generate_follow_up_questions():
    items = [
        EvidenceItem(
            evidence_id="EVD-DEV",
            category=EvidenceCategory.SHARED_INFRASTRUCTURE,
            title="Shared Device",
            description="Device shared",
            severity=EvidenceSeverity.HIGH,
            source=EvidenceSource.GRAPH,
            source_reference="GRAPH:device",
            device_ids=("DEV-ABC",),
        ),
        EvidenceItem(
            evidence_id="EVD-CYC",
            category=EvidenceCategory.CIRCULAR_ROUTING,
            title="Cycle",
            description="Routing cycle",
            severity=EvidenceSeverity.CRITICAL,
            source=EvidenceSource.RULE,
            source_reference="RULE:cycle",
        ),
    ]
    pkg = _create_sample_evidence_package(items=items)
    questions = generate_follow_up_questions(pkg)

    assert len(questions) == 2
    assert any("DEV-ABC" in q for q in questions)
    assert any("circular transaction flow" in q for q in questions)


def test_generate_audit_limitations_with_missing_sources():
    pkg = EvidencePackage(
        case_id="CAS-01",
        subject_id="ACC-01",
        transaction_id="TX-01",
        composite_risk_score=50.0,
        risk_level=RiskLevel.MEDIUM,
        evidence_items=(),
        evidence_summary="Empty evidence",
        source_coverage={"GRAPH_ML": SourceCoverageStatus.UNAVAILABLE},
        total_evidence_count=0,
        severity_counts={},
    )
    ctx = InvestigationContext(case_id="CAS-01", evidence_package=pkg)
    limitations = generate_audit_limitations(ctx)

    assert any("without generative AI or external LLM inference" in lim for lim in limitations)
    assert any("inherited directly from M10 Risk Fusion" in lim for lim in limitations)
    assert any("No forensic evidence items were provided" in lim for lim in limitations)
    assert any("GRAPH_ML" in lim and "UNAVAILABLE" in lim for lim in limitations)


def test_isolated_temporal_velocity_evidence_regression():
    """Focused regression test for isolated TEMPORAL_ANOMALY without preceding pass-through.

    Proves:
    - No UnboundLocalError occurs.
    - Valid deterministic response is produced.
    - No fabricated evidence IDs appear.
    - Correct evidence references are linked.
    - No change to M10 risk score or level.
    - No mutation of upstream M11 EvidencePackage.
    """
    import copy
    from app.engines.ai.copilot import DeterministicInvestigationCopilot

    item = EvidenceItem(
        evidence_id="EVD-ISO-VEL-01",
        category=EvidenceCategory.TEMPORAL_ANOMALY,
        title="High Transaction Velocity",
        description="Burst of 10 rapid transfers within 60 seconds",
        severity=EvidenceSeverity.HIGH,
        source=EvidenceSource.TEMPORAL,
        source_reference="TEMPORAL:velocity_burst",
        metrics={"burst_count": 10, "interval_seconds": 60},
    )

    pkg = EvidencePackage(
        case_id="CAS-REG-001",
        subject_id="ACC-ISO-99",
        transaction_id="TX-REG-001",
        composite_risk_score=78.5,
        risk_level=RiskLevel.HIGH,
        evidence_items=(item,),
        evidence_summary="Isolated velocity burst anomaly",
        source_coverage={"TEMPORAL": SourceCoverageStatus.AVAILABLE},
        total_evidence_count=1,
        severity_counts={"HIGH": 1},
        metadata={"test_tag": "REGRESSION_TEST"},
    )

    pkg_snapshot = copy.deepcopy(pkg.to_dict())

    copilot = DeterministicInvestigationCopilot()
    ctx = InvestigationContext(case_id="CAS-REG-001", evidence_package=pkg)

    # 1. Proves no UnboundLocalError and produces valid response
    response = copilot.investigate_sync(ctx)
    assert response is not None

    # 2. Proves correct evidence references and zero fabricated evidence
    assert response.evidence_references == ("EVD-ISO-VEL-01",)
    assert len(response.key_findings) == 1
    assert response.key_findings[0].evidence_ids == ("EVD-ISO-VEL-01",)

    # 3. Proves correct action generation
    action_ids = [a.action_id for a in response.suggested_next_steps]
    assert "ACT-VEL-001" in action_ids
    assert "ACT-TEM-001" not in action_ids  # Rapid pass-through action should NOT be generated

    # 4. Proves M10 score and level preserved exactly
    assert response.composite_risk_score == 78.5
    assert response.risk_level == "HIGH"

    # 5. Proves M11 EvidencePackage is not mutated
    assert pkg.to_dict() == pkg_snapshot

