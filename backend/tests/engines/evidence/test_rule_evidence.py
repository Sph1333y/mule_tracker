"""
MuleTrace AI — Unit Tests for Rule Evidence Extraction (M5).
"""

from datetime import datetime, timezone

from app.domain.models import TransactionEvent
from app.engines.evidence.collectors import collect_rule_evidence
from app.engines.evidence.models import EvidenceCategory, EvidenceSeverity, EvidenceSource
from app.engines.rules.base import EvaluationResult, RuleMatchResult


def _create_sample_event() -> TransactionEvent:
    return TransactionEvent(
        transaction_id="TX_RULE_001",
        timestamp=datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc),
        sender_account="ACC_SRC_101",
        receiver_account="ACC_DST_202",
        amount=50000.0,
        currency="INR",
        channel="UPI",
        device_id="DEV_FINGERPRINT_99",
        ip_address="192.168.1.10",
    )


def test_collect_rule_evidence_single_match() -> None:
    """Verify single rule match extracts cleanly with preserved metadata."""
    event = _create_sample_event()
    eval_result = EvaluationResult(
        total_risk_score_delta=40,
        matches=[
            RuleMatchResult(
                rule_code="R004",
                rule_name="Mule Chain / Rapid Pass-Through",
                pattern_name="Mule Chain",
                matched=True,
                score_contribution=40,
                severity="HIGH",
                narrative="Account received funds and dispersed 95% within 3 minutes.",
            ),
            RuleMatchResult(
                rule_code="R001",
                rule_name="High Velocity",
                pattern_name="Velocity Spike",
                matched=False,
                score_contribution=0,
                severity="LOW",
                narrative="Transaction velocity normal.",
            ),
        ],
        flagged_patterns=["Mule Chain"],
        highest_severity="HIGH",
    )

    items = collect_rule_evidence(eval_result, event=event)

    # Only matched rules produce evidence
    assert len(items) == 1
    item = items[0]

    assert item.source == EvidenceSource.RULE
    assert item.source_reference == "RULE:R004"
    assert item.category == EvidenceCategory.RULE_VIOLATION
    assert item.severity == EvidenceSeverity.HIGH
    assert item.description == "Account received funds and dispersed 95% within 3 minutes."
    assert item.metrics["rule_code"] == "R004"
    assert item.metrics["score_contribution"] == 40
    assert "ACC_SRC_101" in item.account_ids
    assert "ACC_DST_202" in item.account_ids
    assert "TX_RULE_001" in item.transaction_ids
    assert "DEV_FINGERPRINT_99" in item.device_ids
    assert "192.168.1.10" in item.ip_addresses


def test_collect_rule_evidence_multiple_matches() -> None:
    """Verify multiple matched rules preserve individual severities and score contributions."""
    eval_result = EvaluationResult(
        total_risk_score_delta=85,
        matches=[
            RuleMatchResult(
                rule_code="R006",
                rule_name="Shared Device Syndicate",
                pattern_name="Device Ring",
                matched=True,
                score_contribution=45,
                severity="CRITICAL",
                narrative="Device shared across 4 high-risk accounts.",
            ),
            RuleMatchResult(
                rule_code="R007",
                rule_name="Dormant Account Activation",
                pattern_name="Dormancy Break",
                matched=True,
                score_contribution=40,
                severity="MEDIUM",
                narrative="Account inactive for 180 days suddenly transacting.",
            ),
        ],
        flagged_patterns=["Device Ring", "Dormancy Break"],
        highest_severity="CRITICAL",
    )

    items = collect_rule_evidence(eval_result)
    assert len(items) == 2

    codes = [i.metrics["rule_code"] for i in items]
    assert "R006" in codes
    assert "R007" in codes

    item_r006 = next(i for i in items if i.metrics["rule_code"] == "R006")
    item_r007 = next(i for i in items if i.metrics["rule_code"] == "R007")

    assert item_r006.severity == EvidenceSeverity.CRITICAL
    assert item_r007.severity == EvidenceSeverity.MEDIUM
    assert item_r006.metrics["score_contribution"] == 45
    assert item_r007.metrics["score_contribution"] == 40


def test_collect_rule_evidence_none_or_empty() -> None:
    """Verify None or empty rule evaluations safely return empty evidence lists."""
    assert collect_rule_evidence(None) == []
    empty_res = EvaluationResult(total_risk_score_delta=0, matches=[])
    assert collect_rule_evidence(empty_res) == []
