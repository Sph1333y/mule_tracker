"""
MuleTrace AI — Modality Signal Normalizers.

Converts heterogeneous raw outputs from M5, M6, M7, M8, and M9 into standardized,
deterministic continuous signals strictly bounded in [0.0, 1.0].

Architectural Boundary:
- Every normalization formula is deterministic, documented, and bounded in [0.0, 1.0].
- Explicitly distinguishes genuine low-risk evaluations (available, 0.0) from absent
  or un-trained modalities (unavailable/missing).
- Read-only: never alters the incoming signal structures or their internal states.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.domain.interfaces import ModelPrediction
from app.engines.graph.intelligence.graph_models import GraphFeatures
from app.engines.risk_fusion.models import NormalizedSignal, SignalModality
from app.engines.rules.base import EvaluationResult, RuleMatchResult
from app.engines.temporal.temporal_models import TemporalFeatures

logger = logging.getLogger("app.engines.risk_fusion.normalizers")


class SignalNormalizer:
    """Provides deterministic transformation routines mapping each modality into [0.0, 1.0]."""

    @staticmethod
    def normalize_rules(
        rule_signals: Optional[EvaluationResult | list[RuleMatchResult] | dict[str, Any]],
    ) -> NormalizedSignal:
        """Normalize M5 rule engine evaluation outputs into [0.0, 1.0].

        Formula:
            base_score = min(1.0, total_risk_score_delta / 100.0)
            Severity Floor:
                CRITICAL -> max(base_score, 0.85)
                HIGH     -> max(base_score, 0.65)
                MEDIUM   -> max(base_score, 0.40)
                LOW      -> base_score
        """
        if rule_signals is None:
            return NormalizedSignal(
                modality=SignalModality.RULES,
                value=0.0,
                is_available=False,
                status="missing",
                raw_summary="No rule signals provided",
            )

        total_delta = 0
        highest_severity = "LOW"
        matched_rules: list[str] = []

        if isinstance(rule_signals, EvaluationResult):
            total_delta = rule_signals.total_risk_score_delta
            highest_severity = rule_signals.highest_severity
            matched_rules = [m.rule_code for m in rule_signals.matches if m.matched]
        elif isinstance(rule_signals, list):
            for item in rule_signals:
                if isinstance(item, RuleMatchResult) and item.matched:
                    total_delta += item.score_contribution
                    matched_rules.append(item.rule_code)
                    if item.severity == "CRITICAL":
                        highest_severity = "CRITICAL"
                    elif item.severity == "HIGH" and highest_severity != "CRITICAL":
                        highest_severity = "HIGH"
                    elif item.severity == "MEDIUM" and highest_severity not in ("HIGH", "CRITICAL"):
                        highest_severity = "MEDIUM"
        elif isinstance(rule_signals, dict):
            total_delta = int(rule_signals.get("total_risk_score_delta") or rule_signals.get("score") or 0)
            highest_severity = str(rule_signals.get("highest_severity", "LOW")).upper()
            matched_rules = list(rule_signals.get("flagged_patterns") or rule_signals.get("matches") or [])

        # Compute normalized value
        base_norm = min(1.0, max(0.0, total_delta / 100.0))

        # Severity floor calibration
        severity_floors = {
            "CRITICAL": 0.85,
            "HIGH": 0.65,
            "MEDIUM": 0.40,
            "LOW": 0.0,
        }
        floor = severity_floors.get(highest_severity, 0.0)
        final_value = min(1.0, max(base_norm, floor))

        return NormalizedSignal(
            modality=SignalModality.RULES,
            value=round(final_value, 4),
            is_available=True,
            status="available",
            raw_summary=f"delta={total_delta}, severity={highest_severity}, rules={len(matched_rules)}",
            contributing_factors={
                "total_score_delta": total_delta,
                "highest_severity": highest_severity,
                "matched_rule_count": len(matched_rules),
                "matched_rules": matched_rules,
            },
        )

    @staticmethod
    def normalize_temporal(
        temporal_features: Optional[TemporalFeatures],
    ) -> NormalizedSignal:
        """Normalize M6 temporal intelligence features into [0.0, 1.0].

        Formula:
            S_burst         = 1.0 if burst_detected else 0.0           (weight: 0.35)
            S_rapid         = min(1.0, rapid_in_out_ratio)             (weight: 0.35)
            S_velocity      = min(1.0, transaction_count_1h / 10.0)    (weight: 0.15)
            S_concentration = min(1.0, temporal_concentration)         (weight: 0.15)
            value = 0.35 * S_burst + 0.35 * S_rapid + 0.15 * S_velocity + 0.15 * S_concentration
        """
        if temporal_features is None:
            return NormalizedSignal(
                modality=SignalModality.TEMPORAL,
                value=0.0,
                is_available=False,
                status="missing",
                raw_summary="No temporal features provided",
            )

        s_burst = 1.0 if temporal_features.burst_detected else 0.0
        s_rapid = (
            min(1.0, max(0.0, float(temporal_features.rapid_in_out_ratio)))
            if temporal_features.rapid_in_out_detected
            else 0.0
        )
        s_velocity = min(1.0, max(0.0, float(temporal_features.transaction_count_1h) / 10.0))
        s_concentration = min(1.0, max(0.0, float(temporal_features.temporal_concentration)))

        norm_value = (
            0.35 * s_burst
            + 0.35 * s_rapid
            + 0.15 * s_velocity
            + 0.15 * s_concentration
        )
        final_value = min(1.0, max(0.0, norm_value))

        return NormalizedSignal(
            modality=SignalModality.TEMPORAL,
            value=round(final_value, 4),
            is_available=True,
            status="available",
            raw_summary=f"burst={temporal_features.burst_detected}, rapid={temporal_features.rapid_in_out_detected}, tx_1h={temporal_features.transaction_count_1h}",
            contributing_factors={
                "burst_detected": temporal_features.burst_detected,
                "rapid_in_out_detected": temporal_features.rapid_in_out_detected,
                "rapid_in_out_ratio": round(temporal_features.rapid_in_out_ratio, 4),
                "transaction_count_1h": temporal_features.transaction_count_1h,
                "temporal_concentration": round(temporal_features.temporal_concentration, 4),
            },
        )

    @staticmethod
    def normalize_graph(
        graph_features: Optional[GraphFeatures],
    ) -> NormalizedSignal:
        """Normalize M7 graph topological features into [0.0, 1.0].

        Formula:
            S_cycle   = 1.0 if has_cycle else 0.0                                          (weight: 0.35)
            S_shared  = min(1.0, (shared_device_count * 0.6 + shared_ip_count * 0.4) / 3.0) (weight: 0.35)
            S_fan     = min(1.0, max(fan_in_ratio, fan_out_ratio))                         (weight: 0.15)
            S_density = min(1.0, neighborhood_density)                                     (weight: 0.15)
            value = 0.35 * S_cycle + 0.35 * S_shared + 0.15 * S_fan + 0.15 * S_density
        """
        if graph_features is None:
            return NormalizedSignal(
                modality=SignalModality.GRAPH,
                value=0.0,
                is_available=False,
                status="missing",
                raw_summary="No graph features provided",
            )

        s_cycle = 1.0 if graph_features.has_cycle else 0.0
        shared_score = (float(graph_features.shared_device_count) * 0.6 + float(graph_features.shared_ip_count) * 0.4) / 3.0
        s_shared = min(1.0, max(0.0, shared_score))
        s_fan = min(1.0, max(0.0, max(float(graph_features.fan_in_ratio), float(graph_features.fan_out_ratio))))
        s_density = min(1.0, max(0.0, float(graph_features.neighborhood_density)))

        norm_value = (
            0.35 * s_cycle
            + 0.35 * s_shared
            + 0.15 * s_fan
            + 0.15 * s_density
        )
        final_value = min(1.0, max(0.0, norm_value))

        return NormalizedSignal(
            modality=SignalModality.GRAPH,
            value=round(final_value, 4),
            is_available=True,
            status="available",
            raw_summary=f"cycle={graph_features.has_cycle}, shared_dev={graph_features.shared_device_count}, shared_ip={graph_features.shared_ip_count}",
            contributing_factors={
                "has_cycle": graph_features.has_cycle,
                "cycle_count": graph_features.cycle_count,
                "shared_device_count": graph_features.shared_device_count,
                "shared_ip_count": graph_features.shared_ip_count,
                "fan_in_ratio": round(graph_features.fan_in_ratio, 4),
                "fan_out_ratio": round(graph_features.fan_out_ratio, 4),
                "neighborhood_density": round(graph_features.neighborhood_density, 4),
            },
        )

    @staticmethod
    def normalize_tabular_ml(
        prediction: Optional[ModelPrediction],
    ) -> NormalizedSignal:
        """Normalize M8 tabular machine learning prediction into [0.0, 1.0].

        Explicitly identifies whether model inference is active vs fallback/unavailable.
        """
        if prediction is None:
            return NormalizedSignal(
                modality=SignalModality.TABULAR_ML,
                value=0.0,
                is_available=False,
                status="missing",
                raw_summary="No tabular ML prediction provided",
            )

        details = prediction.details or {}
        is_unavailable = (
            details.get("status") in ("model_unavailable", "unavailable")
            or details.get("model_artifact_loaded") is False
            or "_fallback" in prediction.model_version
        )

        if is_unavailable:
            return NormalizedSignal(
                modality=SignalModality.TABULAR_ML,
                value=0.0,
                is_available=False,
                status="model_unavailable",
                raw_summary=f"Tabular ML model un-trained or offline ({prediction.model_version})",
                contributing_factors={"model_version": prediction.model_version, "details": details},
            )

        raw_prob = float(prediction.fraud_probability)
        prob = min(1.0, max(0.0, raw_prob))

        return NormalizedSignal(
            modality=SignalModality.TABULAR_ML,
            value=round(prob, 4),
            is_available=True,
            status="available",
            raw_summary=f"proba={prob:.4f}, score={prediction.risk_score}, version={prediction.model_version}",
            contributing_factors={
                "fraud_probability": round(prob, 4),
                "risk_score": prediction.risk_score,
                "is_fraud": prediction.is_fraud,
                "model_version": prediction.model_version,
            },
        )

    @staticmethod
    def normalize_graph_ml(
        prediction: Optional[ModelPrediction],
    ) -> NormalizedSignal:
        """Normalize M9 GraphSAGE Graph ML prediction into [0.0, 1.0].

        Explicitly identifies whether GraphSAGE model inference is active vs fallback/unavailable.
        """
        if prediction is None:
            return NormalizedSignal(
                modality=SignalModality.GRAPH_ML,
                value=0.0,
                is_available=False,
                status="missing",
                raw_summary="No Graph ML prediction provided",
            )

        details = prediction.details or {}
        is_unavailable = (
            details.get("status") in ("model_unavailable", "unavailable")
            or details.get("model_artifact_loaded") is False
            or "_fallback" in prediction.model_version
        )

        if is_unavailable:
            return NormalizedSignal(
                modality=SignalModality.GRAPH_ML,
                value=0.0,
                is_available=False,
                status="model_unavailable",
                raw_summary=f"GraphSAGE model un-trained or offline ({prediction.model_version})",
                contributing_factors={"model_version": prediction.model_version, "details": details},
            )

        raw_prob = float(prediction.fraud_probability)
        prob = min(1.0, max(0.0, raw_prob))

        return NormalizedSignal(
            modality=SignalModality.GRAPH_ML,
            value=round(prob, 4),
            is_available=True,
            status="available",
            raw_summary=f"proba={prob:.4f}, score={prediction.risk_score}, version={prediction.model_version}",
            contributing_factors={
                "fraud_probability": round(prob, 4),
                "risk_score": prediction.risk_score,
                "is_fraud": prediction.is_fraud,
                "model_version": prediction.model_version,
            },
        )


# Singleton normalizer instance
signal_normalizer = SignalNormalizer()
