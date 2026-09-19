"""
MuleTrace AI — Deterministic Investigation Copilot Templates & Renderers.

Provides pure, deterministic template rendering and rule-based narrative synthesis
for Milestone 12 (Deterministic Investigation Copilot).

Architectural Boundary:
- Cloud-agnostic and framework-neutral (pure Python standard library).
- Zero LLM dependency (no OpenAI, Gemini, Bedrock, Ollama, Claude, prompt injection, etc.).
- Zero randomness or probabilistic text generation.
- Deterministic, stable ordering for all collections.
- Strictly non-punitive, evidence-based recommendations.
"""

from __future__ import annotations

from typing import Any, Optional

from app.engines.ai.models import (
    ActionPriority,
    ActionType,
    InvestigationContext,
    KeyFinding,
    SuggestedAction,
)
from app.engines.evidence.models import (
    EvidenceCategory,
    EvidenceItem,
    EvidencePackage,
    EvidenceSeverity,
    EvidenceSource,
    SourceCoverageStatus,
)


def render_risk_summary(
    composite_risk_score: float,
    risk_level: str,
    contributions: Optional[dict[str, Any]] = None,
) -> str:
    """Render a deterministic, factual summary of the composite risk assessment.

    Args:
        composite_risk_score: Score in [0.0, 100.0] preserved from M10.
        risk_level: Tier string (LOW, MEDIUM, HIGH, CRITICAL) preserved from M10.
        contributions: Optional mapping of modality names to contribution details or dicts.

    Returns:
        Structured string summarizing composite risk posture and top driver modalities.
    """
    base = (
        f"Subject assessment indicates a {risk_level} risk posture with an M10 composite "
        f"risk score of {composite_risk_score:.2f}/100.0."
    )

    if not contributions:
        return base

    # Sort modalities deterministically by weighted score descending, then alphabetically
    driver_items: list[tuple[str, float]] = []
    for mod_name, contrib in sorted(contributions.items(), key=lambda x: x[0]):
        if isinstance(contrib, dict):
            w_score = float(contrib.get("weighted_score", contrib.get("normalized_value", 0.0)))
        elif hasattr(contrib, "weighted_score"):
            w_score = float(contrib.weighted_score)
        else:
            w_score = 0.0
        driver_items.append((mod_name, w_score))

    # Rank by score desc
    driver_items.sort(key=lambda x: (-x[1], x[0]))
    active_drivers = [f"{name} ({score:.2f})" for name, score in driver_items if score > 0.0]

    if active_drivers:
        driver_str = ", ".join(active_drivers[:3])
        return f"{base} Primary detection drivers: {driver_str}."

    return base


def render_investigation_summary(
    evidence_package: Optional[EvidencePackage],
    risk_level: str,
    composite_risk_score: float,
    subject_id: Optional[str] = None,
) -> str:
    """Render a deterministic executive narrative synthesizing forensic evidence.

    Args:
        evidence_package: M11 evidence package (read-only).
        risk_level: Categorical risk tier.
        composite_risk_score: Numeric score [0.0, 100.0].
        subject_id: Optional account or entity ID.

    Returns:
        Deterministic narrative paragraph.
    """
    subject_ref = f"for subject '{subject_id}'" if subject_id else "for the evaluated subject"

    if evidence_package is None or not evidence_package.evidence_items:
        return (
            f"Case analysis {subject_ref} establishes a {risk_level} risk profile "
            f"({composite_risk_score:.2f}/100.0). No supporting forensic evidence items were recorded "
            f"in the evidence package for this evaluation."
        )

    items = evidence_package.evidence_items
    count = len(items)

    # Deterministically extract distinct signal themes
    themes: list[str] = []
    seen_categories: set[str] = set()

    for item in items:
        cat = item.category.value if hasattr(item.category, "value") else str(item.category)
        if cat in seen_categories:
            continue
        seen_categories.add(cat)

        if cat == EvidenceCategory.CIRCULAR_ROUTING.value:
            themes.append("circular transaction routing")
        elif cat == EvidenceCategory.SHARED_INFRASTRUCTURE.value:
            themes.append("shared device or network infrastructure")
        elif cat == EvidenceCategory.TEMPORAL_ANOMALY.value:
            themes.append("temporal burst or rapid pass-through velocity")
        elif cat == EvidenceCategory.TOPOLOGICAL_PATTERN.value:
            themes.append("high-degree structural network topology")
        elif cat == EvidenceCategory.MODEL_PREDICTION.value:
            themes.append("predictive machine learning anomaly scores")
        elif cat == EvidenceCategory.RULE_VIOLATION.value:
            themes.append("deterministic rule threshold triggers")

    if not themes:
        themes_desc = "correlated forensic anomalies"
    elif len(themes) == 1:
        themes_desc = themes[0]
    elif len(themes) == 2:
        themes_desc = f"{themes[0]} and {themes[1]}"
    else:
        themes_desc = f"{', '.join(themes[:-1])}, and {themes[-1]}"

    narrative = (
        f"Case analysis {subject_ref} reflects an aggregate {risk_level} risk profile "
        f"({composite_risk_score:.2f}/100.0) supported by {count} forensic evidence item(s). "
        f"Key analytical signals demonstrate {themes_desc}. "
        f"Investigative review is recommended to corroborate behavioral patterns across linked entity networks."
    )

    return narrative


