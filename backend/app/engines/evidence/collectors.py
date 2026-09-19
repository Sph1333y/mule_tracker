"""
MuleTrace AI — Forensic Evidence Collectors.

Provides modular, read-only extraction routines mapping upstream outputs
from M1, M5, M6, M7, M8, M9, and M10 into standardized EvidenceItem instances.

Architectural Boundary:
- Read-only: never alters upstream domain objects.
- Zero recalculation: consumes precomputed values from upstream engines.
- Zero LLM dependency.
- Deterministic: consistent output given identical input.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.domain.interfaces import ModelPrediction
from app.domain.models import TransactionEvent
from app.engines.evidence.models import (
    EvidenceCategory,
    EvidenceItem,
    EvidenceSeverity,
    EvidenceSource,
)
from app.engines.evidence.provenance import generate_evidence_id
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.engines.risk_fusion.models import FusionResult, RiskLevel
from app.engines.rules.base import EvaluationResult, RuleMatchResult
from app.engines.temporal.temporal_models import TemporalFeatures

logger = logging.getLogger("app.engines.evidence.collectors")


def _severity_from_string(sev_str: str) -> EvidenceSeverity:
    """Safely map string severity to EvidenceSeverity enum."""
    clean = str(sev_str).strip().upper()
    mapping = {
        "CRITICAL": EvidenceSeverity.CRITICAL,
        "HIGH": EvidenceSeverity.HIGH,
        "MEDIUM": EvidenceSeverity.MEDIUM,
        "LOW": EvidenceSeverity.LOW,
        "INFO": EvidenceSeverity.INFO,
    }
    return mapping.get(clean, EvidenceSeverity.LOW)


# ── 1. Rule Evidence Collector (M5) ─────────────────────────────────────────


def collect_rule_evidence(
    rule_signals: Optional[EvaluationResult | list[RuleMatchResult] | dict[str, Any]],
    event: Optional[TransactionEvent] = None,
) -> list[EvidenceItem]:
    """Extract deterministic forensic evidence from M5 rule engine results.

    Preserves rule IDs, names, severities, score contributions, and narratives
    without re-evaluating or modifying any rule logic.
    """
    if rule_signals is None:
        return []

    items: list[EvidenceItem] = []
    matched_results: list[RuleMatchResult] = []

    if isinstance(rule_signals, EvaluationResult):
        matched_results = [m for m in rule_signals.matches if m.matched]
    elif isinstance(rule_signals, list):
        for m in rule_signals:
            if isinstance(m, RuleMatchResult) and m.matched:
                matched_results.append(m)
    elif isinstance(rule_signals, dict):
        # Support dictionary representation if passed
        matches_raw = rule_signals.get("matches", [])
        for m_raw in matches_raw:
            if isinstance(m_raw, dict) and m_raw.get("matched", True):
                code = str(m_raw.get("rule_code", "UNKNOWN"))
                name = str(m_raw.get("rule_name", code))
                pat = str(m_raw.get("pattern_name", name))
                score = int(m_raw.get("score_contribution", 0))
                sev = str(m_raw.get("severity", "LOW"))
                narr = str(m_raw.get("narrative", f"Rule {code} triggered."))
                matched_results.append(
                    RuleMatchResult(
                        rule_code=code,
                        rule_name=name,
                        pattern_name=pat,
                        matched=True,
                        score_contribution=score,
                        severity=sev,
                        narrative=narr,
                    )
                )

    txn_ids: tuple[str, ...] = (event.transaction_id,) if event and event.transaction_id else ()
    acct_ids: tuple[str, ...] = (
        tuple(filter(None, [event.sender_account, event.receiver_account]))
        if event
        else ()
    )
    dev_ids: tuple[str, ...] = (event.device_id,) if event and event.device_id else ()
    ip_addrs: tuple[str, ...] = (event.ip_address,) if event and event.ip_address else ()
    timestamps: tuple[str, ...] = (
        (event.timestamp.isoformat(),) if event and event.timestamp else ()
    )

    for match in matched_results:
        source_ref = f"RULE:{match.rule_code}"
        severity = _severity_from_string(match.severity)
        category = EvidenceCategory.RULE_VIOLATION

        evidence_id = generate_evidence_id(
            source=EvidenceSource.RULE,
            source_reference=source_ref,
            category=category,
            account_ids=acct_ids,
            transaction_ids=txn_ids,
        )

        title = f"Forensic Rule {match.rule_code} Triggered ({match.pattern_name})"
        desc = (
            match.narrative
            if match.narrative
            else f"Rule {match.rule_code} ({match.rule_name}) flagged suspicious pattern with severity {match.severity}."
        )

        metrics = {
            "rule_code": match.rule_code,
            "rule_name": match.rule_name,
            "pattern_name": match.pattern_name,
            "score_contribution": match.score_contribution,
            "original_severity": match.severity,
        }

        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                category=category,
                title=title,
                description=desc,
                severity=severity,
                source=EvidenceSource.RULE,
                source_reference=source_ref,
                transaction_ids=txn_ids,
                account_ids=acct_ids,
                device_ids=dev_ids,
                ip_addresses=ip_addrs,
                timestamps=timestamps,
                metrics=metrics,
            )
        )

    return items


# ── 2. Temporal Evidence Collector (M6) ─────────────────────────────────────


def collect_temporal_evidence(
    temporal_features: Optional[TemporalFeatures],
    event: Optional[TransactionEvent] = None,
) -> list[EvidenceItem]:
    """Extract deterministic temporal evidence from M6 TemporalFeatures.

    Consumes precomputed rolling counts, burst flags, and pass-through sequences
    without re-evaluating temporal sliding windows.
    """
    if temporal_features is None:
        return []

    items: list[EvidenceItem] = []
    base_txns: tuple[str, ...] = (event.transaction_id,) if event and event.transaction_id else ()
    base_accts: tuple[str, ...] = (
        tuple(filter(None, [event.sender_account, event.receiver_account]))
        if event
        else ()
    )

    # A. Rapid In/Out Pass-Through
    if temporal_features.rapid_in_out_detected:
        source_ref = "TEMPORAL:rapid_in_out"
        category = EvidenceCategory.TEMPORAL_ANOMALY
        delay = temporal_features.rapid_in_out_delay_seconds
        ratio = temporal_features.rapid_in_out_ratio

        # Contributing txns and accounts from pass-through event if available
        pass_txns = list(base_txns)
        pass_accts = list(base_accts)
        if temporal_features.rapid_in_out_events:
            for pt in temporal_features.rapid_in_out_events:
                if pt.incoming_transaction_id and pt.incoming_transaction_id not in pass_txns:
                    pass_txns.append(pt.incoming_transaction_id)
                if pt.outgoing_transaction_id and pt.outgoing_transaction_id not in pass_txns:
                    pass_txns.append(pt.outgoing_transaction_id)
                if pt.account_id and pt.account_id not in pass_accts:
                    pass_accts.append(pt.account_id)

        delay_str = f"{delay:.1f}s" if delay is not None else "immediate"
        title = "Rapid In/Out Fund Pass-Through"
        description = (
            f"Funds rapidly routed through account within {delay_str} with "
            f"turnaround ratio of {ratio:.1%}."
        )

        severity = (
            EvidenceSeverity.CRITICAL
            if (delay is not None and delay <= 300 and ratio >= 0.85)
            else EvidenceSeverity.HIGH
        )

        evidence_id = generate_evidence_id(
            source=EvidenceSource.TEMPORAL,
            source_reference=source_ref,
            category=category,
            account_ids=tuple(pass_accts),
            transaction_ids=tuple(pass_txns),
        )

        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                category=category,
                title=title,
                description=description,
                severity=severity,
                source=EvidenceSource.TEMPORAL,
                source_reference=source_ref,
                transaction_ids=tuple(pass_txns),
                account_ids=tuple(pass_accts),
                metrics={
                    "delay_seconds": delay,
                    "pass_through_ratio": round(ratio, 4),
                    "events_count": len(temporal_features.rapid_in_out_events),
                },
            )
        )

    # B. Burst Activity
    if temporal_features.burst_detected:
        source_ref = "TEMPORAL:burst"
        category = EvidenceCategory.TEMPORAL_ANOMALY
        burst_txs = tuple(temporal_features.burst_transaction_ids) or base_txns
        count = temporal_features.burst_count

        title = f"High Frequency Transaction Burst ({count} Txns)"
        description = (
            f"Sudden concentration of {count} transactions executed within a short burst window, "
            f"indicating automated or coordinated structuring."
        )
        severity = EvidenceSeverity.HIGH if count >= 5 else EvidenceSeverity.MEDIUM

        evidence_id = generate_evidence_id(
            source=EvidenceSource.TEMPORAL,
            source_reference=source_ref,
            category=category,
            account_ids=base_accts,
            transaction_ids=burst_txs,
        )

        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                category=category,
                title=title,
                description=description,
                severity=severity,
                source=EvidenceSource.TEMPORAL,
                source_reference=source_ref,
                transaction_ids=burst_txs,
                account_ids=base_accts,
                metrics={"burst_count": count},
            )
        )

    # C. High 1-Hour Velocity
    if temporal_features.transaction_count_1h >= 5:
        source_ref = "TEMPORAL:velocity_1h"
        category = EvidenceCategory.TEMPORAL_ANOMALY
        tx_count = temporal_features.transaction_count_1h
        vol = temporal_features.amount_sum_1h

        window_txs = list(base_txns)
        if "1h" in temporal_features.windows:
            for tid in temporal_features.windows["1h"].contributing_transaction_ids:
                if tid not in window_txs:
                    window_txs.append(tid)

        title = f"Elevated 1-Hour Transaction Velocity ({tx_count} Txns)"
        description = (
            f"Account completed {tx_count} transactions totaling ₹{vol:,.2f} within rolling 1-hour window."
        )
        severity = EvidenceSeverity.HIGH if tx_count >= 10 else EvidenceSeverity.MEDIUM

        evidence_id = generate_evidence_id(
            source=EvidenceSource.TEMPORAL,
            source_reference=source_ref,
            category=category,
            account_ids=base_accts,
            transaction_ids=tuple(window_txs),
        )

        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                category=category,
                title=title,
                description=description,
                severity=severity,
                source=EvidenceSource.TEMPORAL,
                source_reference=source_ref,
                transaction_ids=tuple(window_txs),
                account_ids=base_accts,
                metrics={
                    "transaction_count_1h": tx_count,
                    "amount_sum_1h": round(vol, 2),
                },
            )
        )

    return items


# ── 3. Graph Evidence Collector (M7) ────────────────────────────────────────


def collect_graph_evidence(
    graph_features: Optional[GraphFeatures],
    event: Optional[TransactionEvent] = None,
) -> list[EvidenceItem]:
    """Extract deterministic topological evidence from M7 GraphFeatures.

    Consumes precomputed cycles, shared device/IP clusters, and fan ratios
    without re-traversing the graph repository.
    """
    if graph_features is None:
        return []

    items: list[EvidenceItem] = []
    base_txns: tuple[str, ...] = (event.transaction_id,) if event and event.transaction_id else ()
    primary_acct = graph_features.account_id

    # A. Circular Flow Routing Loop
    if graph_features.has_cycle or len(graph_features.cycles) > 0:
        source_ref = "GRAPH:circular_routing"
        category = EvidenceCategory.CIRCULAR_ROUTING
        cycle_nodes = list(graph_features.contributing_cycle_nodes)
        if not cycle_nodes and graph_features.cycles:
            cycle_nodes = graph_features.cycles[0]
        if primary_acct not in cycle_nodes:
            cycle_nodes.insert(0, primary_acct)

        loop_repr = " -> ".join(cycle_nodes) if cycle_nodes else primary_acct
        title = "Circular Fund Routing Loop"
        description = (
            f"Identified {graph_features.cycle_count} circular fund loop(s) returning money "
            f"through intermediary accounts: {loop_repr}."
        )
        severity = EvidenceSeverity.CRITICAL

        evidence_id = generate_evidence_id(
            source=EvidenceSource.GRAPH,
            source_reference=source_ref,
            category=category,
            account_ids=tuple(cycle_nodes),
            transaction_ids=base_txns,
        )

        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                category=category,
                title=title,
                description=description,
                severity=severity,
                source=EvidenceSource.GRAPH,
                source_reference=source_ref,
                transaction_ids=base_txns,
                account_ids=tuple(cycle_nodes),
                metrics={
                    "cycle_count": graph_features.cycle_count,
                    "cycle_lengths": graph_features.cycle_lengths,
                },
            )
        )

    # B. Shared Device Syndicate
    if graph_features.shared_device_count > 0:
        source_ref = "GRAPH:shared_device"
        category = EvidenceCategory.SHARED_INFRASTRUCTURE
        dev_count = graph_features.shared_device_count
        devices = tuple(graph_features.associated_devices)

        title = f"Shared Device Hardware Syndicate ({dev_count} Device{'s' if dev_count > 1 else ''})"
        description = (
            f"Focal account shares {dev_count} hardware device fingerprint(s) across multiple distinct "
            f"account entities, indicating synthetic identity or mule ring coordination."
        )
        severity = EvidenceSeverity.CRITICAL if dev_count >= 3 else EvidenceSeverity.HIGH

        evidence_id = generate_evidence_id(
            source=EvidenceSource.GRAPH,
            source_reference=source_ref,
            category=category,
            account_ids=(primary_acct,),
            transaction_ids=base_txns,
        )

        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                category=category,
                title=title,
                description=description,
                severity=severity,
                source=EvidenceSource.GRAPH,
                source_reference=source_ref,
                transaction_ids=base_txns,
                account_ids=(primary_acct,),
                device_ids=devices,
                metrics={
                    "shared_device_count": dev_count,
                    "accounts_per_shared_device": dict(graph_features.accounts_per_shared_device),
                },
            )
        )

    # C. Shared IP Syndicate
    if graph_features.shared_ip_count > 0:
        source_ref = "GRAPH:shared_ip"
        category = EvidenceCategory.SHARED_INFRASTRUCTURE
        ip_count = graph_features.shared_ip_count
        ips = tuple(graph_features.associated_ips)

        title = f"Shared Network IP Cluster ({ip_count} IP{'s' if ip_count > 1 else ''})"
        description = (
            f"Focal account co-locates on {ip_count} network IP address(es) with other transacting entities."
        )
        severity = EvidenceSeverity.HIGH if ip_count >= 3 else EvidenceSeverity.MEDIUM

        evidence_id = generate_evidence_id(
            source=EvidenceSource.GRAPH,
            source_reference=source_ref,
            category=category,
            account_ids=(primary_acct,),
            transaction_ids=base_txns,
        )

        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                category=category,
                title=title,
                description=description,
                severity=severity,
                source=EvidenceSource.GRAPH,
                source_reference=source_ref,
                transaction_ids=base_txns,
                account_ids=(primary_acct,),
                ip_addresses=ips,
                metrics={
                    "shared_ip_count": ip_count,
                    "accounts_per_shared_ip": dict(graph_features.accounts_per_shared_ip),
                },
            )
        )

    # D. Extreme Fan-In or Fan-Out Dispersion
    if graph_features.fan_in_ratio >= 3.0 or graph_features.fan_out_ratio >= 3.0:
        source_ref = "GRAPH:fan_ratio"
        category = EvidenceCategory.TOPOLOGICAL_PATTERN
        max_ratio = max(graph_features.fan_in_ratio, graph_features.fan_out_ratio)
        fan_type = "Fan-In Aggregation" if graph_features.fan_in_ratio >= graph_features.fan_out_ratio else "Fan-Out Dispersion"

        title = f"Topological Anomaly: {fan_type} (Ratio: {max_ratio:.1f})"
        description = (
            f"Account demonstrates extreme {fan_type.lower()} ratio of {max_ratio:.2f} "
            f"({graph_features.unique_senders_count} senders -> {graph_features.unique_receivers_count} receivers)."
        )
        severity = EvidenceSeverity.HIGH if max_ratio >= 5.0 else EvidenceSeverity.MEDIUM

        evidence_id = generate_evidence_id(
            source=EvidenceSource.GRAPH,
            source_reference=source_ref,
            category=category,
            account_ids=(primary_acct,),
            transaction_ids=base_txns,
        )

        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                category=category,
                title=title,
                description=description,
                severity=severity,
                source=EvidenceSource.GRAPH,
                source_reference=source_ref,
                transaction_ids=base_txns,
                account_ids=(primary_acct,),
                metrics={
                    "fan_in_ratio": round(graph_features.fan_in_ratio, 4),
                    "fan_out_ratio": round(graph_features.fan_out_ratio, 4),
                    "unique_senders": graph_features.unique_senders_count,
                    "unique_receivers": graph_features.unique_receivers_count,
                },
            )
        )

    # E. Multi-Hop Downstream Layering Path
    if graph_features.max_downstream_path_length >= 3:
        source_ref = "GRAPH:downstream_layering"
        category = EvidenceCategory.TOPOLOGICAL_PATTERN
        hops = graph_features.max_downstream_path_length
        downstream = tuple(graph_features.downstream_accounts)

        title = f"Multi-Hop Layering Chain ({hops} Hops)"
        description = (
            f"Fund trail traces through an extended layering path of {hops} hops across "
            f"{len(downstream)} downstream beneficiary accounts."
        )
        severity = EvidenceSeverity.HIGH

        evidence_id = generate_evidence_id(
            source=EvidenceSource.GRAPH,
            source_reference=source_ref,
            category=category,
            account_ids=(primary_acct, *downstream[:3]),
            transaction_ids=base_txns,
        )

        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                category=category,
                title=title,
                description=description,
                severity=severity,
                source=EvidenceSource.GRAPH,
                source_reference=source_ref,
                transaction_ids=base_txns,
                account_ids=(primary_acct, *downstream[:5]),
                metrics={
                    "max_downstream_hops": hops,
                    "downstream_accounts_count": len(downstream),
                    "path_summary": graph_features.path_summary,
                },
            )
        )

    return items


# ── 4. Machine Learning Evidence Collector (M8 & M9) ────────────────────────


def collect_ml_evidence(
    tabular_prediction: Optional[ModelPrediction],
    graph_ml_prediction: Optional[ModelPrediction],
    event: Optional[TransactionEvent] = None,
) -> list[EvidenceItem]:
    """Extract deterministic model-derived risk indicators from M8 and M9 predictions.

    Maintains factual, non-speculative language ('Model-derived risk indicator', not 'Confirmed fraud').
    Ignores unavailable or un-trained models rather than fabricating low-risk evidence.
    """
    items: list[EvidenceItem] = []
    base_txns: tuple[str, ...] = (event.transaction_id,) if event and event.transaction_id else ()
    base_accts: tuple[str, ...] = (
        tuple(filter(None, [event.sender_account, event.receiver_account]))
        if event
        else ()
    )

    # A. Tabular ML (M8)
    if tabular_prediction is not None:
        det = tabular_prediction.details or {}
        is_avail = (
            det.get("status") != "model_unavailable"
            and "_fallback" not in str(tabular_prediction.model_version)
            and det.get("model_artifact_loaded") is not False
        )
        # Only surface active risk indicators (fraud_probability >= 0.5 or risk_score >= 50)
        if is_avail and (tabular_prediction.fraud_probability >= 0.50 or tabular_prediction.risk_score >= 50):
            source_ref = f"TABULAR_ML:{tabular_prediction.model_version}"
            category = EvidenceCategory.MODEL_PREDICTION
            p = tabular_prediction.fraud_probability
            score = tabular_prediction.risk_score

            title = f"Tabular ML Fraud Indicator (Prob: {p:.1%})"
            description = (
                f"Supervised gradient-boosted tabular model ({tabular_prediction.model_version}) produced a "
                f"fraud probability of {p:.2%} (risk score {score}/100) based on 57-dimensional feature schema."
            )
            severity = (
                EvidenceSeverity.CRITICAL
                if p >= 0.85
                else EvidenceSeverity.HIGH
                if p >= 0.65
                else EvidenceSeverity.MEDIUM
            )

            evidence_id = generate_evidence_id(
                source=EvidenceSource.TABULAR_ML,
                source_reference=source_ref,
                category=category,
                account_ids=base_accts,
                transaction_ids=base_txns,
            )

            items.append(
                EvidenceItem(
                    evidence_id=evidence_id,
                    category=category,
                    title=title,
                    description=description,
                    severity=severity,
                    source=EvidenceSource.TABULAR_ML,
                    source_reference=source_ref,
                    transaction_ids=base_txns,
                    account_ids=base_accts,
                    metrics={
                        "risk_score": score,
                        "fraud_probability": round(p, 4),
                        "model_version": tabular_prediction.model_version,
                        "is_fraud": tabular_prediction.is_fraud,
                    },
                )
            )

    # B. Graph ML / GraphSAGE (M9)
    if graph_ml_prediction is not None:
        det = graph_ml_prediction.details or {}
        is_avail = (
            det.get("status") != "model_unavailable"
            and "_fallback" not in str(graph_ml_prediction.model_version)
            and det.get("model_artifact_loaded") is not False
        )
        if is_avail and (graph_ml_prediction.fraud_probability >= 0.50 or graph_ml_prediction.risk_score >= 50):
            source_ref = f"GRAPH_ML:{graph_ml_prediction.model_version}"
            category = EvidenceCategory.MODEL_PREDICTION
            p = graph_ml_prediction.fraud_probability
            score = graph_ml_prediction.risk_score

            title = f"Graph Neural Network (GraphSAGE) Risk Indicator (Prob: {p:.1%})"
            description = (
                f"Inductive GraphSAGE GNN model ({graph_ml_prediction.model_version}) produced a "
                f"mule probability of {p:.2%} (risk score {score}/100) via multi-hop neighborhood representation."
            )
            severity = (
                EvidenceSeverity.CRITICAL
                if p >= 0.85
                else EvidenceSeverity.HIGH
                if p >= 0.65
                else EvidenceSeverity.MEDIUM
            )

            evidence_id = generate_evidence_id(
                source=EvidenceSource.GRAPH_ML,
                source_reference=source_ref,
                category=category,
                account_ids=base_accts,
                transaction_ids=base_txns,
            )

            items.append(
                EvidenceItem(
                    evidence_id=evidence_id,
                    category=category,
                    title=title,
                    description=description,
                    severity=severity,
                    source=EvidenceSource.GRAPH_ML,
                    source_reference=source_ref,
                    transaction_ids=base_txns,
                    account_ids=base_accts,
                    metrics={
                        "risk_score": score,
                        "fraud_probability": round(p, 4),
                        "model_version": graph_ml_prediction.model_version,
                        "is_fraud": graph_ml_prediction.is_fraud,
                    },
                )
            )

    return items


# ── 5. Risk Fusion Evidence Collector (M10) ─────────────────────────────────


def collect_fusion_evidence(
    fusion_result: Optional[FusionResult],
    event: Optional[TransactionEvent] = None,
) -> list[EvidenceItem]:
    """Extract deterministic explainability evidence from M10 FusionResult.

    Consumes composite risk score, tier, and modality mathematical contributions.
    NEVER recalculates or modifies the composite risk score!
    """
    if fusion_result is None:
        return []

    items: list[EvidenceItem] = []
    base_txns: tuple[str, ...] = (event.transaction_id,) if event and event.transaction_id else ()
    base_accts: tuple[str, ...] = (
        tuple(filter(None, [event.sender_account, event.receiver_account]))
        if event
        else ()
    )

    # A. Composite Risk Assessment Summary Item
    source_ref = f"RISK_FUSION:{fusion_result.fusion_version}"
    category = EvidenceCategory.RISK_FUSION_ASSESSMENT
    score = fusion_result.composite_risk_score
    tier = (
        fusion_result.risk_level.value
        if isinstance(fusion_result.risk_level, RiskLevel)
        else str(fusion_result.risk_level)
    )

    # Map M10 RiskLevel directly to EvidenceSeverity
    sev_map = {
        "CRITICAL": EvidenceSeverity.CRITICAL,
        "HIGH": EvidenceSeverity.HIGH,
        "MEDIUM": EvidenceSeverity.MEDIUM,
        "LOW": EvidenceSeverity.LOW,
    }
    severity = sev_map.get(tier, EvidenceSeverity.LOW)

    title = f"Risk Fusion Composite Score: {score:.1f}/100 ({tier})"
    description = (
        f"Multi-modal Risk Fusion engine synthesized detection signals across "
        f"{len(fusion_result.available_modalities)} active modalities "
        f"({', '.join(fusion_result.available_modalities)}) under policy "
        f"'{fusion_result.missing_signal_policy.value}'. Composite risk score: {score:.2f}/100."
    )

    evidence_id = generate_evidence_id(
        source=EvidenceSource.RISK_FUSION,
        source_reference=source_ref,
        category=category,
        account_ids=base_accts,
        transaction_ids=base_txns,
    )

    items.append(
        EvidenceItem(
            evidence_id=evidence_id,
            category=category,
            title=title,
            description=description,
            severity=severity,
            source=EvidenceSource.RISK_FUSION,
            source_reference=source_ref,
            transaction_ids=base_txns,
            account_ids=base_accts,
            metrics={
                "composite_risk_score": round(score, 4),
                "normalized_risk": round(fusion_result.normalized_risk, 4),
                "risk_level": tier,
                "missing_signal_policy": fusion_result.missing_signal_policy.value,
                "available_modalities": fusion_result.available_modalities,
                "unavailable_modalities": fusion_result.unavailable_modalities,
            },
        )
    )

    # B. Dominant Modality Contribution Breakdown
    for mod_name, contrib in fusion_result.contributions.items():
        # Highlight significant contributors (>= 15 points to composite score)
        if contrib.is_available and (contrib.weighted_score * 100.0) >= 15.0:
            contrib_pts = contrib.weighted_score * 100.0
            c_source_ref = f"RISK_FUSION:contribution_{mod_name}"
            c_sev = (
                EvidenceSeverity.CRITICAL
                if contrib_pts >= 30.0
                else EvidenceSeverity.HIGH
                if contrib_pts >= 20.0
                else EvidenceSeverity.MEDIUM
            )
            c_title = f"Significant Modality Contribution: {mod_name.upper()} (+{contrib_pts:.1f} pts)"
            c_desc = contrib.explanation

            c_evidence_id = generate_evidence_id(
                source=EvidenceSource.RISK_FUSION,
                source_reference=c_source_ref,
                category=category,
                account_ids=base_accts,
                transaction_ids=base_txns,
            )

            items.append(
                EvidenceItem(
                    evidence_id=c_evidence_id,
                    category=category,
                    title=c_title,
                    description=c_desc,
                    severity=c_sev,
                    source=EvidenceSource.RISK_FUSION,
                    source_reference=c_source_ref,
                    transaction_ids=base_txns,
                    account_ids=base_accts,
                    metrics={
                        "modality": mod_name,
                        "normalized_value": round(contrib.normalized_value, 4),
                        "effective_weight": round(contrib.effective_weight, 4),
                        "contribution_points": round(contrib_pts, 2),
                    },
                )
            )

    return items


# ── 6. Transaction Context Evidence Collector (M1) ──────────────────────────


def collect_transaction_evidence(
    event: Optional[TransactionEvent],
) -> list[EvidenceItem]:
    """Extract factual context evidence from the canonical TransactionEvent (M1)."""
    if event is None:
        return []

    items: list[EvidenceItem] = []
    base_txns: tuple[str, ...] = (event.transaction_id,)
    base_accts: tuple[str, ...] = tuple(
        filter(None, [event.sender_account, event.receiver_account])
    )

    # Large transaction amount anomaly
    if event.amount >= 200_000.0:
        source_ref = "TRANSACTION:large_amount"
        category = EvidenceCategory.TRANSACTION_CONTEXT
        sev = (
            EvidenceSeverity.HIGH
            if event.amount >= 500_000.0
            else EvidenceSeverity.MEDIUM
        )
        title = f"Large High-Value Transfer (₹{event.amount:,.2f})"
        desc = (
            f"Transaction amount of ₹{event.amount:,.2f} {event.currency} executed via "
            f"{event.channel} channel from {event.sender_account} to {event.receiver_account}."
        )

        evidence_id = generate_evidence_id(
            source=EvidenceSource.TRANSACTION,
            source_reference=source_ref,
            category=category,
            account_ids=base_accts,
            transaction_ids=base_txns,
        )

        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                category=category,
                title=title,
                description=desc,
                severity=sev,
                source=EvidenceSource.TRANSACTION,
                source_reference=source_ref,
                transaction_ids=base_txns,
                account_ids=base_accts,
                device_ids=((event.device_id,) if event.device_id else ()),
                ip_addresses=((event.ip_address,) if event.ip_address else ()),
                timestamps=((event.timestamp.isoformat(),) if event.timestamp else ()),
                metrics={
                    "amount": event.amount,
                    "currency": event.currency,
                    "channel": event.channel,
                },
            )
        )

    return items