def extract_key_findings(
    evidence_package: Optional[EvidencePackage],
) -> tuple[KeyFinding, ...]:
    """Extract structured, evidence-linked findings preserving M11 deterministic ranking.

    Args:
        evidence_package: Upstream M11 EvidencePackage.

    Returns:
        Tuple of immutable KeyFinding instances referencing valid evidence IDs.
    """
    if evidence_package is None or not evidence_package.evidence_items:
        return ()

    findings: list[KeyFinding] = []
    for item in evidence_package.evidence_items:
        cat_val = item.category.value if hasattr(item.category, "value") else str(item.category)
        sev_val = item.severity.value if hasattr(item.severity, "value") else str(item.severity)
        src_val = item.source.value if hasattr(item.source, "value") else str(item.source)

        finding_text = f"{item.title}: {item.description}"
        finding = KeyFinding(
            finding=finding_text,
            evidence_ids=(item.evidence_id,),
            severity=sev_val,
            category=cat_val,
            source=src_val,
            metrics=dict(item.metrics) if item.metrics else {},
        )
        findings.append(finding)

    return tuple(findings)


def generate_investigation_actions(
    evidence_package: Optional[EvidencePackage],
) -> tuple[SuggestedAction, ...]:
    """Generate prioritized, deterministic investigative actions strictly based on evidence.

    Actions are strictly non-accusatory and non-regulatory. They suggest investigative
    verification and data auditing steps, never automated account blocking or law enforcement actions.

    Args:
        evidence_package: Upstream M11 EvidencePackage.

    Returns:
        Tuple of SuggestedAction instances.
    """
    if evidence_package is None or not evidence_package.evidence_items:
        return (
            SuggestedAction(
                action_id="ACT-GEN-001",
                title="Conduct baseline account audit",
                description="Review subject profile data, KYC documentation, and recent transaction records.",
                priority=ActionPriority.LOW,
                action_type=ActionType.GENERAL_AUDIT,
                related_evidence_ids=(),
            ),
        )

    # Collect related evidence IDs per action archetype
    action_map: dict[str, dict[str, Any]] = {}

    for item in evidence_package.evidence_items:
        cat = item.category.value if hasattr(item.category, "value") else str(item.category)
        ref = item.source_reference.lower()
        title_lower = item.title.lower()
        desc_lower = item.description.lower()

        # Shared Device
        if (
            cat == EvidenceCategory.SHARED_INFRASTRUCTURE.value
            and (item.device_ids or "device" in ref or "device" in title_lower)
        ):
            key = "shared_device"
            if key not in action_map:
                action_map[key] = {
                    "action_id": "ACT-DEV-001",
                    "title": "Review shared device cluster",
                    "description": "Inspect accounts and authentication events associated with the shared hardware fingerprint(s).",
                    "priority": ActionPriority.HIGH,
                    "action_type": ActionType.DEVICE_VERIFICATION,
                    "evidence_ids": [],
                }
            action_map[key]["evidence_ids"].append(item.evidence_id)

        # Shared IP
        if (
            cat == EvidenceCategory.SHARED_INFRASTRUCTURE.value
            and (item.ip_addresses or "ip" in ref or "ip" in title_lower)
        ):
            key = "shared_ip"
            if key not in action_map:
                action_map[key] = {
                    "action_id": "ACT-NET-001",
                    "title": "Review shared IP network entities",
                    "description": "Verify session logs and counterparty accounts originating from the flagged IP address(es).",
                    "priority": ActionPriority.MEDIUM,
                    "action_type": ActionType.COUNTERPARTY_VERIFICATION,
                    "evidence_ids": [],
                }
            action_map[key]["evidence_ids"].append(item.evidence_id)

        # Circular Flow
        if (
            cat == EvidenceCategory.CIRCULAR_ROUTING.value
            or "cycle" in ref
            or "circular" in title_lower
            or "cycle" in desc_lower
        ):
            key = "circular_routing"
            if key not in action_map:
                action_map[key] = {
                    "action_id": "ACT-CYC-001",
                    "title": "Trace circular fund routing cycle",
                    "description": "Examine intermediary accounts, timing intervals, and balance retention in the detected circular transaction loop.",
                    "priority": ActionPriority.CRITICAL,
                    "action_type": ActionType.TOPOLOGY_ANALYSIS,
                    "evidence_ids": [],
                }
            action_map[key]["evidence_ids"].append(item.evidence_id)

        # Rapid pass-through
        is_rapid_passthrough = False
        if (
            "pass_through" in ref
            or "rapid pass-through" in title_lower
            or "pass-through" in desc_lower
            or "r003" in ref
        ):
            is_rapid_passthrough = True
            key = "rapid_passthrough"
            if key not in action_map:
                action_map[key] = {
                    "action_id": "ACT-TEM-001",
                    "title": "Audit rapid pass-through sequence",
                    "description": "Analyze transaction timestamps and amounts to verify inbound deposit and rapid outbound disbursement intervals.",
                    "priority": ActionPriority.HIGH,
                    "action_type": ActionType.TEMPORAL_AUDIT,
                    "evidence_ids": [],
                }
            action_map[key]["evidence_ids"].append(item.evidence_id)

        # Velocity / Burst
        if (
            (cat == EvidenceCategory.TEMPORAL_ANOMALY.value and not is_rapid_passthrough)
            or "velocity" in ref
            or "burst" in title_lower
            or "velocity" in title_lower
        ):
            key = "high_velocity"
            if key not in action_map:
                action_map[key] = {
                    "action_id": "ACT-VEL-001",
                    "title": "Examine high-velocity transaction burst",
                    "description": "Evaluate transaction volume and frequency spikes against established baseline historical activity.",
                    "priority": ActionPriority.HIGH,
                    "action_type": ActionType.TEMPORAL_AUDIT,
                    "evidence_ids": [],
                }
            action_map[key]["evidence_ids"].append(item.evidence_id)

        # Fan-in
        if "fan_in" in ref or "fan-in" in title_lower or "fan-in" in desc_lower or "in_degree" in ref:
            key = "fan_in"
            if key not in action_map:
                action_map[key] = {
                    "action_id": "ACT-TOP-001",
                    "title": "Analyze fan-in transaction concentration",
                    "description": "Examine source accounts and transfer rationales contributing to aggregated incoming payment flows.",
                    "priority": ActionPriority.MEDIUM,
                    "action_type": ActionType.TOPOLOGY_ANALYSIS,
                    "evidence_ids": [],
                }
            action_map[key]["evidence_ids"].append(item.evidence_id)

        # Fan-out
        if "fan_out" in ref or "fan-out" in title_lower or "fan-out" in desc_lower or "out_degree" in ref:
            key = "fan_out"
            if key not in action_map:
                action_map[key] = {
                    "action_id": "ACT-TOP-002",
                    "title": "Inspect fan-out disbursement distribution",
                    "description": "Review destination beneficiaries receiving rapid dispersed outbound transfers.",
                    "priority": ActionPriority.MEDIUM,
                    "action_type": ActionType.TOPOLOGY_ANALYSIS,
                    "evidence_ids": [],
                }
            action_map[key]["evidence_ids"].append(item.evidence_id)

        # ML anomaly
        if cat == EvidenceCategory.MODEL_PREDICTION.value:
            key = "ml_prediction"
            if key not in action_map:
                action_map[key] = {
                    "action_id": "ACT-MOD-001",
                    "title": "Review machine learning anomaly signals",
                    "description": "Inspect predictive model feature deviations and topological embedding scores flagged by automated classifiers.",
                    "priority": ActionPriority.MEDIUM,
                    "action_type": ActionType.MODEL_ANOMALY_REVIEW,
                    "evidence_ids": [],
                }
            action_map[key]["evidence_ids"].append(item.evidence_id)

        # General Rule Violations
        if cat == EvidenceCategory.RULE_VIOLATION.value and not any(
            k in action_map for k in ["circular_routing", "rapid_passthrough", "shared_device"]
        ):
            key = "rule_violation"
            if key not in action_map:
                action_map[key] = {
                    "action_id": "ACT-RUL-001",
                    "title": "Verify triggered rule criteria",
                    "description": "Validate transaction records against triggered rule thresholds and perimeter constraints.",
                    "priority": ActionPriority.MEDIUM,
                    "action_type": ActionType.INVESTIGATIVE_REVIEW,
                    "evidence_ids": [],
                }
            action_map[key]["evidence_ids"].append(item.evidence_id)

    # Order actions deterministically by priority (CRITICAL -> HIGH -> MEDIUM -> LOW) then action_id
    priority_weights = {
        ActionPriority.CRITICAL: 0,
        ActionPriority.HIGH: 1,
        ActionPriority.MEDIUM: 2,
        ActionPriority.LOW: 3,
    }

    action_list: list[SuggestedAction] = []
    for d in action_map.values():
        action_list.append(
            SuggestedAction(
                action_id=d["action_id"],
                title=d["title"],
                description=d["description"],
                priority=d["priority"],
                action_type=d["action_type"],
                related_evidence_ids=tuple(sorted(d["evidence_ids"])),
            )
        )

    action_list.sort(key=lambda a: (priority_weights.get(a.priority, 99), a.action_id))

    if not action_list:
        action_list.append(
            SuggestedAction(
                action_id="ACT-GEN-001",
                title="Conduct baseline account audit",
                description="Review subject profile data, KYC documentation, and recent transaction records.",
                priority=ActionPriority.LOW,
                action_type=ActionType.GENERAL_AUDIT,
                related_evidence_ids=tuple(i.evidence_id for i in evidence_package.evidence_items),
            )
        )

    return tuple(action_list)


def generate_follow_up_questions(
    evidence_package: Optional[EvidencePackage],
) -> tuple[str, ...]:
    """Generate targeted, evidence-derived investigative questions.

    Questions are purely inquisitive and strictly tied to existing evidence items.

    Args:
        evidence_package: Upstream M11 EvidencePackage.

    Returns:
        Tuple of deterministic question strings.
    """
    if evidence_package is None or not evidence_package.evidence_items:
        return (
            "Are additional transaction logs or counterparty KYC records available for this subject?",
        )

    questions: list[str] = []
    seen: set[str] = set()

    for item in evidence_package.evidence_items:
        cat = item.category.value if hasattr(item.category, "value") else str(item.category)
        ref = item.source_reference.lower()
        title_lower = item.title.lower()
        desc_lower = item.description.lower()

        # Shared Device
        if (
            (cat == EvidenceCategory.SHARED_INFRASTRUCTURE.value and (item.device_ids or "device" in ref))
            and "device_q" not in seen
        ):
            seen.add("device_q")
            dev_str = f" ({', '.join(item.device_ids)})" if item.device_ids else ""
            questions.append(
                f"Which other accounts have authenticated using the identified device ID{dev_str}?"
            )

        # Shared IP
        if (
            (cat == EvidenceCategory.SHARED_INFRASTRUCTURE.value and (item.ip_addresses or "ip" in ref))
            and "ip_q" not in seen
        ):
            seen.add("ip_q")
            ip_str = f" ({', '.join(item.ip_addresses)})" if item.ip_addresses else ""
            questions.append(
                f"Are there concurrent active sessions or proxy/VPN signatures linked to the shared IP{ip_str}?"
            )

        # Circular Flow
        if (
            (cat == EvidenceCategory.CIRCULAR_ROUTING.value or "cycle" in ref or "circular" in title_lower)
            and "cycle_q" not in seen
        ):
            seen.add("cycle_q")
            questions.append(
                "What accounts and counterparties participate in the detected circular transaction flow?"
            )

        # Rapid Pass-Through
        if (
            ("pass_through" in ref or "pass-through" in title_lower or "pass-through" in desc_lower)
            and "passthrough_q" not in seen
        ):
            seen.add("passthrough_q")
            questions.append(
                "What is the exact time delta between inbound fund credits and outbound debits across the flagged sequence?"
            )

        # Fan-in
        if ("fan_in" in ref or "fan-in" in title_lower or "in_degree" in ref) and "fanin_q" not in seen:
            seen.add("fanin_q")
            questions.append(
                "What is the commercial or personal relationship connecting the multiple originators in the fan-in pattern?"
            )

        # Fan-out
        if ("fan_out" in ref or "fan-out" in title_lower or "out_degree" in ref) and "fanout_q" not in seen:
            seen.add("fanout_q")
            questions.append(
                "Are the destination accounts in the outbound distribution cluster newly activated or historically linked?"
            )

        # High Velocity
        if ("velocity" in ref or "burst" in title_lower or "velocity" in title_lower) and "vel_q" not in seen:
            seen.add("vel_q")
            questions.append(
                "Does the burst in transaction velocity coincide with recent authentication changes or credential updates?"
            )

    if not questions:
        questions.append(
            "Do supplementary behavioral logs or device records exist for the transactions in this package?"
        )

    # Deterministic sorting
    questions.sort()
    return tuple(questions)


def generate_audit_limitations(
    context: InvestigationContext,
) -> tuple[str, ...]:
    """Compile deterministic audit disclosures and operational boundaries.

    Ensures total transparency regarding M10/M11 boundaries and zero LLM usage.

    Args:
        context: The investigation context.

    Returns:
        Tuple of limitation and governance statements.
    """
    limitations: list[str] = [
        "Investigation guidance and executive narrative are generated deterministically via structured templates without generative AI or external LLM inference.",
        "Risk level and composite score are inherited directly from M10 Risk Fusion without recalculation or scoring drift.",
        "All key findings and recommended actions strictly reference verified evidence items from the M11 EvidencePackage.",
    ]

    pkg = context.evidence_package
    if pkg is None or not pkg.evidence_items:
        limitations.append(
            "No forensic evidence items were provided in the evaluation context."
        )

    if pkg and pkg.source_coverage:
        # Check for unavailable or missing modalities
        for src, status in sorted(pkg.source_coverage.items()):
            status_val = status.value if hasattr(status, "value") else str(status)
            if status_val in (SourceCoverageStatus.UNAVAILABLE.value, SourceCoverageStatus.MISSING.value):
                limitations.append(
                    f"Analytical source '{src}' was marked as {status_val} during evidence collection."
                )

    if context.fusion_result and context.fusion_result.unavailable_modalities:
        for mod in sorted(context.fusion_result.unavailable_modalities):
            limitations.append(
                f"Risk fusion modality '{mod}' was unavailable during composite risk calculation."
            )

    return tuple(limitations)
